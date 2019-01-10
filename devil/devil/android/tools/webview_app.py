#!/usr/bin/env python
# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""A script to use a package as the WebView provider while running a command."""

import argparse
import contextlib
import logging
import os
import re
import shutil
import sys
import tempfile


if __name__ == '__main__':
  sys.path.append(
      os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   '..', '..', '..')))


from devil.android import apk_helper
from devil.android import device_errors
from devil.android.sdk import version_codes
from devil.android.tools import script_common
from devil.android.tools import system_app
from devil.utils import cmd_helper
from devil.utils import parallelizer
from devil.utils import run_tests_helper

logger = logging.getLogger(__name__)

ANDROID_WEBVIEW_PACKAGE = "com.android.webview"
GOOGLE_WEBVIEW_PACKAGE = "com.google.android.webview"
_SYSTEM_PATH_RE = re.compile(r'^\s*\/system\/')

@contextlib.contextmanager
def UseWebViewProvider(device, apk):
  """A context manager that uses the apk as the webview provider while in scope.

  Args:
    device: (device_utils.DeviceUtils) the device for which the webview apk
      should be used as the provider.
    apk: (str) the path to the webview APK to use.
  """
  package_name = apk_helper.GetPackageName(apk)

  # Only need to check package names for versions under N, for N+ versions,
  # invalid providers will be detected during implementation switching time.
  if device.build_version_sdk < version_codes.NOUGAT:
    if device.HasGoogleFeatures():
      if package_name != GOOGLE_WEBVIEW_PACKAGE:
        raise device_errors.CommandFailedError(
            '%s is not a valid Google WebView package' % package_name,
            str(device))
    else:
      if package_name != ANDROID_WEBVIEW_PACKAGE:
        raise device_errors.CommandFailedError(
          '%s is not a valid Android WebView package' % package_name,
          str(device))

  if device.build_version_sdk in \
      [version_codes.NOUGAT, version_codes.NOUGAT_MR1]:
    logger.warning('Due to webviewupdate bug in Nougat, WebView Fallback Logic '
                   'will be disabled and WebView provider may be changed after '
                   'exit of UseWebViewProvider context manager scope.')

  webview_update = device.GetWebViewUpdateServiceDump()
  original_fallback_logic = webview_update.get('FallbackLogicEnabled', None)
  original_provider = webview_update.get('CurrentWebViewPackage', None)

  # This is only necessary if the provider is a fallback provider, but we can't
  # generally determine this, so we set this just in case.
  device.SetWebViewFallbackLogic(False)

  try:
    # If user installed versions of the package is present, they must be
    # uninstalled first, so that the system version of the package,
    # if any, can be found by the ReplaceSystemApp context manager
    with _UninstallNonSystemApp(device, package_name):
      all_paths = device.GetApplicationPaths(package_name)
      system_paths = _FilterPaths(all_paths, True)
      non_system_paths = _FilterPaths(all_paths, False)
      if non_system_paths:
        raise device_errors.CommandFailedError(
            'Non-System application paths found after uninstallation: ',
            str(non_system_paths))
      elif system_paths:
        # app is system app, use ReplaceSystemApp to install
        with system_app.ReplaceSystemApp(device, package_name, apk):
          _SetWebViewProvider(device, package_name)
          yield
      else:
        # app is not present on device, can directly install
        with _InstallApp(device, apk):
          _SetWebViewProvider(device, package_name)
          yield
  finally:
    # restore the original provider only if it was known and not the current
    # provider
    if original_provider is not None:
      webview_update = device.GetWebViewUpdateServiceDump()
      new_provider = webview_update.get('CurrentWebViewPackage', None)
      if new_provider != original_provider:
        device.SetWebViewImplementation(original_provider)

    # enable the fallback logic only if it was known to be enabled
    if original_fallback_logic is True:
      device.SetWebViewFallbackLogic(True)


def _SetWebViewProvider(device, package_name):
  """ Set the WebView provider to the package_name if supported. """
  if device.build_version_sdk >= version_codes.NOUGAT:
    device.SetWebViewImplementation(package_name)


def _FilterPaths(path_list, is_system):
  """ Return paths in the path_list that are/aren't system paths. """
  paths = []
  for p in path_list:
    if is_system and re.match(_SYSTEM_PATH_RE, p):
      paths.append(p)
    elif not is_system and not re.match(_SYSTEM_PATH_RE, p):
      paths.append(p)
  return paths


def _RebasePath(new_root, old_root):
  """ Graft old_root onto new_root and return the result. """
  return os.path.join(new_root, os.path.relpath(old_root, '/'))


@contextlib.contextmanager
def _UninstallNonSystemApp(device, package_name):
  """ Make package un-installed while in scope. """
  all_paths = device.GetApplicationPaths(package_name)
  user_paths = _FilterPaths(all_paths, False)
  host_paths = []
  if user_paths:
    temp_dir = tempfile.mkdtemp()
    for user_path in user_paths:
      host_path = _RebasePath(temp_dir, user_path)
      # PullFile takes care of host_path creation if needed.
      device.PullFile(user_path, host_path)
      host_paths.append(host_path)
    device.Uninstall(package_name)

  try:
    yield
  finally:
    if user_paths:
      host_paths.reverse()
      for host_path in host_paths:
        device.Install(host_path, reinstall=True)
      shutil.rmtree(temp_dir)


@contextlib.contextmanager
def _InstallApp(device, apk):
  """ Make apk installed while in scope. """
  package_name = apk_helper.GetPackageName(apk)
  device.Install(apk, reinstall=True)
  try:
    yield
  finally:
    device.Uninstall(package_name)


def main(raw_args):
  parser = argparse.ArgumentParser()
  subparsers = parser.add_subparsers()

  def add_common_arguments(p):
    script_common.AddDeviceArguments(p)
    script_common.AddEnvironmentArguments(p)
    p.add_argument(
        '-v', '--verbose', action='count', default=0,
        help='Print more information.')
    p.add_argument('command', nargs='*')

  @contextlib.contextmanager
  def use_webview_provider(device, args):
    with UseWebViewProvider(device, args.package):
      yield

  use_webview_parser = subparsers.add_parser('use-webview')
  use_webview_parser.add_argument(
      '--package', required=True,
      help='The standalone webview package to use as the provider.')
  add_common_arguments(use_webview_parser)
  use_webview_parser.set_defaults(func=use_webview_provider)

  args = parser.parse_args(raw_args)

  run_tests_helper.SetLogLevel(args.verbose)
  script_common.InitializeEnvironment(args)

  devices = script_common.GetDevices(args.devices, args.blacklist_file)
  parallel_devices = parallelizer.SyncParallelizer(
      [args.func(d, args) for d in devices])
  with parallel_devices:
    if args.command:
      return cmd_helper.Call(args.command)
    return 0


if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
