# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Collection of evaluator combinators.

This module exports common evaluator types which are used to compose multiple
specific evaluators. Use these combinators to compose a single evaluator from
multiple specific evaluator implementations, to be used when calling
dashboard.dashboard.pinpoint.model.task.Evalute(...).
"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

__all__ = ('DispatchEvaluator', 'PayloadLiftingEvaluator', 'SequenceEvaluator',
           'FilteringEvaluator', 'TaskTypeFilter', 'NoopEvaluator')


class TaskTypeFilter(object):

  def __init__(self, task_type_filter):
    self._task_type_filter = task_type_filter

  def __call__(self, task, *_):
    return task.task_type == self._task_type_filter


class NoopEvaluator(object):

  def __call__(self, *_):
    return None


class PayloadLiftingEvaluator(object):

  def __init__(self, exclude_keys=None, exclude_event_types=None):
    self._exclude_keys = exclude_keys or {}
    self._exclude_event_types = exclude_event_types or {}

  def __call__(self, task, event, accumulator):
    if event.type in self._exclude_event_types:
      return None

    update = {
        key: val
        for key, val in task.payload.items()
        if key not in self._exclude_keys
    }
    update['status'] = task.status
    accumulator.update({task.id: update})
    return None


class SequenceEvaluator(object):

  def __init__(self, evaluators):
    if not evaluators:
      raise ValueError('Argument `evaluators` must not be empty.')

    self._evaluators = evaluators

  def __call__(self, task, event, accumulator):
    actions = []
    for evaluator in self._evaluators:
      result = evaluator(task, event, accumulator)
      if result:
        actions.extend(result)
    return actions if actions else None


class FilteringEvaluator(object):

  def __init__(self, predicate, delegate):
    if not predicate:
      raise ValueError('Argument `predicate` must not be empty.')
    if not delegate:
      raise ValueError('Argument `delegate` must not be empty.')

    self._predicate = predicate
    self._delegate = delegate

  def __call__(self, task, event, accumulator):
    if self._predicate(task, event, accumulator):
      return self._delegate(task, event, accumulator)
    return None


class DispatchEvaluator(object):

  def __init__(self, evaluator_map, default_evaluator):
    if not evaluator_map and not default_evaluator:
      raise ValueError(
          'Either one of evaluator_map or default_evaluator must be provided.')

    self._evaluator_map = evaluator_map
    self._default_evaluator = default_evaluator or NoopEvaluator

  def __call__(self, task, event, accumulator):
    handler = self._evaluator_map.get(event.type, self._default_evaluator)
    return handler(task, event, accumulator)
