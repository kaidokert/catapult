# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import functools
import logging
import time


def RetryOnException(exc_type, retries=3):
  """Decorator to retry running a function if an exception is raised.

  Implements exponential backoff to wait between retries.

  Args:
    exc_type: An exception type (or a tuple of them), on which to retry.
    retries: Number of extra attempts to try. If an exception is raised during
      the last try, the exception is not caught and passed to the caller.
  """
  def Decorator(f):
    @functools.wraps(f)
    def Wrapper(*args, **kwargs):
      wait = 1
      for _ in xrange(kwargs.pop('retries', retries)):
        try:
          return f(*args, **kwargs)
        except exc_type as exc:
          logging.warning(
              '%s raised %s, will retry in %d second%s ...',
              f.__name__, type(exc).__name__, wait, '' if wait == 1 else 's')
          time.sleep(wait)
          wait *= 2
      # Last try with no exception catching.
      return f(*args, **kwargs)
    return Wrapper
  return Decorator
