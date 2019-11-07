# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import logging

from dashboard.pinpoint.models import evaluators
from dashboard.pinpoint.models.tasks import find_isolate
from dashboard.pinpoint.models.tasks import run_test
from dashboard.pinpoint.models.tasks import read_value
from dashboard.pinpoint.models.tasks import performance_bisection


class Serializer(evaluators.DispatchByTaskType):
  """Serializes a task graph associated with a job.

  This Serializer follows the same API contract of an Evaluator, which applies
  specific transformations based on the type of a task in the graph.

  The end state of the accumulator is a mapping with the following schema:

    {
      'comparison_mode': <string>
      'metric': <string>
      'quests': [<string>]
      'state': [
        {
          'attempts': [
            {
              'executions': [
                {
                  'completed': <boolean>
                  'exception': <string>
                  'details': [
                    {
                      'key': <string>
                      'value': <string>
                      'url': <string>
                    }
                  ]
                }
              ]
            }
          ]
          'change': { ... }
          'comparisons': {
            'next': <string|None>
            'prev': <string|None>
          }
          'result_values': [
            <float>
          ]
        }
      ]
    }

  NOTE: The 'quests' and 'executions' in the schema are legacy names, which
  refers to the previous quest abstractions from which the tasks and evaluators
  are derived from. We keep the name in the schema to ensure that we are
  backwards-compatible with what the consumers of the data expect (i.e. the Web
  UI).
  """

  def __init__(self):
    super(Serializer, self).__init__({
        'find_isolate':
            evaluators.SequenceEvaluator(
                [find_isolate.Serializer(), BuildTransformer]),
        'run_test':
            evaluators.SequenceEvaluator(
                [run_test.Serializer(), TestTransformer]),
        'read_value':
            evaluators.SequenceEvaluator(
                [read_value.Serializer(), ResultTransformer]),
        'find_culprit':
            evaluators.SequenceEvaluator(
                [performance_bisection.Serializer(), AnalysisTransformer]),
    })

  def __call__(self, task, event, accumulator):
    # First we delegate to the task-specific serializers, and have the
    # domain-aware transformers canonicalise the data in the accumulator. We
    # then do a dictionary merge following a simple protocol for editing a
    # single accumulator. This way the transformers can output a canonical set
    # of transformations to build up the (global) accumulator.
    local_accumulator = {}
    super(Serializer, self).__call__(task, event, local_accumulator)

    logging.debug('Local accumulator: %s', local_accumulator)

    # What we expect to see in the local accumulator is data in the following
    # form:
    #
    #   {
    #      # The 'state' key is required to identify to which change and which
    #      # state we should be performing the actions.
    #      'state': {
    #         'change': {...}
    #         'quest': <string>
    #
    #         # In the quest-based system, we end up with different "execution"
    #         # details, which come in "quest" order. In the task-based
    #         # evaluation model, the we use the 'index' in the 'add_details'
    #         # sub-object to identify the index in the details.
    #         'add_execution': {
    #             'add_details': {
    #                 'index': <int>
    #                 ...
    #             }
    #             ...
    #         }
    #
    #         # This allows us to accumulate the resulting values we encounter
    #         # associated with the change.
    #         'append_result_values': [<float>]
    #
    #         # This allows us to set the comparison result for this change in
    #         # context of other changes.
    #         'set_comparison': {
    #             'next': <string|None>,
    #             'prev': <string|None>,
    #         }
    #      }
    #
    #      # If we see the 'order_changes' key in the local accumulator, then
    #      # that means we can sort the states according to the changes as they
    #      # appear in this list.
    #      'order_changes': [...]
    #
    #      # If we see the 'set_parameters' key in the local accumulator, then
    #      # we can set the overall parameters we're looking to compare and
    #      # convey in the results.
    #      'set_parameters': {
    #          'comparison_mode': <string>
    #          'metric': <string>
    #      }
    #   }
    #
    # At this point we process the accumulator to update the global accumulator
    # following the protocol defined above.
    if 'state' in local_accumulator:
      modification = local_accumulator.get('state')
      logging.debug('Modification = %s', modification)
      states = accumulator.setdefault('state', [])
      quests = accumulator.setdefault('quests', [])

      # We need to find the existing state which matches the quest and the
      # change. If we don't find one, we create the first state entry for that.
      state_index = None
      change = modification.get('change')
      for index, state in enumerate(states):
        if state.get('change') == change:
          state_index = index
          break

      if state_index is None:
        states.append({'attempts': [{'executions': []}], 'change': change})
        state_index = len(states) - 1

      quest = modification.get('quest')
      try:
        quest_index = quests.index(quest)
      except ValueError:
        quests.append(quest)
        quest_index = len(quests) - 1

      add_execution = modification.get('add_execution')
      append_result_values = modification.get('append_result_values')
      attempt_index = modification.get('index', 0)
      set_comparison = modification.get('set_comparison')
      state = states[state_index]
      if add_execution:
        executions = state['attempts'][attempt_index]['executions']
        executions[:len(executions)] = [None] * (
            (quest_index + 1) - len(executions))
        executions[quest_index] = dict(add_execution)

      if append_result_values:
        state.setdefault('result_values', []).extend(append_result_values)

      if set_comparison:
        state.setdefault('comparisons', {}).update(set_comparison)

    if 'order_changes' in local_accumulator:
      # FIXME
      pass

    if 'set_parameters' in local_accumulator:
      modification = local_accumulator.get('set_parameters')
      accumulator['comparison_mode'] = modification.get('comparison_mode')
      accumulator['metric'] = modification.get('metric')

    logging.debug('After Processing: %s', accumulator)


def BuildTransformer(task, _, accumulator):
  """Takes the form:

  {
    <task id> : {
      ...
    }
  }

  And turns it into:

  {
    'state': {
      'change': {...}
      'quest': 'Build'
      'index': <int>
      'add_execution': {
        ...
      }
    }
  }
  """
  logging.debug('BuildTransformer called: %s', task)
  input_data = accumulator.get(task.id)
  if not input_data:
    return None

  result = {
      'state': {
          'change': task.payload.get('change'),
          'quest': 'Build',
          'index': 0,
          'add_execution': input_data,
      }
  }
  accumulator.clear()
  accumulator.update(result)
  logging.debug('After Transform: %s', accumulator)


def TestTransformer(*_):
  pass


def ResultTransformer(*_):
  pass


def AnalysisTransformer(*_):
  pass
