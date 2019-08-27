# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import collections
import logging
import mock
import functools

from dashboard.pinpoint.models import task as task_module
from dashboard.pinpoint.models import job as job_module
from dashboard.pinpoint import test

FakeEvent = collections.namedtuple('Event', ('type', 'status', 'payload'))


def TaskStatusGetter(task_status, task, event, _):
  if event.type == 'test':
    task_status[task.id] = task.status
  return None


def TaskStatusAndPayloadGetter(task_status, task, event, _):
  if event.type == 'test':
    task_status[task.id] = {
        'status': task.status,
        'payload': task.payload if task.payload else {}
    }
  return None


def UpdateTask(job, task_id, new_state, _):
  logging.debug('Updating task "%s" to "%s"', task_id, new_state)
  task_module.UpdateTask(job, task_id, new_state=new_state)


def UpdateTaskWithPayload(job, task_id, new_state, payload, _):
  logging.debug('Updating task "%s" to "%s" ; payload = %s', task_id, new_state,
                payload)
  task_module.UpdateTask(job, task_id, new_state=new_state, payload=payload)


def ExtendTaskGraph(job, vertices, dependencies, _):
  logging.debug('Extending task graph with vertices += %s ; dependencies = %s',
                vertices, dependencies)
  task_module.ExtendTaskGraph(job, vertices, dependencies)


def BuildEvaluator(job, task, event, accumulator):
  logging.debug('Evaluating <%s> with event <%s>; accumulator = %r', task,
                event, accumulator)
  accumulator.update({task.id: {'status': task.status}})
  if task.status in {'completed', 'failed'}:
    return None

  if task.task_type == 'build':
    if event.type == 'initiate':
      if task.status == 'pending':
        return [functools.partial(UpdateTask, job, task.id, 'ongoing')]
      else:
        return None
    if event.type == 'update':
      if event.payload.get('task_id') != task.id:
        return None
      if event.status == 'build_completed':
        return [functools.partial(UpdateTask, job, task.id, 'completed')]
      if event.status == 'build_failed':
        return [functools.partial(UpdateTask, job, task.id, 'failed')]
      if event.status == 'reset':
        return [functools.partial(UpdateTask, job, task.id, 'pending')]
      raise ValueError('Unsupported update.')

  dep_status = [
      accumulator.get(dep, {}).get('status') for dep in task.dependencies
  ]

  if dep_status and any(status == 'failed' for status in dep_status):
    return [functools.partial(UpdateTask, job, task.id, 'failed')]
  if dep_status and all(status == 'completed'
                        for status in dep_status) and task.status == 'pending':
    return [functools.partial(UpdateTask, job, task.id, 'ongoing')]
  return None


class TaskTest(test.TestCase):

  def setUp(self):
    super(TaskTest, self).setUp()
    self.maxDiff = None  # pylint: disable=invalid-name

  def testPopulateEvaluateSimpleNoop(self):
    job = job_module.Job.New((), ())
    task_graph = task_module.TaskGraph(
        vertices=[
            task_module.TaskVertex(
                id='build_0', vertex_type='build', payload={}),
            task_module.TaskVertex(
                id='build_1', vertex_type='build', payload={}),
            task_module.TaskVertex(id='test_0', vertex_type='test', payload={}),
            task_module.TaskVertex(id='test_1', vertex_type='test', payload={}),
            task_module.TaskVertex(
                id='find_culprit', vertex_type='process', payload={}),
            task_module.TaskVertex(
                id='generate_results', vertex_type='process', payload={}),
            task_module.TaskVertex(
                id='export_stats', vertex_type='process', payload={})
        ],
        edges=[
            task_module.Dependency(from_='export_stats', to='find_culprit'),
            task_module.Dependency(from_='generate_results', to='find_culprit'),
            task_module.Dependency(from_='find_culprit', to='test_0'),
            task_module.Dependency(from_='find_culprit', to='test_1'),
            task_module.Dependency(from_='test_0', to='build_0'),
            task_module.Dependency(from_='test_1', to='build_1'),
        ])
    task_module.PopulateTaskGraph(job, task_graph)
    calls = {}

    def Evaluator(task, event, accumulator):
      logging.debug('Evaluate(%s, %s, %s) called.', task.id, event, accumulator)
      calls[task.id] = calls.get(task.id, 0) + 1
      return None

    task_module.Evaluate(job, 'test', Evaluator)
    self.assertDictEqual(
        {
            'build_0': 1,
            'build_1': 1,
            'test_0': 1,
            'test_1': 1,
            'find_culprit': 1,
            'generate_results': 1,
            'export_stats': 1,
        }, calls)

  def testPopulateEmptyGraph(self):
    job = job_module.Job.New((), ())
    task_graph = task_module.TaskGraph(vertices=[], edges=[])
    task_module.PopulateTaskGraph(job, task_graph)
    evaluator = mock.MagicMock()
    evaluator.assert_not_called()
    task_module.Evaluate(job, 'test', evaluator)

  def testPopulateCycles(self):
    job = job_module.Job.New((), ())
    task_graph = task_module.TaskGraph(
        vertices=[
            task_module.TaskVertex(
                id='node_0', vertex_type='process', payload={}),
            task_module.TaskVertex(
                id='node_1', vertex_type='process', payload={})
        ],
        edges=[
            task_module.Dependency(from_='node_0', to='node_1'),
            task_module.Dependency(from_='node_1', to='node_0')
        ])
    task_module.PopulateTaskGraph(job, task_graph)
    calls = {}

    def Evaluator(task, event, accumulator):
      logging.debug('Evaluate(%s, %s, %s) called.', task.id, event, accumulator)
      calls[task.id] = calls.get(task.id, 0) + 1
      return None

    task_module.Evaluate(job, 'test', Evaluator)
    self.assertDictEqual({'node_0': 1, 'node_1': 1}, calls)

  def testPopulateIslands(self):
    self.skipTest('Not implemented yet')

  def testEvaluateSimpleAB(self):
    job = job_module.Job.New((), ())
    task_graph = task_module.TaskGraph(
        vertices=[
            task_module.TaskVertex(
                id='build_0', vertex_type='build', payload={}),
            task_module.TaskVertex(
                id='build_1', vertex_type='build', payload={}),
            task_module.TaskVertex(id='test_0', vertex_type='test', payload={}),
            task_module.TaskVertex(id='test_1', vertex_type='test', payload={}),
            task_module.TaskVertex(
                id='find_culprit', vertex_type='process', payload={}),
            task_module.TaskVertex(
                id='generate_results', vertex_type='process', payload={}),
            task_module.TaskVertex(
                id='export_stats', vertex_type='process', payload={})
        ],
        edges=[
            task_module.Dependency(from_='export_stats', to='find_culprit'),
            task_module.Dependency(from_='generate_results', to='find_culprit'),
            task_module.Dependency(from_='find_culprit', to='test_0'),
            task_module.Dependency(from_='find_culprit', to='test_1'),
            task_module.Dependency(from_='test_0', to='build_0'),
            task_module.Dependency(from_='test_1', to='build_1'),
        ])
    task_module.PopulateTaskGraph(job, task_graph)

    # The first event we send should be an 'initiate' event, and we should see
    # that we've found the build events and updated those.
    task_module.Evaluate(
        job,
        FakeEvent(
            type='initiate', status='new', payload={'task_id': 'build_0'}),
        functools.partial(BuildEvaluator, job))
    task_module.Evaluate(
        job,
        FakeEvent(
            type='initiate', status='new', payload={'task_id': 'build_1'}),
        functools.partial(BuildEvaluator, job))

    task_status = {}
    task_module.Evaluate(job, FakeEvent(type='test', status='new', payload={}),
                         functools.partial(TaskStatusGetter, task_status))
    self.assertDictEqual(
        {
            'build_0': 'ongoing',
            'build_1': 'ongoing',
            'test_0': 'pending',
            'test_1': 'pending',
            'find_culprit': 'pending',
            'generate_results': 'pending',
            'export_stats': 'pending',
        }, task_status)

  def testEvaluateABWithCancellation(self):
    job = job_module.Job.New((), ())
    task_graph = task_module.TaskGraph(
        vertices=[
            task_module.TaskVertex(
                id='build_0', vertex_type='build', payload={}),
            task_module.TaskVertex(
                id='build_1', vertex_type='build', payload={}),
            task_module.TaskVertex(id='test_0', vertex_type='test', payload={}),
            task_module.TaskVertex(id='test_1', vertex_type='test', payload={}),
            task_module.TaskVertex(
                id='find_culprit', vertex_type='process', payload={}),
            task_module.TaskVertex(
                id='generate_results', vertex_type='process', payload={}),
            task_module.TaskVertex(
                id='export_stats', vertex_type='process', payload={})
        ],
        edges=[
            task_module.Dependency(from_='export_stats', to='find_culprit'),
            task_module.Dependency(from_='generate_results', to='find_culprit'),
            task_module.Dependency(from_='find_culprit', to='test_0'),
            task_module.Dependency(from_='find_culprit', to='test_1'),
            task_module.Dependency(from_='test_0', to='build_0'),
            task_module.Dependency(from_='test_1', to='build_1'),
        ])
    task_module.PopulateTaskGraph(job, task_graph)

    # The first event we send should be an 'initiate' event, and we should see
    # that we've found the build events and updated those.
    task_module.Evaluate(
        job,
        FakeEvent(
            type='initiate', status='new', payload={'task_id': 'build_0'}),
        functools.partial(BuildEvaluator, job))

    # Then we test how we can do cancellation of ongoing events.
    def CancellationEvaluator(task, event, _):
      if task.status in {'ongoing', 'pending'}:
        return [
            functools.partial(UpdateTaskWithPayload, job, task.id, 'cancelled',
                              event.payload)
        ]

    task_module.Evaluate(
        job,
        FakeEvent(
            type='update',
            status='terminate',
            payload={'reason': 'Terminal conditions failed.'}),
        CancellationEvaluator)

    task_status = {}
    task_module.Evaluate(
        job, FakeEvent(type='test', status='new', payload={}),
        functools.partial(TaskStatusAndPayloadGetter, task_status))
    self.assertDictEqual(
        {
            'build_0': {
                'status': 'cancelled',
                'payload': {
                    'reason': 'Terminal conditions failed.'
                }
            },
            'build_1': {
                'status': 'cancelled',
                'payload': {
                    'reason': 'Terminal conditions failed.'
                }
            },
            'test_0': {
                'status': 'cancelled',
                'payload': {
                    'reason': 'Terminal conditions failed.'
                }
            },
            'test_1': {
                'status': 'cancelled',
                'payload': {
                    'reason': 'Terminal conditions failed.'
                }
            },
            'find_culprit': {
                'status': 'cancelled',
                'payload': {
                    'reason': 'Terminal conditions failed.'
                }
            },
            'generate_results': {
                'status': 'cancelled',
                'payload': {
                    'reason': 'Terminal conditions failed.'
                }
            },
            'export_stats': {
                'status': 'cancelled',
                'payload': {
                    'reason': 'Terminal conditions failed.'
                }
            }
        }, task_status)

  def testEvaluateFailures(self):
    job = job_module.Job.New((), ())
    task_graph = task_module.TaskGraph(
        vertices=[
            task_module.TaskVertex(
                id='build_0', vertex_type='build', payload={}),
            task_module.TaskVertex(
                id='build_1', vertex_type='build', payload={}),
            task_module.TaskVertex(id='test_0', vertex_type='test', payload={}),
            task_module.TaskVertex(id='test_1', vertex_type='test', payload={}),
            task_module.TaskVertex(
                id='find_culprit', vertex_type='process', payload={}),
            task_module.TaskVertex(
                id='generate_results', vertex_type='process', payload={}),
            task_module.TaskVertex(
                id='export_stats', vertex_type='process', payload={})
        ],
        edges=[
            task_module.Dependency(from_='export_stats', to='find_culprit'),
            task_module.Dependency(from_='generate_results', to='find_culprit'),
            task_module.Dependency(from_='find_culprit', to='test_0'),
            task_module.Dependency(from_='find_culprit', to='test_1'),
            task_module.Dependency(from_='test_0', to='build_0'),
            task_module.Dependency(from_='test_1', to='build_1'),
        ])
    task_module.PopulateTaskGraph(job, task_graph)

    # Then we send a completion event to build_0, which should cause it to be
    # marked 'completed' and send a failure event to build_1.
    task_module.Evaluate(
        job,
        FakeEvent(
            type='update',
            status='build_completed',
            payload={'task_id': 'build_0'}),
        functools.partial(BuildEvaluator, job))
    task_module.Evaluate(
        job,
        FakeEvent(
            type='update',
            status='build_failed',
            payload={'task_id': 'build_1'}),
        functools.partial(BuildEvaluator, job))

    task_status = {}
    task_module.Evaluate(job, FakeEvent(type='test', status='new', payload={}),
                         functools.partial(TaskStatusGetter, task_status))
    self.assertDictEqual(
        {
            'build_0': 'completed',
            'build_1': 'failed',
            'test_0': 'ongoing',
            'test_1': 'failed',
            'find_culprit': 'failed',
            'generate_results': 'failed',
            'export_stats': 'failed',
        }, task_status)

  def testEvaluateBisectionWithGraphExtensions(self):
    # In this test we simulate the case where we have a task spawn other tasks
    # and extend the graph with more vertices and edges.
    job = job_module.Job.New((), ())
    task_graph = task_module.TaskGraph(
        vertices=[
            task_module.TaskVertex(
                id='build_0', vertex_type='build', payload={}),
            task_module.TaskVertex(
                id='build_1', vertex_type='build', payload={}),
            task_module.TaskVertex(id='test_0', vertex_type='test', payload={}),
            task_module.TaskVertex(id='test_1', vertex_type='test', payload={}),
            task_module.TaskVertex(
                id='find_culprit', vertex_type='process', payload={}),
            task_module.TaskVertex(
                id='generate_results', vertex_type='process', payload={}),
            task_module.TaskVertex(
                id='export_stats', vertex_type='process', payload={})
        ],
        edges=[
            task_module.Dependency(from_='export_stats', to='find_culprit'),
            task_module.Dependency(from_='generate_results', to='find_culprit'),
            task_module.Dependency(from_='find_culprit', to='test_0'),
            task_module.Dependency(from_='find_culprit', to='test_1'),
            task_module.Dependency(from_='test_0', to='build_0'),
            task_module.Dependency(from_='test_1', to='build_1'),
        ])
    task_module.PopulateTaskGraph(job, task_graph)

    def SimpleBuildEvaluator(task, event, accumulator):
      logging.debug('Task: %s ; Event: %s ; Accumulator: %s', task, event,
                    accumulator)
      if task.id != event.payload.get('task_id'):
        return None

      if event.type == 'initiate':
        if task.status == 'ongoing':
          return None
        accumulator.update(
            {task.id: {
                'status': 'ongoing',
                'payload': event.payload,
            }})
        return [
            functools.partial(UpdateTaskWithPayload, job, task.id, 'ongoing',
                              event.payload)
        ]

      if event.type == 'update':
        if task.status == 'completed':
          return None
        accumulator.update(
            {task.id: {
                'status': 'completed',
                'payload': event.payload,
            }})
        return [
            functools.partial(UpdateTaskWithPayload, job, task.id, 'completed',
                              event.payload)
        ]
      raise ValueError('Unhandled event type: %s', event)

    def CulpritNotFoundEvaluator(task, event, accumulator):
      if task.id != event.payload.get('task_id'):
        accumulator.update({
            task.id: {
                'status': task.status,
                'payload': event.payload,
            }
        })
        return None

      dep_status = [
          accumulator.get(dep, {}).get('status') for dep in task.dependencies
      ]
      if all(
          s == 'completed' for s in dep_status):
        logging.debug('Simulating a culprit was not found.')
        return [
            functools.partial(ExtendTaskGraph, job, [
                task_module.TaskVertex(
                    id='build_2', vertex_type='build', payload={}),
                task_module.TaskVertex(
                    id='test_2', vertex_type='test', payload={}),
                task_module.TaskVertex(
                    id='build_3', vertex_type='build', payload={}),
                task_module.TaskVertex(
                    id='test_3', vertex_type='test', payload={}),
                task_module.TaskVertex(
                    id='build_4', vertex_type='build', payload={}),
                task_module.TaskVertex(
                    id='test_4', vertex_type='test', payload={}),
            ], [
                task_module.Dependency(from_='test_2', to='build_2'),
                task_module.Dependency(from_='test_3', to='build_3'),
                task_module.Dependency(from_='test_4', to='build_4'),
                task_module.Dependency(from_='find_culprit', to='test_2'),
                task_module.Dependency(from_='find_culprit', to='test_3'),
                task_module.Dependency(from_='find_culprit', to='test_4'),
            ]),
        ]

    events = [
        # The first event we send should be an 'initiate' event, and we should
        # see that we've found the build events and updated those.
        FakeEvent(
            type='initiate', status='new', payload={'task_id': 'build_0'}),
        FakeEvent(
            type='initiate', status='new', payload={'task_id': 'build_1'}),
        FakeEvent(
            type='update',
            status='build_completed',
            payload={'task_id': 'build_0'}),
        FakeEvent(
            type='update',
            status='build_completed',
            payload={'task_id': 'build_1'}),
        FakeEvent(type='initiate', status='new', payload={'task_id': 'test_0'}),
        FakeEvent(type='initiate', status='new', payload={'task_id': 'test_1'}),
        FakeEvent(
            type='update',
            status='test_completed',
            payload={'task_id': 'test_0'}),
        FakeEvent(
            type='update',
            status='test_completed',
            payload={'task_id': 'test_1'}),
        FakeEvent(
            type='initiate',
            status='analyze_results',
            payload={'task_id': 'find_culprit'}),
    ]
    for event in events:
      task_module.Evaluate(job, event, SimpleBuildEvaluator)

    task_module.Evaluate(
        job,
        FakeEvent(
            type='test',
            status='not_important',
            payload={'task_id': 'find_culprit'}), CulpritNotFoundEvaluator)

    task_status = {}
    task_module.Evaluate(
        job, FakeEvent(type='test', status='not_important', payload={}),
        functools.partial(TaskStatusGetter, task_status))
    self.assertDictEqual(
        {
            'build_0': 'completed',
            'test_0': 'completed',
            'build_1': 'completed',
            'test_1': 'completed',
            'build_2': 'pending',
            'test_2': 'pending',
            'build_3': 'pending',
            'test_3': 'pending',
            'build_4': 'pending',
            'test_4': 'pending',
            'find_culprit': 'ongoing',
            'generate_results': 'pending',
            'export_stats': 'pending',
        }, task_status)

  def testEvaluateInvalidActions(self):
    self.skipTest('Not implemented yet')

  def testEvaluateConverges(self):
    self.skipTest('Not implemented yet')
