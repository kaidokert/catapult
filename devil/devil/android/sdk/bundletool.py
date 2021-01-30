# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""This module wraps bundletool."""

from distutils import spawn
import json

from devil import base_error
from devil import devil_env
from devil.utils import cmd_helper
from devil.utils import decorators
from devil.utils import lazy

with devil_env.SysPath(devil_env.PY_UTILS_PATH):
  from py_utils import tempfile_ext

_bundletool_path = lazy.WeakConstant(lambda: devil_env.config.FetchPath(
    'bundletool'))


@decorators.Memoize
def _FindJava():
  return spawn.find_executable('java')


def ExtractApks(output_dir,
                apks_path,
                abis,
                locales,
                features,
                pixel_density,
                sdk_version,
                modules=None):
  """Extracts splits from APKS archive.

  Args:
    output_dir: Directory to extract splits into.
    apks_path: Path to APKS archive.
    abis: ABIs to support.
    locales: Locales to support.
    features: Device features to support.
    pixel_density: Pixel density to support.
    sdk_version: Target SDK version.
    modules: Extra modules to install.
  """
  java_path = _FindJava()
  if not java_path:
    raise base_error.BaseError("Unable to find 'java' executable on PATH.")
  device_spec = {
      'supportedAbis': abis,
      'supportedLocales': ['%s-%s' % l for l in locales],
      'deviceFeatures': features,
      'screenDensity': pixel_density,
      'sdkVersion': sdk_version,
  }
  with tempfile_ext.TemporaryFileName(suffix='.json') as device_spec_path:
    with open(device_spec_path, 'w') as f:
      json.dump(device_spec, f)
    cmd = [
        java_path,
        '-jar',
        _bundletool_path.read(),
        'extract-apks',
        '--apks=%s' % apks_path,
        '--device-spec=%s' % device_spec_path,
        '--output-dir=%s' % output_dir,
    ]
    if modules:
      cmd += ['--modules=%s' % ','.join(modules)]
    status, stdout, stderr = cmd_helper.GetCmdStatusOutputAndError(cmd)
    if status != 0:
      raise base_error.BaseError('Failed running {} with output\n{}\n{}'.format(
          ' '.join(cmd), stdout, stderr))
