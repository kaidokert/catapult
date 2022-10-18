# Copyright 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# pylint: disable=import-error
# pylint: disable=no-name-in-module
from __future__ import print_function
from __future__ import absolute_import
import distutils.spawn as spawn
import logging
import os
import re
import stat
import subprocess
import sys

from telemetry.internal.platform import desktop_platform_backend


def _BinaryExistsInSudoersFiles(path, sudoers_file_contents):
  """Returns True if the binary in |path| features in the sudoers file.
  """
  for line in sudoers_file_contents.splitlines():
    if re.match(r'\s*\(.+\) NOPASSWD: %s(\s\S+)*$' % re.escape(path), line):
      return True
  return False


def _CanRunElevatedWithSudo(path, interface=None):
  """Returns True if the binary at |path| appears in the sudoers file.
  If this function returns true then the binary at |path| can be run via sudo
  without prompting for a password.
  """
  cmd = ['/usr/bin/sudo', '-l']
  if interface:
    rc, sudoers, _= interface.RunCmdOnDevice(cmd)
    sudoers = sudoers.strip()
    assert rc == 0, 'sudo -l failed to execute'
  else:
    sudoers = subprocess.check_output(cmd)
  return _BinaryExistsInSudoersFiles(path, sudoers)


class PosixPlatformBackend(desktop_platform_backend.DesktopPlatformBackend):

  # This is an abstract class. It is OK to have abstract methods.
  # pylint: disable=abstract-method

  @property
  def interface(self):
    raise NotImplementedError

  def HasRootAccess(self):
    stdout, _  = self.interface.RunCmdOnDevice(['echo', '$UID'])
    return stdout.strip() == 0

  def RunCommand(self, args):
    stdout, _ = self.interface.RunCmdOnDevice(args)
    return stdout

  def GetFileContents(self, path):
    return self.interface.GetFileContents(path)

  def FindApplication(self, application):
    if self.interface.local:
      return spawn.find_executable(application)
    _, stdout, _ = self.interface.RunCmdOnDeviceWithRC(['which', application])
    return stdout

  def CanLaunchApplication(self, application):
    return bool(self.FindApplication(application))

  def LaunchApplication(
      self, application, parameters=None, elevate_privilege=False):
    assert application, 'Must specify application to launch'

    if os.path.sep not in application:
      application = self.FindApplication(application)
      assert application, 'Failed to find application in path'

    args = [application]

    if parameters:
      assert isinstance(parameters, list), 'parameters must be a list'
      args += parameters

    def IsElevated():
      """ Returns True if the current process is elevated via sudo i.e. running
      sudo will not prompt for a password. Returns False if not authenticated
      via sudo or if telemetry is run on a non-interactive TTY."""
      # `sudo -v` will always fail if run from a non-interactive TTY.
      rc, stdout, stderr = self.RunCmdOnDeviceWithRC(
          ['/usr/bin/sudo', '-nv'])
      stdout += stderr
      # Some versions of sudo set the returncode based on whether sudo requires
      # a password currently. Other versions return output when password is
      # required and no output when the user is already authenticated.
      return rc and not stdout

    def IsSetUID(path):
      """Returns True if the binary at |path| has the setuid bit set."""
      if self.interface.local:
        return (os.stat(path).st_mode & stat.S_ISUID) == stat.S_ISUID
      dirname, basename = os.path.split(path)
      stdout, _ = self.interface.RunCmdOnDevice(['find', dirname, '-perm', '/4000',
                                 '-name', basename
                                 ])
      return stdout.strip == path


    if elevate_privilege and not IsSetUID(application):
      if not self.interface.local:
        logging.warning('Non-local platform interface is always running root')
      else:
        args = ['/usr/bin/sudo'] + args
      if not _CanRunElevatedWithSudo(application) and not IsElevated():
        if not sys.stdout.isatty():
          # Without an interactive terminal (or a configured 'askpass', but
          # that is rarely relevant), there's no way to prompt the user for
          # sudo. Fail with a helpful error message. For more information, see:
          #   https://code.google.com/p/chromium/issues/detail?id=426720
          text = (
              'Telemetry needs to run %s with elevated privileges, but the '
              'setuid bit is not set and there is no interactive terminal '
              'for a prompt. Please ask an administrator to set the setuid '
              'bit on this executable and ensure that it is owned by a user '
              'with the necessary privileges. Aborting.' % application)
          print(text)
          raise Exception(text)
        # Else, there is a tty that can be used for a useful interactive prompt.
        print('Telemetry needs to run %s under sudo. Please authenticate.' %
              application)
        # Synchronously authenticate.
        subprocess.check_call(['/usr/bin/sudo', '-v'])


    return self.interface.StartCmd(
        args)
