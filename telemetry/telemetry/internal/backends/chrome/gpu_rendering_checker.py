# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.


class GpuRenderingAssertionFailure(AssertionError):
  pass


def AssertGpuRenderingEnabled(system_info):
  """ Assert the data in |system_info| shows GPU rendering is enabled.

  Args:
    system_info: an instance telemetry.internal.platform.system_info.SystemInfo

  Raises:
    EnvironmentError if GPU rendering is not enabled.
  """
  if system_info.gpu.feature_status['gpu_compositing'] != 'enabled':
    raise GpuRenderingAssertionFailure(
        'GPU rendering is not enabled on the system')
