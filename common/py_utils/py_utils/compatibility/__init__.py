# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from distutils import version
import importlib
import logging


def RequireModule(name, min_version=None, max_version=None):
  """Ensure that a module is importable and within a required version range.

  Args:
    name: A string with the name of the required module.
    min_version: An optional string with the lowest version supported.
    max_version: An optional string with the highest version supported.

  Raises:
    ImportError: If the module requirements are not satisfied.
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

    # TODO: Some modules may not have a __version__ variable. Update this code
    # to accomodate such modules if we ever require them.
    cur_version = version.LooseVersion(module.__version__)
    valid_version = ((min_version is None or min_version <= cur_version) and
                     (max_version is None or cur_version <= max_version))
    logging.log(
        logging.INFO if valid_version else logging.CRITICAL,
        '%s %s loaded from: %s', name, cur_version, module.__file__)
    if not valid_version:
      raise ImportError('Invalid module version')
  except ImportError:
    logging.critical('Failed to import module, required %s', description)
    raise


def CheckModules():
  # Not compatible with versions below 2.x due to changes in:
  # http://grodola.blogspot.com/2014/01/psutil-20-porting.html
  # Chose 2.2.1 as it's the earliest with documentation on:
  # http://psutil.readthedocs.io/en/release-2.2.1/
  # Tested to work on versions at least up to 5.4.0, but hopefully future
  # versions should also work too.
  # See py_utils.compatibility.psutil_compatibility_test for details.
  RequireModule('psutil', '2.2.1')
