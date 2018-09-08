# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os

from devil import devil_env
from devil.utils import lazy


def GetPath(build_tool):
  # Use a specifically configured tool, then the SDK version, then the default version?
  return devil_env.config.LocalPath(build_tool)


def _PathInLocalSdk(build_tool):
  build_tools_path = _build_tools_path.read()
  return (os.path.join(build_tools_path, build_tool) if build_tools_path
          else None)


def _FindBuildTools():
  android_sdk_path = devil_env.config.LocalPath('android_sdk')
  if not android_sdk_path:
    return None

  build_tools_contents = os.listdir(
      os.path.join(android_sdk_path, 'build-tools'))

  if not build_tools_contents:
    return None
  else:
    if len(build_tools_contents) > 1:
      build_tools_contents.sort()
    return os.path.join(android_sdk_path, 'build-tools',
                        build_tools_contents[-1])


_build_tools_path = lazy.WeakConstant(_FindBuildTools)
