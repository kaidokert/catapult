# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import collections
import itertools

from dashboard.pinpoint.models.tasks import read_value
from dashboard.pinpoint.models.tasks import run_test
from dashboard.pinpoint.models.tasks import find_isolate
from dashboard.pinpoint.models import task as task_module

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


def CreateGraph(options):
  if not isinstance(options, TaskOptions):
    raise ValueError(
        'options must be an instance of performance_bisection.TaskOptions')

  start_change = options.start_change
  end_change = options.end_change
  if options.pinned_change:
    start_change.Update(options.pinned_change)
    end_change.Update(options.pinned_change)

  def CreateTaskOptions(change):
    return read_value.TaskOptions(
        test_options=run_test.TaskOptions(
            build_options=find_isolate.TaskOptions(
                builder=options.build_option_template.builder,
                target=options.build_option_template.target,
                bucket=options.build_option_template.bucket,
                change=change),
            swarming_server=options.test_option_template.swarming_server,
            dimensions=options.test_option_template.dimensions,
            extra_args=options.test_option_template.extra_args,
            attempts=options.analysis_options.min_attempts),
        benchmark=options.read_option_template.benchmark,
        histogram_options=options.read_option_template.histogram_options,
        graph_json_options=options.read_option_template.graph_json_options,
        mode=options.read_option_template.mode)

  start_change_read_options = CreateTaskOptions(start_change)
  end_change_read_options = CreateTaskOptions(end_change)

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
          'analysis_options': {
              'comparison_magnitude':
                  options.analysis_options.comparison_magnitude,
              'min_attempts':
                  options.analysis_options.min_attempts,
              'max_attempts':
                  options.analysis_options.max_attempts,
          }
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
