# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import collections
import json
import mock
import unittest
import logging

from dashboard.pinpoint.models.change import change
from dashboard.pinpoint.models import errors
from dashboard.pinpoint.models.quest import run_test

DIMENSIONS = [
    {
        'key': 'pool',
        'value': 'Chrome-perf-pinpoint'
    },
    {
        'key': 'key',
        'value': 'value'
    },
]
_BASE_ARGUMENTS = {
    'swarming_server': 'server',
    'dimensions': DIMENSIONS,
}

_BASE_SWARMING_TAGS = {}

_BOT_QUERY_0_BOTS = {"success": "false"}

_BOT_QUERY_1_BOT = {"items": [{"bot_id": "a"}]}

_BOT_QUERY_4_BOTS = {
    "items": [{
        "bot_id": "a"
    }, {
        "bot_id": "b"
    }, {
        "bot_id": "c"
    }, {
        "bot_id": "d"
    }]
}

FakeJob = collections.namedtuple('Job',
                                 ['job_id', 'url', 'comparison_mode', 'user'])


@mock.patch('dashboard.services.swarming.Bots.List')
@mock.patch('dashboard.services.crrev_service.GetCommit')
class StartTest(unittest.TestCase):

  def testStart(self, get_commit, swarming_bots_list):
    swarming_bots_list.return_value = _BOT_QUERY_1_BOT
    get_commit.return_value = {'number': 999999}
    quest = run_test.RunTest('server', DIMENSIONS, ['arg'], _BASE_SWARMING_TAGS,
                             None, None)
    quest.PropagateJob(
        FakeJob('cafef00d', 'https://pinpoint/cafef00d', 'try',
                'user@example.com'))
    execution = quest.Start('change', 'https://isolate.server', 'isolate hash')
    self.assertEqual(execution._extra_args, ['arg'])


class FromDictTest(unittest.TestCase):

  def testMinimumArguments(self):
    quest = run_test.RunTest.FromDict(_BASE_ARGUMENTS)
    expected = run_test.RunTest('server', DIMENSIONS, [], _BASE_SWARMING_TAGS,
                                None, None)
    self.assertEqual(quest, expected)

  def testAllArguments(self):
    arguments = dict(_BASE_ARGUMENTS)
    arguments['extra_test_args'] = '["--custom-arg", "custom value"]'
    quest = run_test.RunTest.FromDict(arguments)

    extra_args = ['--custom-arg', 'custom value']
    expected = run_test.RunTest('server', DIMENSIONS, extra_args,
                                _BASE_SWARMING_TAGS, None, None)
    self.assertEqual(quest, expected)

  def testMissingSwarmingServer(self):
    arguments = dict(_BASE_ARGUMENTS)
    del arguments['swarming_server']
    with self.assertRaises(TypeError):
      run_test.RunTest.FromDict(arguments)

  def testMissingDimensions(self):
    arguments = dict(_BASE_ARGUMENTS)
    del arguments['dimensions']
    with self.assertRaises(TypeError):
      run_test.RunTest.FromDict(arguments)

  def testStringDimensions(self):
    arguments = dict(_BASE_ARGUMENTS)
    arguments['dimensions'] = json.dumps(DIMENSIONS)
    quest = run_test.RunTest.FromDict(arguments)
    expected = run_test.RunTest('server', DIMENSIONS, [], _BASE_SWARMING_TAGS,
                                None, None)
    self.assertEqual(quest, expected)

  def testInvalidExtraTestArgs(self):
    arguments = dict(_BASE_ARGUMENTS)
    arguments['extra_test_args'] = '"this is a json-encoded string"'
    with self.assertRaises(TypeError):
      run_test.RunTest.FromDict(arguments)

  def testStringExtraTestArgs(self):
    arguments = dict(_BASE_ARGUMENTS)
    arguments['extra_test_args'] = '--custom-arg "custom value"'
    quest = run_test.RunTest.FromDict(arguments)

    extra_args = ['--custom-arg', 'custom value']
    expected = run_test.RunTest('server', DIMENSIONS, extra_args,
                                _BASE_SWARMING_TAGS, None, None)
    self.assertEqual(quest, expected)

_NEW_TASK_BODY_BASE = {
        'realm':
            'chrome:pinpoint',
        'name':
            'Pinpoint job',
        'user':
            'Pinpoint',
        'tags':
            mock.ANY,
        'priority':
            '100',
        'pubsub_topic':
            'projects/chromeperf/topics/pinpoint-swarming-updates',
        'pubsub_auth_token':
            'UNUSED',
        'pubsub_userdata':
            mock.ANY,
        'service_account':
            mock.ANY,
        'task_slices': [{
            'expiration_secs': '86400',
            'properties': {
                'inputs_ref': {
                    'isolatedserver': 'isolate server',
                    'isolated': 'input isolate hash',
                },
                'extra_args': ['arg'],
                'dimensions': DIMENSIONS,
                'execution_timeout_secs': mock.ANY,
                'io_timeout_secs': mock.ANY,
            }
        },],
    }

class _RunTestExecutionTest(unittest.TestCase):

  def assertNewTaskHasDimensionsMulti(self, swarming_tasks_new, patches):
      tasks = []
      for p in patches:
          task = _NEW_TASK_BODY_BASE
          task.update(p)
          tasks.append(mock.call(task))
      print(str(tasks))
      swarming_tasks_new.assert_has_calls(tasks)
  def assertNewTaskHasDimensions(self, swarming_tasks_new, patch=None):
    body = _NEW_TASK_BODY_BASE
    if patch:
      body.update(patch)
    swarming_tasks_new.assert_called_with(body)


@mock.patch('dashboard.services.swarming.Bots.List')
@mock.patch('dashboard.services.swarming.Tasks.New')
@mock.patch('dashboard.services.swarming.Task.Result')
@mock.patch('dashboard.services.crrev_service.GetCommit')
class RunTestFullTest(_RunTestExecutionTest):

  def testSuccess(self, get_commit, swarming_task_result, swarming_tasks_new,
                  swarming_bots_list):
    swarming_bots_list.return_value = _BOT_QUERY_1_BOT
    get_commit.return_value = {'number': 675460}
    # Goes through a full run of two Executions.

    # Call RunTest.Start() to create an Execution.
    quest = run_test.RunTest('server', DIMENSIONS, ['arg'], _BASE_SWARMING_TAGS,
                             None, None)

    # Propagate a thing that looks like a job.
    quest.PropagateJob(
        FakeJob('cafef00d', 'https://pinpoint/cafef00d', 'try',
                'user@example.com'))

    execution = quest.Start(
        change.Change("a", variant=0), 'isolate server', 'input isolate hash')
    quest.Start(
        change.Change("a", variant=1), 'isolate server', 'input isolate hash')

    swarming_task_result.assert_not_called()
    swarming_tasks_new.assert_not_called()

    # Call the first Poll() to start the swarming task.
    swarming_tasks_new.return_value = {'task_id': 'task id'}
    execution.Poll()

    swarming_task_result.assert_not_called()
    self.assertEqual(swarming_tasks_new.call_count, 2)
    self.assertNewTaskHasDimensions(
        swarming_tasks_new, {
            'task_slices': [{
                'expiration_secs': '86400',
                'properties': {
                    'inputs_ref': {
                        'isolatedserver': 'isolate server',
                        'isolated': 'input isolate hash'
                    },
                    'extra_args': ['arg'],
                    'dimensions': DIMENSIONS + [{
                        "key": "id",
                        "value": "a"
                    }],
                    'execution_timeout_secs': mock.ANY,
                    'io_timeout_secs': mock.ANY,
                }
            }]
        })
    self.assertFalse(execution.completed)
    self.assertFalse(execution.failed)

    # Call subsequent Poll()s to check the task status.
    swarming_task_result.return_value = {'state': 'PENDING'}
    execution.Poll()

    self.assertFalse(execution.completed)
    self.assertFalse(execution.failed)

    swarming_task_result.return_value = {
        'bot_id': 'a',
        'exit_code': 0,
        'failure': False,
        'outputs_ref': {
            'isolatedserver': 'output isolate server',
            'isolated': 'output isolate hash',
        },
        'state': 'COMPLETED',
    }
    execution.Poll()

    self.assertTrue(execution.completed)
    self.assertFalse(execution.failed)
    self.assertEqual(execution.result_values, ())
    self.assertEqual(
        execution.result_arguments, {
            'isolate_server': 'output isolate server',
            'isolate_hash': 'output isolate hash',
        })
    self.assertEqual(
        execution.AsDict(), {
            'completed':
                True,
            'exception':
                None,
            'details': [
                {
                    'key': 'bot',
                    'value': 'a',
                    'url': 'server/bot?id=a',
                },
                {
                    'key': 'task',
                    'value': 'task id',
                    'url': 'server/task?id=task id',
                },
                {
                    'key': 'isolate',
                    'value': 'output isolate hash',
                    'url': 'output isolate server/browse?'
                           'digest=output isolate hash',
                },
            ],
        })

  def testGetABOrderings(self, get_commit, swarming_task_result,
                                     swarming_tasks_new, swarming_bots_list):
    pass

  @mock.patch('dashboard.pinpoint.models.quest.run_test.RunTest._GetABOrderings'
             )
  @mock.patch('random.choice')
  def testBotAllocationAndScheduling(self, random_choice, get_ab_orderings,
                                     get_commit, swarming_task_result,
                                     swarming_tasks_new, swarming_bots_list):
    # Same iteration on different changes should use the same bot
    # Different iterations should use different bots
    # Ordering of A and B should be "random"
    random_choice.side_effect = ["b", "a", "No more bots"]
    # List of lists because side_effects returns one list element per call
    get_ab_orderings.side_effect = [[1, 0]]
    swarming_bots_list.return_value = _BOT_QUERY_4_BOTS
    get_commit.return_value = {'number': 675460}
    # Goes through a full run of two Executions.

    # Call RunTest.Start() to create an Execution.
    quest = run_test.RunTest('server', DIMENSIONS, ['arg'], _BASE_SWARMING_TAGS,
                             None, None)

    # Propagate a thing that looks like a job.
    quest.PropagateJob(
        FakeJob('cafef00d', 'https://pinpoint/cafef00d', 'try',
                'user@example.com'))

    changeA = change.Change("a", variant=0)
    changeB = change.Change("b", variant=1)
    execution_a_0 = quest.Start(changeA, 'isolate server', 'hasha/111')
    quest.Start(changeA, 'isolate server', 'hasha/111')
    quest.Start(changeB, 'isolate server', 'hashb/111')
    quest.Start(changeB, 'isolate server', 'hashb/111')

    swarming_task_result.assert_not_called()
    swarming_tasks_new.assert_not_called()

    # Call the first Poll() to start the swarming task.
    swarming_tasks_new.return_value = {'task_id': 'task id'}
    execution_a_0.Poll()

    swarming_task_result.assert_not_called()
    self.assertEqual(swarming_tasks_new.call_count, 4)

    def getPatch(hash, bot):
        return {
            'task_slices': [{
                'expiration_secs': '86400',
                'properties': {
                    'cas_input_root': {
                        'cas_instance': 'cas_instance',
                        'digest': {
                            'hash': hash,
                            'size_bytes': 111,
                        },
                    },
                    'extra_args': ['arg'],
                    'dimensions': DIMENSIONS + [{
                        "key": "id",
                        "value": bot
                    }],
                    'execution_timeout_secs': mock.ANY,
                    'io_timeout_secs': mock.ANY,
                }
            }]
        }
    self.assertNewTaskHasDimensionsMulti(swarming_tasks_new, [
        getPatch("hashb", "b"),
        getPatch("hasha", "b"),
        getPatch("hasha", "a"),
        getPatch("hashb", "a")
    ])


  def testSuccess_Cas(self, get_commit, swarming_task_result,
                      swarming_tasks_new, swarming_bots_list):
    swarming_bots_list.return_value = _BOT_QUERY_1_BOT
    get_commit.return_value = {'number': 675460}
    # Goes through a full run of two Executions.

    # Call RunTest.Start() to create an Execution.
    quest = run_test.RunTest('server', DIMENSIONS, ['arg'], _BASE_SWARMING_TAGS,
                             None, None)

    # Propagate a thing that looks like a job.
    quest.PropagateJob(
        FakeJob('cafef00d', 'https://pinpoint/cafef00d', 'try',
                'user@example.com'))

    execution_a = quest.Start(
        change.Change("a", variant=0), 'cas_instance', 'xxxxxxxx/111')
    execution_b = quest.Start(
        change.Change("b", variant=1), 'cas_instance', 'xxxxxxxx/111')

    swarming_task_result.assert_not_called()
    swarming_tasks_new.assert_not_called()

    # Call the first Poll() to start the swarming task.
    swarming_tasks_new.return_value = {'task_id': 'task id'}
    execution_b.Poll()
    execution_a.Poll()

    swarming_task_result.assert_not_called()
    self.assertEqual(swarming_tasks_new.call_count, 2)
    self.assertNewTaskHasDimensions(
        swarming_tasks_new, {
            'task_slices': [{
                'expiration_secs': '86400',
                'properties': {
                    'cas_input_root': {
                        'cas_instance': 'cas_instance',
                        'digest': {
                            'hash': 'xxxxxxxx',
                            'size_bytes': 111,
                        },
                    },
                    'extra_args': ['arg'],
                    'dimensions': DIMENSIONS + [{
                        "key": "id",
                        "value": "a"
                    }],
                    'execution_timeout_secs': mock.ANY,
                    'io_timeout_secs': mock.ANY,
                }
            }]
        })
    self.assertFalse(execution_b.completed)
    self.assertFalse(execution_b.failed)

    # Call subsequent Poll()s to check the task status.
    swarming_task_result.return_value = {'state': 'PENDING'}
    execution_b.Poll()

    self.assertFalse(execution_b.completed)
    self.assertFalse(execution_b.failed)

    swarming_task_result.return_value = {
        'bot_id': 'a',
        'exit_code': 0,
        'failure': False,
        'cas_output_root': {
            'cas_instance': 'projects/x/instances/default_instance',
            'digest': {
                'hash': 'e3b0c44298fc1c149afbf4c8996fb',
                'size_bytes': 1,
            },
        },
        'state': 'COMPLETED',
    }
    execution_b.Poll()

    self.assertTrue(execution_b.completed)
    self.assertFalse(execution_b.failed)
    self.assertEqual(execution_b.result_values, ())
    self.assertEqual(
        execution_b.result_arguments, {
            'cas_root_ref': {
                'cas_instance': 'projects/x/instances/default_instance',
                'digest': {
                    'hash': 'e3b0c44298fc1c149afbf4c8996fb',
                    'size_bytes': 1,
                },
            }
        })
    self.assertEqual(
        execution_b.AsDict(), {
            'completed':
                True,
            'exception':
                None,
            'details': [
                {
                    'key': 'bot',
                    'value': 'a',
                    'url': 'server/bot?id=a',
                },
                {
                    'key': 'task',
                    'value': 'task id',
                    'url': 'server/task?id=task id',
                },
                {
                    'key': 'isolate',
                    'value': 'e3b0c44298fc1c149afbf4c8996fb/1',
                    'url': 'https://cas-viewer.appspot.com/'
                           'projects/x/instances/default_instance/blobs/'
                           'e3b0c44298fc1c149afbf4c8996fb/1/tree',
                },
            ],
        })

  def testStart_NoSwarmingTags(self, get_commit, swarming_task_result,
                               swarming_tasks_new, swarming_bots_list):
    swarming_bots_list.return_value = _BOT_QUERY_1_BOT
    get_commit.return_value = {'number': 675460}
    del swarming_task_result
    del swarming_tasks_new

    quest = run_test.RunTest('server', DIMENSIONS, ['arg'], None, None, None)
    quest.PropagateJob(
        FakeJob('cafef00d', 'https://pinpoint/cafef00d', 'try',
                'user@example.com'))
    quest.Start('change_1', 'isolate server', 'input isolate hash')


@mock.patch('dashboard.services.swarming.Bots.List')
@mock.patch('dashboard.services.swarming.Tasks.New')
@mock.patch('dashboard.services.swarming.Task.Result')
@mock.patch('dashboard.services.crrev_service.GetCommit')
class SwarmingTaskStatusTest(_RunTestExecutionTest):

  def testSwarmingError(self, get_commit, swarming_task_result,
                        swarming_tasks_new, swarming_bots_list):
    swarming_bots_list.return_value = _BOT_QUERY_1_BOT
    get_commit.return_value = {'number': 675460}
    swarming_task_result.return_value = {'state': 'BOT_DIED'}
    swarming_tasks_new.return_value = {'task_id': 'task id'}

    quest = run_test.RunTest('server', DIMENSIONS, ['arg'], _BASE_SWARMING_TAGS,
                             None, None)
    quest.PropagateJob(
        FakeJob('cafef00d', 'https://pinpoint/cafef00d', 'try',
                'user@example.com'))
    execution = quest.Start(
        change.Change("a", variant=0), 'isolate server', 'input isolate hash')
    quest.Start(
        change.Change("a", variant=1), 'isolate server', 'input isolate hash')
    execution.Poll()
    execution.Poll()

    self.assertTrue(execution.completed)
    self.assertTrue(execution.failed)
    last_exception_line = execution.exception['traceback'].splitlines()[-1]
    self.assertTrue(last_exception_line.startswith('SwarmingTaskError'))

  @mock.patch('dashboard.services.swarming.Task.Stdout')
  def testTestError(self, swarming_task_stdout, get_commit,
                    swarming_task_result, swarming_tasks_new,
                    swarming_bots_list):
    swarming_bots_list.return_value = _BOT_QUERY_1_BOT
    get_commit.return_value = {'number': 675460}
    swarming_task_stdout.return_value = {'output': ''}
    swarming_task_result.return_value = {
        'bot_id': 'a',
        'exit_code': 1,
        'failure': True,
        'state': 'COMPLETED',
        'outputs_ref': {
            'isolatedserver': 'https://server',
            'isolated': 'deadc0de',
        },
    }
    swarming_tasks_new.return_value = {'task_id': 'task id'}

    quest = run_test.RunTest('server', DIMENSIONS, ['arg'], _BASE_SWARMING_TAGS,
                             None, None)
    quest.PropagateJob(
        FakeJob('cafef00d', 'https://pinpoint/cafef00d', 'try',
                'user@example.com'))
    execution = quest.Start(
        change.Change("a", variant=0), 'isolate server', 'input isolate hash')
    quest.Start(
        change.Change("a", variant=1), 'isolate server', 'input isolate hash')
    execution.Poll()
    execution.Poll()

    self.assertTrue(execution.completed)
    self.assertTrue(execution.failed)
    logging.debug('Exception: %s', execution.exception)
    self.assertIn('https://server/browse?digest=deadc0de',
                  execution.exception['traceback'])


@mock.patch('dashboard.services.swarming.Bots.List')
@mock.patch('dashboard.services.swarming.Tasks.New')
@mock.patch('dashboard.services.swarming.Task.Result')
@mock.patch('dashboard.services.crrev_service.GetCommit')
class BotIdHandlingTest(_RunTestExecutionTest):

  def testExecutionExpired(self, get_commit, swarming_task_result,
                           swarming_tasks_new, swarming_bots_list):
    # If the Swarming task expires, the bots are overloaded or the dimensions
    # don't correspond to any bot. Raise an error that's fatal to the Job.
    swarming_bots_list.return_value = _BOT_QUERY_1_BOT
    get_commit.return_value = {'number': 675460}
    swarming_tasks_new.return_value = {'task_id': 'task id'}
    swarming_task_result.return_value = {'state': 'EXPIRED'}

    quest = run_test.RunTest('server', DIMENSIONS, ['arg'], _BASE_SWARMING_TAGS,
                             None, None)
    quest.PropagateJob(
        FakeJob('cafef00d', 'https://pinpoint/cafef00d', 'try',
                'user@example.com'))
    execution_a = quest.Start(
        change.Change("a", variant=0), 'isolate server', 'input isolate hash')
    quest.Start(
        change.Change("a", variant=1), 'isolate server', 'input isolate hash')
    execution_a.Poll()
    with self.assertRaises(errors.SwarmingExpired):
      execution_a.Poll()

  def testNoBotsAvailable(self, get_commit, swarming_task_result,
                          swarming_tasks_new, swarming_bots_list):
    swarming_bots_list.return_value = _BOT_QUERY_0_BOTS
    get_commit.return_value = {'number': 675460}
    swarming_tasks_new.return_value = {'task_id': 'task id'}
    swarming_task_result.return_value = {'state': 'CANCELED'}

    quest = run_test.RunTest('server', DIMENSIONS, ['arg'], _BASE_SWARMING_TAGS,
                             None, None)
    quest.PropagateJob(
        FakeJob('cafef00d', 'https://pinpoint/cafef00d', 'try',
                'user@example.com'))
    with self.assertRaises(errors.SwarmingNoBots):
      quest.Start('change_1', 'isolate server', 'input isolate hash')

  def testBisectsDontUsePairing(self, get_commit, swarming_task_result,
                                swarming_tasks_new, swarming_bots_list):
    swarming_bots_list.return_value = _BOT_QUERY_1_BOT
    get_commit.return_value = {'number': 675460}
    swarming_tasks_new.return_value = {'task_id': 'task id'}
    swarming_task_result.return_value = {'state': 'CANCELED'}

    quest = run_test.RunTest('server', DIMENSIONS, ['arg'], _BASE_SWARMING_TAGS,
                             None, None)
    quest.PropagateJob(
        FakeJob('cafef00d', 'https://pinpoint/cafef00d', 'performance',
                'user@example.com'))
    quest.Start('change_1', 'isolate server', 'input isolate hash')
    self.assertEqual(swarming_bots_list.call_count, 0)

  def testSimultaneousExecutions(self, get_commit, swarming_task_result,
                                 swarming_tasks_new, swarming_bots_list):
    swarming_bots_list.return_value = _BOT_QUERY_1_BOT
    get_commit.return_value = {'number': 675460}
    quest = run_test.RunTest('server', DIMENSIONS, ['arg'], _BASE_SWARMING_TAGS,
                             None, None)
    quest.PropagateJob(
        FakeJob('cafef00d', 'https://pinpoint/cafef00d', 'try',
                'user@example.com'))
    execution_1 = quest.Start(
        change.Change("a", variant=0), 'input isolate server',
        'input isolate hash')
    execution_2 = quest.Start(
        change.Change("a", variant=1), 'input isolate server',
        'input isolate hash')

    swarming_tasks_new.return_value = {'task_id': 'task id'}
    swarming_task_result.return_value = {'state': 'PENDING'}
    execution_1.Poll()
    execution_2.Poll()

    self.assertEqual(swarming_tasks_new.call_count, 2)

    swarming_task_result.return_value = {
        'bot_id': 'a',
        'exit_code': 0,
        'failure': False,
        'outputs_ref': {
            'isolatedserver': 'output isolate server',
            'isolated': 'output isolate hash',
        },
        'state': 'COMPLETED',
    }
    execution_1.Poll()
    execution_2.Poll()

    self.assertEqual(swarming_tasks_new.call_count, 2)
