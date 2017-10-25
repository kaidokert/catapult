# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from distutils import version
import importlib
import logging
import sys


def RequireModule(name, min_version=None, max_version=None):
  """Ensure that a module is importable and within a required version range.

  Displays an error and halts the execution of the program if the module
  requirements are not satisfied.

  Args:
    name: A string with the name of the required module.
    min_version: An optional string with the lowest version supported.
    max_version: An optional string with the highest version supported.
  """
  parts = ['version']
  if min_version is not None:
    min_version = version.LooseVersion(min_version)
    parts = [str(min_version), '<='] + parts
  if max_version is not None:
    max_version = version.LooseVersion(max_version)
    parts = parts + ['<=', str(max_version)]
    if min_version is not None:
      assert min_version < max_version
  if len(parts) > 1:
    description = '%s (%s)' % (name, ' '.join(parts))
  else:
    description = name
  try:
    module = importlib.import_module(name)
  except ImportError:
    logging.exception('Failed to import required module: %s', description)
    sys.exit(1)

  cur_version = version.LooseVersion(module.__version__)
  valid_version = ((min_version is None or min_version <= cur_version) and
                   (max_version is None or cur_version <= max_version))
  logging.log(
      logging.INFO if valid_version else logging.CRITICAL,
      '%s %s loaded from: %s', name, cur_version, module.__file__)
  if not valid_version:
    logging.critical('Invalid module version, required: %s', description)
    sys.exit(1)
