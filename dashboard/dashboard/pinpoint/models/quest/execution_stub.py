# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from dashboard.pinpoint.models.quest import execution


class _ExecutionStub(execution.Execution):

  def _AsDict(self):
    return {'details key': 'details value'}

  def _Poll(self):
    raise NotImplementedError()


class ExecutionException(_ExecutionStub):
  """This Execution always fails with a fatal exception on first Poll()."""

  def _Poll(self):
    raise StandardError('An unhandled, unexpected exception.')


class ExecutionFail(_ExecutionStub):
  """This Execution always fails on first Poll()."""

  def _Poll(self):
    raise Exception('Expected error for testing.')


class ExecutionFail2(_ExecutionStub):
  """This Execution always fails on first Poll()."""

  def _Poll(self):
    raise Exception('A different expected error for testing.')


class ExecutionPass(_ExecutionStub):
  """This Execution always completes on first Poll()."""

  def _Poll(self):
    self._Complete(result_arguments={'arg key': 'arg value'},
                   result_values=(1, 2, 3))


class ExecutionSpin(_ExecutionStub):
  """This Execution never completes."""

  def _Poll(self):
    pass
