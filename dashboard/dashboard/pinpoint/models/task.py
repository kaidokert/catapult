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

from google.appengine.ext import ndb

__all__ = (
    'PopulateTaskGraph',
    'TaskGraph',
    'TaskVertex',
    'Dependency',
    'Evaluate',
    'ExtendTaskGraph',
    'UpdateTask',
    'AppendTasklog',
)

TaskVertex = collections.namedtuple('TaskVertex',
                                    ('id', 'vertex_type', 'payload'))
Dependency = collections.namedtuple('Dependency', ('from_', 'to'))
TaskGraph = collections.namedtuple('TaskGraph', ('vertices', 'edges'))
TraversalTask = collections.namedtuple(
    'TraversalTask', ('id', 'task_type', 'payload', 'status', 'dependencies'))

VALID_TRANSITIONS = {
    'pending': {'ongoing', 'completed', 'failed', 'cancelled'},
    'ongoing': {'completed', 'failed', 'cancelled'},
    'cancelled': {'pending'},
    'completed': {'pending'},
    'failed': {'pending'},
}

WHITE, GREY, BLACK = (0, 1, 2)

ReconstitutedTaskGraph = collections.namedtuple('ReconstitutedTaskGraph',
                                                ('terminal_tasks', 'tasks'))


class Error(Exception):
  pass


class InvalidAmendment(Error):
  pass


class TaskNotFound(Error):
  pass


class InvalidTransition(Error):
  pass


# These are internal-only models, used as an implementation detail of the
# execution engine.
class Task(ndb.Model):
  """A Task associated with a Pinpoint Job.

  Task instances are always associated with a Job. Tasks represent units of work
  that are in well-defined states. Updates to Task instances are transactional
  and need to be.
  """
  task_type = ndb.StringProperty(required=True)
  status = ndb.StringProperty(required=True, choices=VALID_TRANSITIONS.keys())
  payload = ndb.JsonProperty(compressed=True, indexed=False)
  dependencies = ndb.KeyProperty(repeated=True, kind='Task')
  created = ndb.DateTimeProperty(required=True, auto_now_add=True)
  updated = ndb.DateTimeProperty(required=True, auto_now_add=True)


class TaskLog(ndb.Model):
  """Log entries associated with Task instances.

  TaskLog instances are always associated with a Task. These entries are
  immutable once created.
  """
  timestamp = ndb.DateTimeProperty(
      required=True, auto_now_add=True, indexed=False)
  message = ndb.TextProperty()
  payload = ndb.JsonProperty(compressed=True, indexed=False)


@ndb.transactional
def PopulateTaskGraph(job, graph):
  """Populate the Datastore with Task instances associated with a Job.

  The `graph` argument must have two properties: a collection of `TaskVertex`
  instances
  """
  if job is None:
    raise ValueError('job must not be None.')

  job_key = job.key
  tasks = {
      v.id: Task(
          key=ndb.Key(Task, v.id, parent=job_key),
          task_type=v.vertex_type,
          payload=v.payload,
          status='pending') for v in graph.vertices
  }
  dependencies = set()
  for dependency in graph.edges:
    dependency_key = ndb.Key(Task, dependency.to, parent=job_key)
    if dependency not in dependencies:
      tasks[dependency.from_].dependencies.append(dependency_key)
      dependencies.add(dependency)

  ndb.put_multi(tasks.values(), use_cache=True)


@ndb.transactional
def ExtendTaskGraph(job, vertices, dependencies):
  """Add new vertices and dependency links to the graph.

  Args:
    job: a dashboard.pinpoint.model.job.Job instance.
    vertices: an iterable of TaskVertex instances.
    dependencies: an iterable of Dependency instances.
  """
  if job is None:
    raise ValueError('job must not be None.')
  if not vertices and not dependencies:
    return

  job_key = job.key
  amendment_task_graph = {
      v.id: Task(
          key=ndb.Key(Task, v.id, parent=job_key),
          task_type=v.vertex_type,
          status='pending') for v in vertices
  }

  # Ensure that the keys we're adding are not in the graph yet.
  current_tasks = Task.query(ancestor=job_key).fetch()
  current_task_keys = set(t.key for t in current_tasks)
  new_tasks = set(t.key for t in amendment_task_graph.values())
  overlap = new_tasks.intersection(current_task_keys)
  if overlap:
    raise InvalidAmendment('vertices (%r) already in task graph.' % (overlap,))

  # Then we add the dependencies.
  current_task_graph = {t.key.id(): t for t in current_tasks}
  handled_dependencies = set()
  update_filter = set(amendment_task_graph)
  for dependency in dependencies:
    dependency_key = ndb.Key(Task, dependency.to, parent=job_key)
    if dependency not in handled_dependencies:
      current_task = current_task_graph.get(dependency.from_)
      amendment_task = amendment_task_graph.get(dependency.from_)
      if current_task is None and amendment_task is None:
        raise InvalidAmendment('dependency `from` (%s) not in amended graph.' %
                               (dependency.from_,))
      if current_task:
        current_task_graph[dependency.from_].dependencies.append(dependency_key)
      if amendment_task:
        amendment_task_graph[dependency.from_].dependencies.append(
            dependency_key)
      handled_dependencies.add(dependency)
      update_filter.add(dependency.from_)

  logging.debug('Adding vertices [%s] and edges [%s]',
                amendment_task_graph.keys(),
                [(dep.from_, dep.to) for dep in handled_dependencies])

  ndb.put_multi(
      itertools.chain(
          amendment_task_graph.values(),
          [t for id_, t in current_task_graph.items() if id_ in update_filter]),
      use_cache=True)


@ndb.transactional
def UpdateTask(job, task_id, new_state=None, payload=None):
  """Update a task.

  This enforces that the status transitions are semantically correct, where only
  the following transitions are supported:

    pending -> ongoing
    ongoing -> { completed | failed }
    completed -> pending
    failed -> pending

  This also allows us to update the payload.

  At least one of 'new_state' and 'payload' must be present in the call to this
  function.
  """
  if new_state is None and payload is None:
    raise ValueError('Set one of `new_state` or `payload`.')

  if new_state and new_state not in VALID_TRANSITIONS:
    raise InvalidTransition('Unknown state: %s' % (new_state,))

  task = Task.get_by_id(task_id, parent=job.key)
  if not task:
    raise TaskNotFound('Task with id "%s" not found for job "%s".' %
                       (task_id, job.job_id))

  if new_state:
    valid_transitions = VALID_TRANSITIONS.get(task.status)
    if new_state not in valid_transitions:
      raise InvalidTransition(
          'Attempting transition from "%s" to "%s" not in {%s}.' %
          (task.status, new_state, valid_transitions))
    task.status = new_state

  if payload:
    task.payload = payload

  task.put()


@ndb.transactional
def AppendTasklog(job, task_id, message, payload):
  task_log = TaskLog(
      parent=ndb.Key(Task, task_id, parent=job.key),
      message=message,
      payload=payload)
  task_log.put()


@ndb.transactional()
def _LoadTaskGraph(job):
  tasks = Task.query(ancestor=job.key).fetch()
  # The way we get the terminal tasks is by looking at tasks where nothing
  # depends on them.
  has_dependents = set()
  for task in tasks:
    has_dependents |= set(dep for dep in task.dependencies)
  terminal_tasks = [t.key for t in tasks if t.key not in has_dependents]
  return ReconstitutedTaskGraph(
      terminal_tasks=terminal_tasks, tasks={task.key: task for task in tasks})


@ndb.non_transactional
def Evaluate(job, event, evaluator):
  if job is None:
    raise ValueError('job must not be None.')

  first = True
  accumulator = {}
  actions = []
  while first or actions:
    first = False
    for action in actions:
      logging.debug('Running action: %r', action)
      # Each action should be a callable which takes the accumulator as an
      # input. We want to run each action in their own transaction as well.
      # This must not be called in a transaction.
      ndb.transaction(
          functools.partial(action, accumulator),
          # We want to have all transactions to be independent.
          propagation=ndb.TransactionOptions.INDEPENDENT)

    # Clear the actions and accumulator for this traversal.
    actions = []
    accumulator = {}

    # Load the graph transactionally.
    graph = _LoadTaskGraph(job)

    if not graph.tasks:
      logging.debug('Task graph empty for job %s', job.job_id)
      return

    # First get all the "terminal" tasks, and traverse the dependencies in a
    # depth-first-search.
    task_stack = [graph.tasks[task] for task in graph.terminal_tasks]

    # If the stack is empty, we should start at an arbitrary point.
    if not task_stack:
      task_stack = [graph.tasks.values()[0]]
    vertex_colours = {}
    while task_stack:
      task = task_stack[-1]
      colour = vertex_colours.get(task.key, WHITE)
      if colour == GREY:
        # We isolate the ndb model `Task` from the evaluator, to avoid
        # accidentially modifying the state in datastore.
        traversal_task = TraversalTask(
            id=task.key.id(),
            task_type=task.task_type,
            payload=task.payload,
            status=task.status,
            dependencies=[dep.id() for dep in task.dependencies])
        result_actions = evaluator(traversal_task, event, accumulator)
        if result_actions:
          actions.extend(result_actions)
        vertex_colours[task.key] = BLACK
        task_stack.pop()
      elif colour == WHITE:
        # This vertex is coloured white, we should traverse the dependencies.
        vertex_colours[task.key] = GREY
        for dependency in task.dependencies:
          if vertex_colours.get(dependency, WHITE) == WHITE:
            task_stack.append(graph.tasks[dependency])
      else:
        assert colour == BLACK
