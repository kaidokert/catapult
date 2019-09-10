# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import collections
import json
import logging
import urlparse

from dashboard.pinpoint.models import change as change_module
from dashboard.pinpoint.models import errors
from dashboard.pinpoint.models import isolate
from dashboard.pinpoint.models import task as task_module
from dashboard.pinpoint.models import evaluators
from dashboard.pinpoint.models import event as event_module
from dashboard.pinpoint.models.change import commit as commit_module
from dashboard.pinpoint.models.quest import execution
from dashboard.pinpoint.models.quest import quest
from dashboard.services import buildbucket_service
from dashboard.services import gerrit_service


BUCKET = 'master.tryserver.chromium.perf'


class FindIsolate(quest.Quest):

  def __init__(self, builder, target, bucket):
    self._builder_name = builder
    self._target = target
    self._bucket = bucket

    self._previous_builds = {}
    self._build_tags = collections.OrderedDict()

  def __eq__(self, other):
    return (isinstance(other, type(self)) and
            self._bucket == other._bucket and
            self._builder_name == other._builder_name)

  def __str__(self):
    return 'Build'

  @property
  def build_tags(self):
    if hasattr(self, '_build_tags'):
      return self._build_tags
    return collections.OrderedDict()

  def __setstate__(self, state):
    self.__dict__ = state  # pylint: disable=attribute-defined-outside-init
    # TODO(dberris): Remove this when we migrate all the instances.
    if not hasattr(self, '_build_tags'):
      self._build_tags = collections.OrderedDict()

  def Start(self, change):
    return _FindIsolateExecution(self._builder_name, self._target, self._bucket,
                                 change, self._previous_builds, self.build_tags)

  def PropagateJob(self, job):
    self._build_tags = _BuildTagsFromJob(job)
  @classmethod
  def FromDict(cls, arguments):
    for arg in ('builder', 'target', 'bucket'):
      if arg not in arguments:
        raise TypeError('Missing "{0}" argument'.format(arg))

    return cls(arguments['builder'], arguments['target'], arguments['bucket'])


class _FindIsolateExecution(execution.Execution):

  def __init__(self, builder_name, target, bucket, change, previous_builds,
               build_tags):
    super(_FindIsolateExecution, self).__init__()
    self._builder_name = builder_name
    self._target = target
    self._bucket = bucket
    self._change = change
    # previous_builds is shared among all Executions of the same Quest.
    self._previous_builds = previous_builds

    self._build = None
    self._build_url = None

    # an ordered dict of tags.
    self._build_tags = build_tags

  def _AsDict(self):
    details = []
    details.append({
        'key': 'builder',
        'value': self._builder_name,
    })
    if self._build:
      details.append({
          'key': 'build',
          'value': self._build,
          'url': self._build_url if hasattr(self, '_build_url') else None,
      })
    if self._result_arguments:
      details.append({
          'key': 'isolate',
          'value': self._result_arguments['isolate_hash'],
          'url': self._result_arguments['isolate_server'] + '/browse?digest=' +
                 self._result_arguments['isolate_hash'],
      })
    return details

  def _Poll(self):
    logging.debug('_FindIsolateExecution Polling: %s', self._AsDict())

    if self._CheckIsolateCache():
      return

    if self._build:
      self._CheckBuildStatus()
      return

    self._RequestBuild()

  def _CheckIsolateCache(self):
    """Checks the isolate cache to see if a build is already available.

    Returns:
      True iff the isolate was found, meaning the execution is completed.
    """
    try:
      isolate_server, isolate_hash = isolate.Get(
          self._builder_name, self._change, self._target)
    except KeyError:
      logging.debug('NOT found in isolate cache')
      return False

    result_arguments = {
        'isolate_server': isolate_server,
        'isolate_hash': isolate_hash,
    }
    logging.debug('Found in isolate cache: %s', result_arguments)
    self._Complete(result_arguments=result_arguments)
    return True

  def _CheckBuildStatus(self):
    """Checks on the status of a previously requested build.

    Raises:
      BuildError: The build failed, was canceled, or didn't produce an isolate.
    """
    build = buildbucket_service.GetJobStatus(self._build)['build']
    logging.debug('buildbucket response: %s', build)

    self._build_url = build.get('url')

    if build['status'] != 'COMPLETED':
      return
    if build['result'] == 'FAILURE':
      raise errors.BuildFailed(build['failure_reason'])
    if build['result'] == 'CANCELED':
      raise errors.BuildCancelled(build['cancelation_reason'])

    # The build succeeded. Parse the result and complete this Quest.
    properties = json.loads(build['result_details_json'])['properties']

    commit_position = properties['got_revision_cp'].replace('@', '(at)')
    suffix = 'with_patch' if 'patch_storage' in properties else 'without_patch'
    key = '_'.join(('swarm_hashes', commit_position, suffix))

    if self._target not in properties[key]:
      raise errors.BuildIsolateNotFound()

    result_arguments = {
        'isolate_server': properties['isolate_server'],
        'isolate_hash': properties[key][self._target],
    }
    self._Complete(result_arguments=result_arguments)

  @property
  def bucket(self):
    if hasattr(self, '_bucket'):
      return self._bucket
    return BUCKET

  @property
  def build_tags(self):
    if hasattr(self, '_build_tags'):
      return self._build_tags
    return collections.OrderedDict()

  def __setstate__(self, state):
    self.__dict__ = state  # pylint: disable=attribute-defined-outside-init
    # TODO(dberris): Remove this when we migrate all the instances.
    if not hasattr(self, '_build_tags'):
      self._build_tags = collections.OrderedDict()

  def _RequestBuild(self):
    """Requests a build.

    If a previous Execution already requested a build for this Change, returns
    that build instead of requesting a new one.
    """
    logging.debug('_FindIsolateExecution _RequestBuild')

    if self._change in self._previous_builds:
      logging.debug('%s in list of previous_builds', self._change)
      # If another Execution already requested a build, reuse that one.
      self._build = self._previous_builds[self._change]
    else:
      logging.debug('Requesting a build')
      # Request a build!
      buildbucket_info = _RequestBuild(self._builder_name, self._change,
                                       self.bucket, self.build_tags)
      self._build = buildbucket_info['build']['id']
      self._previous_builds[self._change] = self._build


def _RequestBuild(builder_name, change, bucket, build_tags, task=None):
  base_as_dict = change.base_commit.AsDict()
  review_url = base_as_dict.get('review_url')
  if not review_url:
    raise errors.BuildGerritUrlNotFound(str(change.base_commit))

  url_parts = urlparse.urlparse(review_url)
  base_review_url = urlparse.urlunsplit(
      (url_parts.scheme, url_parts.netloc, '', '', ''))

  patch = change_module.GerritPatch.FromUrl(review_url)

  change_info = gerrit_service.GetChange(base_review_url, patch.change)

  commit_url_parts = urlparse.urlparse(base_as_dict['url'])

  # Note: The ordering here for buildbucket v1 api is important.
  # crbug.com/937392
  builder_tags = []
  if change.patch:
    builder_tags.append(change.patch.BuildsetTags())
  builder_tags.append('buildset:commit/gitiles/%s/%s/+/%s' %
                      (commit_url_parts.netloc, change_info['project'],
                       change.base_commit.git_hash))
  builder_tags.extend(['%s:%s' % (k, v) for k, v in build_tags.items()])

  deps_overrides = {dep.repository_url: dep.git_hash for dep in change.deps}
  parameters = {
      'builder_name': builder_name,
      'properties': {
          'clobber': True,
          'revision': change.base_commit.git_hash,
          'deps_revision_overrides': deps_overrides,
      },
  }

  if change.patch:
    parameters['properties'].update(change.patch.BuildParameters())

  logging.debug('bucket: %s', bucket)
  logging.debug('builder_tags: %s', builder_tags)
  logging.debug('parameters: %s', parameters)

  pubsub_callback = None
  if build_tags:
    # This means we have access to Pinpoint job details, we should provide this
    # information to the attempts to build.
    pubsub_callback = {
        # TODO(dberris): Consolidate constants in environment vars?
        'topic':
            'projects/chromeperf/topics/pinpoint-swarming-updates',
        'auth_token':
            'UNUSED',
        'user_data':
            json.dumps({
                'job_id': build_tags.get('pinpoint_job_id'),
                'task': {
                    'type':
                        'build',
                    'id':
                        build_tags.get('pinpoint_task_id')
                        if not task else task.id,
                }
            })
    }
    logging.debug('pubsub_callback: %s', pubsub_callback)

  # TODO: Look up Buildbucket bucket from builder_name.
  return buildbucket_service.Put(bucket, builder_tags, parameters,
                                 pubsub_callback)


def _BuildTagsFromJob(job):
  return collections.OrderedDict([
      ('pinpoint_job_id', job.job_id),
      ('pinpoint_user', job.user),
      ('pinpoint_url', job.url),
  ])


# Everything beyond this point aims to define an evaluator for 'find_isolate'
# tasks.
FAILURE_MAPPING = {'FAILURE': 'failed', 'CANCELLED': 'cancelled'}


class ScheduleBuildAction(object):

  def __init__(self, job, task, change):
    self.job = job
    self.task = task
    self.change = change

  def __call__(self, accumulator):
    # This will actually schedule a build, and set it up to ensure we're able to
    # receive an update as PubSub messages via Buildbucket. We can re-use the
    # code in the Quest that does this.
    # TODO(dberris): Maybe use a value in the accumulator to check whether we
    # should bail?
    self.task.payload.update({'tries': self.task.payload.get('tries', 0) + 1})
    try:
      task_module.UpdateTask(
          self.job,
          self.task.id,
          new_state='ongoing',
          payload=self.task.payload)
      result = _RequestBuild(
          self.task.payload.get('builder'), self.change,
          self.task.payload.get('bucket'), _BuildTagsFromJob(self.job),
          self.task)
      self.task.payload.update({'buildbucket_result': result})
      task_module.UpdateTask(self.job, self.task.id, payload=self.task.payload)
    except task_module.InvalidTransition as e:
      logging.debug(
          'Attempting state transition failed; task = %s , error = %s',
          self.task, e)
      # TODO(dberris): Poll the ongoing build, if we have the data in payload.

  def __str__(self):
    return 'Build Action <job = %s, task = %s>' % (self.job.job_id, self.task)


class UpdateBuildStatusAction(object):

  def __init__(self, job, task, change):
    self.job = job
    self.task = task
    self.change = change

  def __call__(self, accumulator):
    # The task contains the buildbucket_result which we need to update by
    # polling the status of the id.
    build_details = self.task.payload.get('buildbucket_result')
    if not build_details:
      logging.error(
          'No build details in attempt to update build status; task = %s',
          self.task)
      task_module.UpdateTask(self.job, self.task.id, new_state='failed')
      return None

    # Use the build ID and poll.
    build = buildbucket_service.GetJobStatus(build_details).get('build', {})
    logging.debug('buildbucket response: %s', build)

    # Update the buildbucket result.
    self.task.payload.update({
        'buildbucket_job_status': build,
    })

    # Decide whether the build was successful or not.
    if build.get('status') != 'COMPLETED':
      logging.error('Unexpected status: %s', build.get('status'))
      task_module.UpdateTask(
          self.job, self.task.id, new_state='failed', payload=self.task.payload)
      return None

    result = build.get('result')
    if not result:
      logging.debug('Missing result field in response, bailing.')
      task_module.UpdateTask(
          self.job, self.task.id, new_state='failed', payload=self.task.payload)
      return None

    if result in FAILURE_MAPPING:
      try:
        task_module.UpdateTask(
            self.job,
            self.task.id,
            new_state=FAILURE_MAPPING[result],
            payload=self.task.payload)
      except task_module.InvalidTransition as e:
        logging.error('Failed state transition for task; task = %s, error = %s',
                      self.task, e)
      return

    try:
      # Parse the result and mark this task completed.
      properties = json.loads(build['result_details_json'])['properties']
      commit_position = properties['got_revision_cp'].replace('@', '(at)')
      suffix = '%s_patch' % ('with'
                             if 'patch_storage' in properties else 'without',)
      key = '_'.join(('swarm_hashes', commit_position, suffix))

      if self.task.payload.get('target') not in properties.get(key, {}):
        # TODO(dberris): Update the job state with an exception, or set of
        # failures.
        self.task.payload.update({
            'failure': {
                'reason':
                    'BuildIsolateNotFound',
                'message':
                    'Could not find isolate for build at %s' % (self.change,)
            }
        })
        task_module.UpdateTask(
            self.job,
            self.task.id,
            new_state='failed',
            payload=self.task.payload)
      else:
        self.task.payload.update({
            'isolate_server': properties['isolate_server'],
            'isolate_hash': properties[key][self.task.payload.get('target')]
        })
        task_module.UpdateTask(
            self.job,
            self.task.id,
            new_state='completed',
            payload=self.task.payload)
    except task_module.InvalidTransition as e:
      logging.error('Failed marking task "completed"; task = %s, error = %s',
                    self.task, e)
      return

  def __str__(self):
    return 'Update Build Action <job = %s, task = %s>' % (self.job.job_id,
                                                          self.task)


class HandleInitiate(object):

  def __init__(self, job):
    self.job = job

  def __call__(self, task, *_):
    if task.status == 'ongoing':
      logging.warning(
          'Ignoring an initiate event on an ongoing task; task = %s', task)
      return None

    # Outline:
    #   - Check if we can find the isolate for this revision.
    #     - If found, update the payload of the task and update accumulator with
    #       result for this task.
    #     - If not found, schedule a build for this revision, update the task
    #       payload with the build details, wait for updates.
    try:
      change = change_module.Change(
          commits=[
              commit_module.Commit(c['repository'], c['git_hash'])
              for c in task.payload.get('change', {}).get('commits', [])
          ],
          patch=task.payload.get('patch'))
      logging.debug('Looking up isolate for change = %s', change)
      isolate_server, isolate_hash = isolate.Get(
          task.payload.get('builder'), change, task.payload.get('target'))
      task.payload.update({
          'isolate_server': isolate_server,
          'isolate_hash': isolate_hash,
      })
      return [
          lambda _: task_module.UpdateTask(
              self.job, task.id, new_state='completed', payload=task.payload)
      ]
    except KeyError as e:
      logging.error('Failed to find isolate for task = %s;\nError: %s', task, e)
      return [ScheduleBuildAction(self.job, task, change)]
    return None


class HandleUpdate(object):

  def __init__(self, job):
    self.job = job

  def __call__(self, task, event, _):
    # Outline:
    #   - Check build status payload.
    #     - If successful, update the task payload with status and relevant
    #       information, propagate information into the accumulator.
    #     - If unsuccessful:
    #       - Retry if the failure is a retryable error (update payload with
    #         retry information)
    #       - Fail if failure is non-retryable or we've exceeded retries.
    if event.payload.get('status') == 'build_completed':
      change = change_module.Change(
          commits=[
              commit_module.Commit(c['repository'], c['git_hash'])
              for c in task.payload.get('change', {}).get('commits', [])
          ],
          patch=task.payload.get('patch'))
      return [UpdateBuildStatusAction(self.job, task, change)]
    return None


class Evaluator(evaluators.DispatchEvaluator):

  @classmethod
  def Filter(cls, task, event, _):
    if task.task_type != 'find_isolate':
      return False

    if not isinstance(event, event_module.Event):
      return False

    if event.target_task and event.target_task != task.id:
      return False

    if task.status in {'completed', 'failed', 'cancelled'}:
      logging.info('Ignoring event "%s" on a terminal task; task = %s', event,
                   task)
      return False

    return True

  def __init__(self, job):
    super(Evaluator, self).__init__(
        evaluator_map={
            'initiate':
                evaluators.SequenceEvaluator(
                    evaluators=(evaluators.PayloadLiftingEvaluator(),
                                evaluators.FilteringEvaluator(
                                    predicate=Evaluator.Filter,
                                    delegate=HandleInitiate(job)))),
            'update':
                evaluators.SequenceEvaluator(
                    evaluators=(evaluators.PayloadLiftingEvaluator(),
                                evaluators.FilteringEvaluator(
                                    predicate=Evaluator.Filter,
                                    delegate=HandleUpdate(job))))
        },
        default_evaluator=evaluators.PayloadLiftingEvaluator)
