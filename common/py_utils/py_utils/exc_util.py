# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import functools
import logging
import sys


def BestEffort(func):
  """Decorator to log and dismiss exceptions if one if already being handled.

  Typical usage would be in |Close| or |Disconnect| methods, to dismiss but log
  any further exceptions raised if the current execution context is already
  handling an exception. For example:

      class Client(object):
        def Connect(self):
          # code to connect ...

        @exc_util.BestEffort
        def Disconnect(self):
          # code to disconnect ...

      client = Client()
      try:
        client.Connect()
      except:
        client.Disconnect()
        raise

  If an exception is raised by client.Connect(), and then a second exception
  is raised by client.Disconnect(), the decorator will log the second exception
  and let the original one be re-raised.

  Otherwise, without the decorator, the second exception is the one propagated
  to the caller; while information about the original one, usually more
  important, is completely lost (in Python 2.7 since it does not support
  exception chaining).

  Note that if client.Disconnect() is called in a context where an exception
  is *not* being handled, then any exceptions raised within the method will
  get through and be passed on to callers for them to handle in the usual way.

  The decorator can also be used on cleanup functions meant to be called on
  a finally block, hoewever you must also include an except-raise clause to
  let Python know that the exception is being handled; e.g.:

      @exc_util.BestEffort
      def cleanup():
        # do cleanup things ...

      try:
        process(thing)
      except:
        raise  # Needed to let cleanup know if an exception is being handled.
      finally:
        cleanup()

  Failing to include the except-raise block has the same effect as not
  including the decorator at all. Namely: exceptions during |cleanup| are
  raised and swallow any prior exceptions that ocurred during |process|.
  """
  @functools.wraps(func)
  def Wrapper(*args, **kwargs):
    exc_type = sys.exc_info()[0]
    if exc_type is None:
      # Not currently handling an exception; let any errors raise exceptions
      # as usual.
      func(*args, **kwargs)
    else:
      # Otherwise, we are currently handling an exception, dismiss and log
      # any further cascading errors. Callers are responsible to handle the
      # original exception.
      try:
        func(*args, **kwargs)
      except Exception:  # pylint: disable=broad-except
        logging.exception(
            'While handling a %s, the following exception was also raised:',
            exc_type.__name__)

  return Wrapper


class OriginalException(object):
  """While handling an exception, keep it even if a second exception is raised.

  TODO(perezju): NOT FOR COMMIT.

  For example in:

      try:
        client.Connect()
      except:
        with reraise.OriginalException():
          client.Disconnect()

  if an exception is raised during Connect, and then a second exception is
  raised during Disconnect; the seccond exception will be logged, while the
  first one is re-raised. Otherwise, in Python 2.7 and without this wrapper,
  only the second exception is raised, while the first one (usually more
  important) is lost.

  Can also be used in a finally block. However, you must also include an
  empty except-raise block to give a chance for the original exception to be
  recorded, e.g.:

      try:
        worker.Process()
      except:
        raise
      finally:
        with reraise.OriginalException():
          worker.CleanUp()

  Note that a try-except-finally block wont work; however you can nest them
  as:

      try:
        try:
          worker.Process()
        except:
          with reraise.OriginalException():
            worker.Disconnect()
      except:
        raise
      finally:
        with reraise.OriginalException():
          worker.CleanUp()

  This is largely a workaround for Python 2.7, and is not needed for Python 3
  where chained exceptions will do the right thing for you.
  """
  def __init__(self):
    self.exc_type, self.exc_value, self.exc_traceback = sys.exc_info()

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, exc_traceback):
    if self.exc_type is not None:
      if exc_type is not None:
        logging.exception(
            'While handling a %s, the following %s was also raised:',
            self.exc_type.__name__, exc_type.__name__)
      raise self.exc_type, self.exc_value, self.exc_traceback
