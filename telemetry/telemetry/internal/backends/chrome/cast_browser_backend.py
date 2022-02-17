# Copyright 2022 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import os
import re
import subprocess
import time
import tempfile

from telemetry.internal.backends.chrome import chrome_browser_backend

import py_utils


_RUNTIME_CONFIG_TEMPLATE = """
{{
  "grpc": {{
   "cast_core_service_endpoint": "unix:/tmp/cast/grpc/core-service",
   "platform_service_endpoint": "unix:/tmp/cast/grpc/platform-service"
 }},
 "runtimes": [
   {{
     "name": "Cast Web Runtime",
     "type": "CAST_WEB",
     "executable": "{runtime_dir}",
     "args": [
       "--no-sandbox",
       "--no-wifi",
       "--runtime-service-path=%runtime_endpoint%",
       "--cast-core-runtime-id=%runtime_id%",
       "--allow-running-insecure-content",
       "--minidump-path=/tmp/cast/minidumps",
       "--disable-audio-output",
       "--ozone-platform=x11"
     ],
     "capabilities": {{
       "video_supported": true,
       "audio_supported": true,
       "metrics_recorder_supported": true,
       "applications": {{
         "supported": [],
         "unsupported": [
           "CA5E8412",
           "85CDB22F", "8E6C866D"
         ]
       }}
     }}
   }}
 ]
}}
"""

class CastRuntime(object):
  def __init__(self, root_dir, runtime_dir):
    self._root_dir = root_dir
    self._runtime_dir = runtime_dir
    self._runtime_process = None
    self._app_dir = os.path.join(root_dir, 'blaze-bin', 'third_party',
                                 'castlite', 'public', 'sdk', 'samples',
                                 'platform_app', 'platform_app')
    self._config_file = tempfile.NamedTemporaryFile()

  def Start(self):
    with open(self._config_file.name, 'w') as config_file:
      config_file.write(
          _RUNTIME_CONFIG_TEMPLATE.format(runtime_dir=self._runtime_dir))
    runtime_command = [
        self._app_dir,
        '--config', self._config_file.name
    ]
    self._runtime_process = subprocess.Popen(runtime_command,
                                             stdin=open(os.devnull),
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.STDOUT)
    return self._runtime_process

  def Close(self):
    self._runtime_process.kill()
    self._runtime_process = None


class CastBrowserBackend(chrome_browser_backend.ChromeBrowserBackend):
  def __init__(self, cast_platform_backend, browser_options,
               browser_directory, profile_directory):
    super(CastBrowserBackend, self).__init__(
        cast_platform_backend,
        browser_options=browser_options,
        browser_directory=browser_directory,
        profile_directory=profile_directory,
        supports_extensions=False,
        supports_tab_control=False)
    self._browser_process = None
    self._cast_core_process = None
    self._devtools_port = None
    self._output_dir = cast_platform_backend.output_dir
    self._web_runtime = CastRuntime(cast_platform_backend.output_dir,
                                    cast_platform_backend.runtime_dir)

  @property
  def log_file_path(self):
    return None

  def _FindDevToolsPortAndTarget(self):
    return self._devtools_port, None

  def _ReadDevToolsPort(self, stderr):
    def TryReadingPort(f):
      if not f:
        return None
      line = f.readline()
      tokens = re.search(r'Remote debugging port: (\d+)', line)
      return int(tokens.group(1)) if tokens else None
    return py_utils.WaitFor(lambda: TryReadingPort(stderr), timeout=60)

  def Start(self, startup_args):
    cast_core_command = [
        os.path.join(self._root_dir, 'blaze-bin', 'third_party', 'castlite',
                     'public', 'sdk', 'core', 'samples', 'cast_core'),
        '--force_all_apps_discoverable',
        '--remote-debugging-port=0'
    ]
    os.chdir(self._root_dir)
    self._cast_core_process = subprocess.Popen(cast_core_command,
                                               stdin=open(os.devnull),
                                               stdout=subprocess.PIPE,
                                               stderr=subprocess.STDOUT)

    # Wait for Cast Core to start up.
    time.sleep(45)

    self._browser_process = self._web_runtime.Start()

  def GetPid(self):
    return self._browser_process.pid

  def Background(self):
    raise NotImplementedError

  def Close(self):
    super(CastBrowserBackend, self).Close()

    if self._browser_process:
      logging.info('Shutting down Cast browser.')
      self._web_runtime.Close()
    self._browser_process = None

  def IsBrowserRunning(self):
    return bool(self._browser_process)

  def GetStandardOutput(self):
    return 'Stdout is not available for Cast browser.'

  def GetStackTrace(self):
    return (False, 'Stack trace is not yet supported on Cast browser.')

  def SymbolizeMinidump(self, minidump_path):
    logging.info('Symbolizing Minidump is not yet supported on Cast browser.')
    return None
