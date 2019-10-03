# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import collections
import functools
import itertools
import logging

from dashboard.common import math_utils
from dashboard.pinpoint.models import change as change_module
from dashboard.pinpoint.models import compare
from dashboard.pinpoint.models import evaluators
from dashboard.pinpoint.models import exploration
from dashboard.pinpoint.models import task as task_module
from dashboard.pinpoint.models.tasks import find_isolate
from dashboard.pinpoint.models.tasks import read_value
from dashboard.pinpoint.models.tasks import run_test
from dashboard.services import gitiles_service

_DEFAULT_SPECULATION_LEVELS = 2

AnalysisOptions = collections.namedtuple('AnalysisOptions', (
    'comparison_magnitude',
    'min_attempts',
    'max_attempts',
))

BuildOptionTemplate = collections.namedtuple('BuildOptionTemplate',
                                             ('builder', 'target', 'bucket'))

TestOptionTemplate = collections.namedtuple(
    'TestOptionTemplate', ('swarming_server', 'dimensions', 'extra_args'))

ReadOptionTemplate = collections.namedtuple(
    'ReadOptionTemplate',
    ('benchmark', 'histogram_options', 'graph_json_options', 'mode'))

TaskOptions = collections.namedtuple(
    'TaskOptions',
    ('build_option_template', 'test_option_template', 'read_option_template',
     'analysis_options', 'start_change', 'end_change', 'pinned_change'))


def _CreateReadTaskOptions(build_option_template, test_option_template,
                           read_option_template, analysis_options, change):
  return read_value.TaskOptions(
      test_options=run_test.TaskOptions(
          build_options=find_isolate.TaskOptions(
              builder=build_option_template.builder,
              target=build_option_template.target,
              bucket=build_option_template.bucket,
              change=change),
          swarming_server=test_option_template.swarming_server,
          dimensions=test_option_template.dimensions,
          extra_args=test_option_template.extra_args,
          attempts=analysis_options.min_attempts),
      benchmark=read_option_template.benchmark,
      histogram_options=read_option_template.histogram_options,
      graph_json_options=read_option_template.graph_json_options,
      mode=read_option_template.mode)


def CreateGraph(options):
  if not isinstance(options, TaskOptions):
    raise ValueError(
        'options must be an instance of performance_bisection.TaskOptions')

  start_change = options.start_change
  end_change = options.end_change
  if options.pinned_change:
    start_change.Update(options.pinned_change)
    end_change.Update(options.pinned_change)

  start_change_read_options = _CreateReadTaskOptions(
      options.build_option_template, options.test_option_template,
      options.read_option_template, options.analysis_options, start_change)
  end_change_read_options = _CreateReadTaskOptions(
      options.build_option_template, options.test_option_template,
      options.read_option_template, options.analysis_options, end_change)

  # Given the start_change and end_change, we create two subgraphs that we
  # depend on from the 'find_culprit' task. This means we'll need to create
  # independent test options and build options from the template provided by the
  # caller.
  start_subgraph = read_value.CreateGraph(start_change_read_options)
  end_subgraph = read_value.CreateGraph(end_change_read_options)

  # Then we add a dependency from the 'FindCulprit' task with the payload
  # describing the options set for the performance bisection.
  find_culprit_task = task_module.TaskVertex(
      id='performance_bisection',
      vertex_type='find_culprit',
      payload={
          'start_change':
              options.start_change.AsDict(),
          'end_change':
              options.end_change.AsDict(),
          'pinned_change':
              options.pinned_change.AsDict() if options.pinned_change else None,
          # We still persist the templates, because we'll need that data in case
          # we are going to extend the graph with the same build/test templates
          # in subgraphs.
          'analysis_options':
              options.analysis_options._asdict(),
          'build_option_template':
              options.build_option_template._asdict(),
          'test_option_template':
              options.test_option_template._asdict(),
          'read_option_template': {
              'histogram_options':
                  options.read_option_template.histogram_options._asdict(),
              'graph_json_options':
                  options.read_option_template.graph_json_options._asdict(),
              'benchmark':
                  options.read_option_template.benchmark,
              'mode':
                  options.read_option_template.mode,
          },
      })
  return task_module.TaskGraph(
      vertices=itertools.chain(start_subgraph.vertices, end_subgraph.vertices,
                               [find_culprit_task]),
      edges=itertools.chain(start_subgraph.edges, end_subgraph.edges, [
          task_module.Dependency(from_=find_culprit_task.id, to=v.id)
          for v in itertools.chain(start_subgraph.vertices,
                                   end_subgraph.vertices)
          if v.vertex_type == 'read_value'
      ]))


class PrepareCommits(collections.namedtuple('PrepareCLs', ('job', 'task'))):
  __slots__ = ()

  @task_module.LogStateTransitionFailures
  def __call__(self, _):
    start_change = change_module.Change.FromDict(
        self.task.payload['start_change'])
    end_change = change_module.Change.FromDict(self.task.payload['end_change'])
    try:
      # We're storing this once, so that we don't need to always get this when
      # working with the individual commits. This reduces our reliance on
      # datastore operations throughout the course of handling the culprit
      # finding process.
      # TODO(dberris): Handle the cases of auto-roll CLs?
      commits = change_module.Commit.CommitRange(start_change.base_commit,
                                                 end_change.base_commit)
      self.task.payload.update({
          'commits': [start_change.base_commit.AsDict()] + [
              change_module.Commit.FromDict({
                  'repository': start_change.base_commit.repository,
                  'git_hash': commit['commit']
              }).AsDict() for commit in reversed(commits)
          ]
      })
      logging.debug('Commits = %s', self.task.payload['commits'])
      task_module.UpdateTask(
          self.job,
          self.task.id,
          new_state='ongoing',
          payload=self.task.payload)
    except gitiles_service.NotFoundError as e:
      # TODO(dberris): We need to be more resilient to intermittent failures
      # from the Gitiles service here.
      self.task.payload.update({
          'errors':
              self.task.payload.get('errors', []) + [{
                  'reason': 'GitilesFetchError',
                  'message': e.message
              }]
      })
      task_module.UpdateTask(
          self.job, self.task.id, new_state='failed', payload=self.task.payload)

  def __str__(self):
    return 'PrepareCLs( job = %s, task = %s )' % (self.job.job_id, self.task.id)


class RefineExplorationAction(
    collections.namedtuple('RefineExplorationAction',
                           ('job', 'task', 'change', 'additional_attempts'))):
  __slots__ = ()

  def __call__(self, accumulator):
    # Outline:
    #   - Given the job and task, extend the TaskGraph to add new tasks and
    #     dependencies, being careful to filter the IDs from what we already see
    #     in the accumulator to avoid graph amendment errors.
    #   - If we do encounter graph amendment errors, we should log those and not
    #     block progress because that can only happen if there's concurrent
    #     updates being performed with the same actions.
    build_option_template = BuildOptionTemplate(
        **self.task.payload.get('build_option_template'))
    test_option_template = TestOptionTemplate(
        **self.task.payload.get('test_option_template'))
    analysis_options = AnalysisOptions(
        **self.task.payload.get('analysis_options'))

    # The ReadOptionTemplate is special because it has nested structures, so
    # we'll have to reconstitute those accordingly.
    read_option_template_map = self.task.payload.get('read_option_template')
    read_option_template = ReadOptionTemplate(
        benchmark=self.task.payload.get('read_option_template').get(
            'benchmark'),
        histogram_options=read_value.HistogramOptions(
            **read_option_template_map.get('histogram_options')),
        graph_json_options=read_value.GraphJsonOptions(
            **read_option_template_map.get('graph_json_options')),
        mode=read_option_template_map.get('mode'))
    logging.debug('Read Option Template: %s', read_option_template)

    if self.additional_attempts:
      analysis_options.min_attempts = min(
          analysis_options.min_attempts + self.additional_attempts,
          analysis_options.max_attempts)

    new_subgraph = read_value.CreateGraph(
        _CreateReadTaskOptions(build_option_template, test_option_template,
                               read_option_template, analysis_options,
                               self.change))
    try:
      task_module.ExtendTaskGraph(
          self.job,
          vertices=[
              # Add all of the new vertices we do not have in the graph yet.
              v for v in new_subgraph.vertices if v.id not in accumulator
          ],
          dependencies=[
              # Only add dependencies to the new 'read_value' tasks.
              task_module.Dependency(from_=self.task.id, to=v.id)
              for v in new_subgraph.vertices
              if v.id not in accumulator and v.vertex_type == 'read_value'
          ])
    except task_module.InvalidAmendment as e:
      logging.error('Failed to amend graph: %s', e)


class CompleteExplorationAction(
    collections.namedtuple('CompleteExplorationAction', ('job', 'task'))):
  __slots__ = ()

  @task_module.LogStateTransitionFailures
  def __call__(self, accumulator):
    # TODO(dberris): Maybe consider cancelling outstanding actions? Here we'll
    # need a way of synthesising actions if we want to force the continuation of
    # a task graph's evaluation.
    task_module.UpdateTask(
        self.job,
        self.task.id,
        new_state='completed',
        payload=self.task.payload)


class PassFilter(object):

  def __init__(self, lower_bound, upper_bound):
    self.lower_bound = lower_bound
    self.upper_bound = upper_bound
    self.lower_bound_found = False
    self.upper_bound_found = False

  def __call__(self, v):
    if not self.lower_bound_found:
      if self.lower_bound == v:
        self.lower_bound_found = True
        return True
      return False

    if not self.upper_bound_found:
      if self.upper_bound == v:
        self.upper_bound_found = True
        return True
      assert self.lower_bound_found
      return True

    assert self.lower_bound_found and self.upper_bound_found
    return False


def Mean(values):
  values = [v for v in values if isinstance(v, (int, float))]
  if len(values) == 0:
    return float('nan')
  return float(sum(values)) / len(values)


class FindCulprit(collections.namedtuple('FindCulprit', ('job'))):
  __slots__ = ()

  def __call__(self, task, event, accumulator):
    # Outline:
    #  - If the task is still pending, this means this is the first time we're
    #  encountering the task in an evaluation. Set up the payload data to
    #  include the full range of commits, so that we load it once and have it
    #  ready, and emit an action to mark the task ongoing.
    #
    #  - If the task is ongoing, gather all the dependency data (both results
    #  and status) and see whether we have enough data to determine the next
    #  action. We have three main cases:
    #
    #    1. We cannot detect a significant difference between the results from
    #       two different CLs. We call this the NoReproduction case.
    #
    #    2. We do not have enough confidence that there's a difference. We call
    #       this the Indeterminate case.
    #
    #    3. We have enough confidence that there's a difference between any two
    #       ordered changes. We call this the SignificantChange case.
    #
    # - Delegate the implementation to handle the independent cases for each
    #   change point we find in the CL continuum.
    if task.status == 'pending':
      return [PrepareCommits(self.job, task)]

    if task.status == 'ongoing':
      # TODO(dberris): Validate and fail gracefully instead of asserting?
      assert 'commits' in task.payload, ('Programming error, need commits to '
                                         'proceed!')

      # Collect all the dependency task data and analyse the results.
      # Group them by change.
      # Order them by appearance in the CL range.
      # Also count the status per CL (failed, ongoing, etc.)
      deps = set(dep for dep in task.dependencies)
      results_by_change = {}
      status_by_change = {}
      changes_with_data = set()
      for change, status, result_values in [
          (change_module.Change.FromDict(t.get('change')), t.get('status'),
           t.get('result_values'))
          for dep, t in accumulator.items()
          if dep in deps
      ]:
        results_by_change.setdefault(change, [])
        results_by_change[change].append(result_values)
        status_by_change.setdefault(change, {})
        status_by_change[change].update({
            status: status_by_change.get(change).get(status, 0) + 1,
        })
        if status not in {'ongoing', 'pending'}:
          changes_with_data.add(change)

      # We want to reduce the list of ordered changes to only the ones that have
      # data available.
      all_changes = [
          change_module.Change(
              commits=[change_module.Commit.FromDict(commit)],
              patch=task.payload.get('pinned_change'))
          for commit in task.payload.get('commits', [])
      ]
      ordered_changes = [
          change for change in all_changes if change in changes_with_data
      ]

      logging.debug('Ordered Changes = %s', ordered_changes)
      if len(ordered_changes) < 2:
        # We do not have enough data yet to determine whether we should do
        # anything.
        return None

      # From here we can then do the analysis on a pairwise basis, as we're
      # going through the list of Change instances we have data for.
      # NOTE: A lot of this algorithm is already in pinpoint/models/job_state.py
      # which we're adapting.
      def Compare(a, b):
        # This is the comparison function which determines whether the samples
        # we have from the two changes (a and b) are statistically significant.
        if 'pending' in status_by_change[a] or 'pending' in status_by_change[b]:
          return compare.PENDING

        # NOTE: Here we're attempting to scale the provided comparison magnitude
        # threshold by using the central tendencies (means) of the resulting
        # values from individual test attempt results, and scaling those by the
        # larger inter-quartile range (a measure of dispersion, simply computed
        # as the 75th percentile minus the 25th percentile). The reason we're
        # doing this is so that we can scale the tolerance according to the
        # noise inherent in the measurements -- i.e. more noisy measurements
        # will require a larger difference for us to consider statistically
        # significant.
        #
        # TODO(dberris): Rethink this computation to consider the consolidated
        # measurements for a single change, instead of looking at the means,
        # since we cannot assume that the means can be relied on as a good
        # measure of central tendency for small sample sizes.
        means_for_a = tuple(Mean(results) for results in results_by_change[a])
        means_for_b = tuple(Mean(results) for results in results_by_change[b])
        max_iqr = max(math_utils.Iqr(means_for_a), math_utils.Iqr(means_for_b))

        # TODO(dberris): Re-think the default magnitude in the cases where the
        # measurements are very stable.
        comparison_magnitude = task.payload.get(
            'comparison_magnitude', 1.0) / max_iqr if max_iqr > 0 else 1000.0

        # TODO(dberris): Here, again, rethink using the means if we have the
        # individual samples in the attempts.
        attempts = (sum(status_by_change[a].values()) +
                    sum(status_by_change[b].values())) // 2
        return compare.Compare(means_for_a, means_for_b, attempts,
                               'performance', comparison_magnitude)

      def DetectChange(change_a, change_b):
        # We return None if the comparison determins that the result is
        # inconclusive. This is required by the exploration.Speculate contract.
        comparison = Compare(change_a, change_b)
        if comparison == compare.UNKNOWN:
          return None
        return comparison == compare.DIFFERENT

      changes_to_refine = []

      def CollectChangesToRefine(a, b):
        # Here we're collecting changes that need refinement, which happens when
        # two changes when compared yield the "unknown" result.
        attempts_for_a = sum(status_by_change[a].values())
        attempts_for_b = sum(status_by_change[b].values())
        if min(attempts_for_a, attempts_for_b) == task.payload.get(
            'analysis_options').get('max_attempts'):
          return None
        changes_to_refine.append((a if attempts_for_a <= attempts_for_b else b,
                                  max(attempts_for_a, attempts_for_b) -
                                  min(attempts_for_a, attempts_for_b)))
        return None

      def FindMidpoint(a, b):
        # Here we use the (very simple) midpoint finding algorithm given that we
        # already have the full range of commits to bisect through.
        pass_filter = PassFilter(a, b)
        subrange = [c for c in all_changes if pass_filter(c)]
        logging.debug('Subrange: %s', subrange)
        return None if len(subrange) <= 2 else subrange[len(subrange) // 2]

      additional_changes = exploration.Speculate(
          ordered_changes,
          change_detected=DetectChange,
          on_unknown=CollectChangesToRefine,
          midpoint=FindMidpoint,
          levels=_DEFAULT_SPECULATION_LEVELS)

      # At this point we can collect the actions to extend the task graph based
      # on the results of the speculation.
      actions = [
          RefineExplorationAction(self.job, task, change, more_attempts)
          for change, more_attempts in itertools.chain(
              [(c, 0) for _, c in additional_changes],
              [(c, a) for c, a in changes_to_refine],
          )
      ]

      # Here we collect the points where we've found the changes.
      differences = []

      def CollectDifferences(a, b):
        if not a:
          return b
        if DetectChange(a, b):
          differences.append((a, b))
        return b

      functools.reduce(CollectDifferences, ordered_changes, None)

      task.payload.update({'culprits': differences})
      if not actions:
        # Mark this operation complete, storing the differences we can compute.
        actions = [CompleteExplorationAction(self.job, task)]
      return actions


class Evaluator(evaluators.FilteringEvaluator):

  def __init__(self, job):
    super(Evaluator, self).__init__(
        predicate=evaluators.All(
            evaluators.TaskTypeEq('find_culprit'),
            evaluators.Not(evaluators.TaskStatusIn({'completed', 'failed'}))),
        delegate=FindCulprit(job))
