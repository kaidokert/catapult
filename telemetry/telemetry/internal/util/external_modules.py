# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import importlib
import logging

import psutil  # pylint: disable=import-error

from py_utils import modules_util


def ValidateRequirements():
  # Telemetry depends on features from psutil version 2.0 or higher.
  modules_util.RequireVersion(psutil, '2.0')


# LooseVersion allows versions like "1.8.0rc1" (default numpy on macOS Sierra)
# and "2.4.13.2" (a version of OpenCV 2.x).
MODULES = {
    'cv2': ('2.4.8', '3.0.0'),
    'numpy': ('1.8.0', '1.12.0'),
}


# DEPRECATED: New external modules should be added via vpython. Any version
# requirements may be explicitly listed in ValidateRequirements above.
def ImportRequiredModule(module):
  """Tries to import the desired module.

  Returns:
    The module on success, raises error on failure.
  Raises:
    ImportError: The import failed."""
  versions = MODULES.get(module)
  if versions is None:
    raise NotImplementedError('Please teach telemetry about module %s.' %
                              module)

  module = importlib.import_module(module)
  modules_util.RequireVersion(module, *versions)
  return module


# DEPRECATED: New external modules should be added via vpython. Any version
# requirements may be explicitly listed in ValidateRequirements above.
def ImportOptionalModule(module):
  """Tries to import the desired module.

  Returns:
    The module if successful, None if not."""
  try:
    return ImportRequiredModule(module)
  except ImportError as e:
    # This can happen due to a circular dependency. It is usually not a
    # failure to import module_name, but a failed import somewhere in
    # the implementation. It's important to re-raise the error here
    # instead of failing silently.
    if 'cannot import name' in str(e):
      print 'Possible circular dependency!'
      raise
    logging.warning('Unable to import %s due to: %s', module, e)
    return None
