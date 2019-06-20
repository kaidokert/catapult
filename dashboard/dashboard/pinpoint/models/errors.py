# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import


class FatalError(Exception):
  def __init__(self, message):
    super(FatalError, self).__init__(message)


class InformationalError(Exception):
  def __init__(self, message):
    super(InformationalError, self).__init__(message)


class RecoverableError(Exception):
  pass


class BuildIsolateNotFound(FatalError):
  def __init__(self):
    super(BuildIsolateNotFound, self).__init__(
        "Buildbucket says the build completed successfully, "\
        "but Pinpoint can't find the isolate hash.")


class BuildFailed(InformationalError):
  def __init__(self, reason):
    super(BuildFailed, self).__init__(
        'Build failed: %s' % reason)


class BuildCancelled(InformationalError):
  def __init__(self, reason):
    super(BuildCancelled, self).__init__(
        'Build was canceled: %s' % reason)


class BuildGerritURLInvalid(InformationalError):
  def __init__(self, reason):
    super(BuildGerritURLInvalid, self).__init__(
        'Could not find gerrit review url for commit: %s' % reason)


class SwarmingExpired(FatalError):
  """Raised when the Swarming task expires before running.

  This error is fatal, and stops the entire Job. If this error happens, the
  results will be incorrect, and we should stop the Job quickly to avoid
  overloading the bots even further."""
  def __init__(self):
    super(SwarmingExpired, self).__init__(
        'The swarming task expired. The bots are likely '\
        'overloaded, dead, or misconfigured.')


class SwarmingTaskError(InformationalError):
  """Raised when the Swarming task failed and didn't complete.

  If the test completes but fails, that is a SwarmingTestError, not a
  SwarmingTaskError. This error could be something like the bot died, the test
  timed out, or the task was manually canceled."""
  def __init__(self, reason):
    super(SwarmingTaskError, self).__init__(
        'The swarming task failed with state "%s".' % reason)


class SwarmingTaskFailed(InformationalError):
  """Raised when the test fails."""
  def __init__(self, reason):
    super(SwarmingTaskFailed, self).__init__(
        "The test failed. The test's error message was:\n%s" % reason)


class SwarmingTaskFailedNoException(InformationalError):
  def __init__(self):
    super(SwarmingTaskFailedNoException, self).__init__(
        'The test failed. No Python exception '\
        'was found in the log.')

class SwarmingNoBots(InformationalError):
  def __init__(self):
    super(SwarmingNoBots, self).__init__(
        'There are no bots available to run the test.')


class ReadValueNoValues(InformationalError):
  def __init__(self):
    super(ReadValueNoValues, self).__init__(
        'Found matching histogram data, but no values '\
        'were generated by the test.')


class ReadValueNotFound(InformationalError):
  def __init__(self, reason):
    super(ReadValueNotFound, self).__init__(
        'Could not find values matching: %s' % reason)


class ReadValueUnknownStat(InformationalError):
  def __init__(self, reason):
    super(ReadValueUnknownStat, self).__init__(
        'Unknown statistic type: %s' % reason)


class ReadValueChartNotFound(InformationalError):
  def __init__(self, reason):
    super(ReadValueChartNotFound, self).__init__(
        'The chart "%s" is not in the results.' % reason)


class ReadValueTraceNotFound(InformationalError):
  def __init__(self, reason):
    super(ReadValueTraceNotFound, self).__init__(
        'The trace "%s" is not in the results.' % reason)


class ReadValueNoFile(InformationalError):
  def __init__(self, reason):
    super(ReadValueNoFile, self).__init__(
        "The test didn't produce %s." % reason)


class AllRunsFailed(FatalError):
  def __init__(self, exc_count, att_count, exc):
    super(AllRunsFailed, self).__init__(
        'All of the runs failed. The most common error (%d/%d runs) '\
        'was:\n%s' % (exc_count, att_count, exc))


RETRY_LIMIT = "Pinpoint has hit its' retry limit and will terminate this job."
RETRY_FAILED = "Pinpoint wasn't able to reschedule itself to run again."

REFRESH_FAILURE = 'An unknown failure occurred during the run.\n'\
    'Please file a bug under Speed>Bisection with this job.'


