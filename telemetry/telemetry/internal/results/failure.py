# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import sys
import traceback


class Failure(object):

  def __init__(self, exc_info, handleable=True):
    """An object representing a failure when running the page.

    Args:
      exc_info: The exception info (sys.exc_info()) corresponding to
          this failure.
      handleable: A boolean which indicates whether this failure was able to be
          handled by Telemetry.
    """
    self._exc_info = exc_info
    self._handleable = handleable

  @classmethod
  def FromMessage(cls, message, handleable=True):
    """Creates a Failure for a given string message.

    Args:
      message: A string message describing the failure.
    """
    exc_info = cls._GetExcInfoFromMessage(message)
    return Failure(exc_info, handleable)

  @staticmethod
  def _GetExcInfoFromMessage(message):
    try:
      raise Exception(message)
    except Exception: # pylint: disable=broad-except
      return sys.exc_info()

  def __repr__(self):
    return 'Failure(%s, %s)' % (
        GetStringFromExcInfo(self._exc_info), self._handleable)

  @property
  def exc_info(self):
    return self._exc_info

  @property
  def handleable(self):
    return self._handleable


def GetStringFromExcInfo(exc_info):
  return ''.join(traceback.format_exception(*exc_info))
