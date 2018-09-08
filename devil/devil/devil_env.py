# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import contextlib
import json
import logging
import os
import platform
import sys
import tempfile
import threading

CATAPULT_ROOT_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', '..'))
PYMOCK_PATH = os.path.join(
    CATAPULT_ROOT_PATH, 'third_party', 'mock')


@contextlib.contextmanager
def SysPath(path):
  sys.path.append(path)
  yield
  if sys.path[-1] != path:
    sys.path.remove(path)
  else:
    sys.path.pop()


_ANDROID_BUILD_TOOLS = {'aapt', 'dexdump', 'split-select'}

_DEVIL_DEFAULT_CONFIG = os.path.abspath(os.path.join(
    os.path.dirname(__file__), 'devil_dependencies.json'))

_LEGACY_ENVIRONMENT_VARIABLES = {
  'ADB_PATH': {
    'dependency_name': 'adb',
    'platform': 'linux2_x86_64',
  },
  'ANDROID_SDK_ROOT': {
    'dependency_name': 'android_sdk',
    'platform': 'linux2_x86_64',
  },
}


def EmptyConfig():
  return {
    'config_type': 'BaseConfig',
    'dependencies': {}
  }


def LocalConfigItem(dependency_name, dependency_platform, dependency_path):
  if isinstance(dependency_path, basestring):
    dependency_path = [dependency_path]
  return {
    dependency_name: {
      'file_info': {
        dependency_platform: {
          'local_paths': dependency_path
        },
      },
    },
  }


def _GetEnvironmentVariableConfig():
  env_config = EmptyConfig()
  path_config = (
      (os.environ.get(k), v)
      for k, v in _LEGACY_ENVIRONMENT_VARIABLES.iteritems())
  path_config = ((p, c) for p, c in path_config if p)
  for p, c in path_config:
    env_config['dependencies'].update(
        LocalConfigItem(c['dependency_name'], c['platform'], p))
  return env_config


class _Environment(object):

  def __init__(self):
    self._config_init_lock = threading.Lock()
    self._config = None
    self._logging_init_lock = threading.Lock()
    self._logging_initialized = False

  def Initialize(self, configs=None, config_files=None):
    """Initialize devil's environment from configuration files.

    This uses all configurations provided via |configs| and |config_files|
    to determine the locations of devil's dependencies. Configurations should
    all take the form described by py_utils.dependency_manager.BaseConfig.
    If no configurations are provided, a default one will be used if available.

    Args:
      configs: An optional list of dict configurations.
      config_files: An optional list of files to load
    """

    with self._config_init_lock:

      self._config = {}

      if configs is None:
        configs = []

      if config_files is None:
        config_files = []

      if 'DEVIL_ENV_CONFIG' in os.environ:
        config_files.append(os.environ.get('DEVIL_ENV_CONFIG'))
      config_files.append(_DEVIL_DEFAULT_CONFIG)

      import pdb; pdb.set_trace()

      for cf in config_files or []:
        with open(cf) as config_json_file:
          config = json.load(config_json_file)
          for value in config.get('dependencies').itervalues():
            for platform_info in value.get('file_info', {}).itervalues():
              platform_info['local_paths'] = [
                  os.path.realpath(os.path.join(os.path.dirname(cf), lp))
                  for lp in platform_info.get('local_paths', [])]
          configs.append(config)

      env_config = _GetEnvironmentVariableConfig()
      if env_config:
        configs.insert(0, env_config)

      for c in reversed(configs):
        for dep_name, dep_info in c.get('dependencies', {}).iteritems():
          fi = dep_info.get('file_info', {})
          for platform_name, platform_info in fi.iteritems():
            local_paths = platform_info.get('local_paths')
            if local_paths:
              self._config[dep_name][platform_name] = local_paths[0]

  def InitializeLogging(self, log_level, formatter=None, handler=None):
    if self._logging_initialized:
      return

    with self._logging_init_lock:
      if self._logging_initialized:
        return

      formatter = formatter or logging.Formatter(
          '%(threadName)-4s  %(message)s')
      handler = handler or logging.StreamHandler(sys.stdout)
      handler.setFormatter(formatter)

      devil_logger = logging.getLogger('devil')
      devil_logger.setLevel(log_level)
      devil_logger.propagate = False
      devil_logger.addHandler(handler)

      import py_utils.cloud_storage
      lock_logger = py_utils.cloud_storage.logger
      lock_logger.setLevel(log_level)
      lock_logger.propagate = False
      lock_logger.addHandler(handler)

      self._logging_initialized = True

  def FetchPath(self, dependency, arch=None, device=None):
    return self._GetPath(dependency, arch=arch, device=device)

  def LocalPath(self, dependency, arch=None, device=None):
    return self._GetPath(dependency, arch=arch, device=device)

  def _GetPath(self, dependency, arch=None, device=None):
    if self._config is None:
      self.Initialize()
    return self._config.get(dependency, {}).get(GetPlatform(arch, device))

  def PrefetchPaths(self, dependencies=None, arch=None, device=None):
    # Deprecated.
    pass


def GetPlatform(arch=None, device=None):
  if arch or device:
    return 'android_%s' % (arch or device.product_cpu_abi)
  return '%s_%s' % (sys.platform, platform.machine())


config = _Environment()

