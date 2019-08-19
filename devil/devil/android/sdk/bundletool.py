# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""This module wraps bundletool."""

import json
import os

from devil.android.sdk import build_tools
from devil.utils import cmd_helper
from devil.utils import lazy
from py_utils import tempfile_ext

_bundletool_path = lazy.WeakConstant(lambda: build_tools.GetPath('bundletool'))


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
  device_spec = {
      'supportedAbis': abis,
      'supportedLocales': ['%s-%s' % l for l in locales],
      'deviceFeatures': features,
      'screenDensity': pixel_density,
      'sdkVersion': sdk_version,
  }
  with tempfile_ext.NamedTemporaryDirectory() as tmp_dir:
    device_spec_path = os.path.join(tmp_dir, 'device_spec.json')
    with open(device_spec_path, 'w') as f:
      json.dump(device_spec, f)
    cmd = [
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
      raise Exception('Failed running {} with output\n{}\n{}'.format(
          ' '.join(cmd), stdout, stderr))
