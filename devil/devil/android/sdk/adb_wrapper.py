# Copyright 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""This module wraps Android's adb tool.

This is a thin wrapper around the adb interface. Any additional complexity
should be delegated to a higher level (ex. DeviceUtils).
"""

import collections
# pylint: disable=import-error
# pylint: disable=no-name-in-module
import distutils.version as du_version
import errno
import logging
import os
import posixpath
import re
import select
import subprocess
import threading

from devil import base_error
from devil import devil_env
from devil.android import decorators
from devil.android import device_errors
from devil.utils import cmd_helper
from devil.utils import lazy
from devil.utils import timeout_retry

with devil_env.SysPath(devil_env.DEPENDENCY_MANAGER_PATH):
  import dependency_manager  # pylint: disable=import-error

logger = logging.getLogger(__name__)


ADB_KEYS_FILE = '/data/misc/adb/adb_keys'
ADB_HOST_KEYS_DIR = os.path.join(os.path.expanduser('~'), '.android')

DEFAULT_TIMEOUT = 30
DEFAULT_RETRIES = 2

_ADB_VERSION_RE = re.compile(r'Android Debug Bridge version (\d+\.\d+\.\d+)')
_EMULATOR_RE = re.compile(r'^emulator-[0-9]+$')
_DEVICE_NOT_FOUND_RE = re.compile(r"error: device '(?P<serial>.+)' not found")
_READY_STATE = 'device'
_SHELL_OUTPUT_START_MARKER = 'StArT'
_SHELL_OUTPUT_END_MARKER = 'DoNe'
_VERITY_DISABLE_RE = re.compile(r'(V|v)erity (is )?(already )?disabled'
                                r'|Successfully disabled verity')
_VERITY_ENABLE_RE = re.compile(r'(V|v)erity (is )?(already )?enabled'
                               r'|Successfully enabled verity')
_WAITING_FOR_DEVICE_RE = re.compile(r'- waiting for device -')


def VerifyLocalFileExists(path):
  """Verifies a local file exists.

  Args:
    path: Path to the local file.

  Raises:
    IOError: If the file doesn't exist.
  """
  if not os.path.exists(path):
    raise IOError(errno.ENOENT, os.strerror(errno.ENOENT), path)


def _CreateAdbEnvironment():
  adb_env = dict(os.environ)
  adb_env['ADB_LIBUSB'] = '0'
  return adb_env


def _FindAdb():
  try:
    return devil_env.config.LocalPath('adb')
  except dependency_manager.NoPathFoundError:
    pass

  try:
    return os.path.join(devil_env.config.LocalPath('android_sdk'),
                        'platform-tools', 'adb')
  except dependency_manager.NoPathFoundError:
    pass

  try:
    return devil_env.config.FetchPath('adb')
  except dependency_manager.NoPathFoundError:
    raise device_errors.NoAdbError()


def _GetVersion():
  # pylint: disable=protected-access
  raw_version = AdbWrapper._RunAdbCmd(['version'], timeout=2, retries=0)
  for l in raw_version.splitlines():
    m = _ADB_VERSION_RE.search(l)
    if m:
      return m.group(1)
  return None


def _ShouldRetryAdbCmd(exc):
  # Errors are potentially transient and should be retried, with the exception
  # of NoAdbError. Exceptions [e.g. generated from SIGTERM handler] should be
  # raised.
  return (isinstance(exc, base_error.BaseError) and
          not isinstance(exc, device_errors.NoAdbError))


DeviceStat = collections.namedtuple('DeviceStat',
                                    ['st_mode', 'st_size', 'st_time'])

class AdbWrapper(object):
  """A wrapper around a local Android Debug Bridge executable."""

  _ADB_ENV = _CreateAdbEnvironment()

  _adb_path = lazy.WeakConstant(_FindAdb)
  _adb_version = lazy.WeakConstant(_GetVersion)

  class PersistentShell(object):
    '''Class to use persistent shell for ADB.

    This class allows a persistent ADB shell to be created, where multiple
    commands can be passed into it. This avoids the overhead of starting
    up a new ADB shell for each command.

    Example of use:
    with PersistentShell('123456789') as pshell:
        pshell.RunCommand('which ls')
        pshell.RunCommand('echo TEST', close=True)
    '''
    def __init__(self, serial):
      """Initialization function:

      Args:
        serial: Serial number of device.
      """
      self._cmd = [AdbWrapper.GetAdbPath(), '-s', serial, 'shell']
      self._process = None
      self._lock = threading.Lock()

    def __enter__(self):
      self.Start()
      self.WaitForReady()
      return self

    def __exit__(self, exc_type, exc_value, tb):
      self.Stop()

    def Start(self):
      """Start the shell."""
      if self._process is not None:
        raise RuntimeError('Persistent shell already running.')
      # pylint: disable=protected-access
      self._process = subprocess.Popen(self._cmd,
                                       stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE,
                                       shell=False,
                                       env=AdbWrapper._ADB_ENV)

    def WaitForReady(self):
      """Wait for the shell to be ready after starting.

      Sends an echo command, then waits until it gets a response.
      """
      self._process.stdin.write('echo\n')
      output_line = self._process.stdout.readline()
      while output_line.rstrip() != '':
        output_line = self._process.stdout.readline()

    def IterRunCommand(self, command, include_status, close=False, timeme=False):
      """Runs an ADB command and yields the output line by line.

      Args:
        command: Command to send.
        include_status: When False, the status code is not included in output.
            When True, the status code, as an int, is the last item.
        close: If true, terminates the persistent shell after the command.

      Rasies:
        AdbShellCommandFailedError - if the persistent shell crashes.

      Yields:
        The output of the command line by line. If include_status is True, the
        last generated output is an integer status code.
      """

      if close:
        send_cmd = '( %s ); echo $?; exit;\n' % command
        (output, _) = self._process.communicate(send_cmd)
        self._process = None
        output_lines = output.splitlines(True)
        if include_status:
          output_lines[-1] = int(output_lines[-1])
        else:
          output_lines = output_lines[:-1]
        for x in output_lines:
          yield x

      else:
        # Ensure there's a newline before DONE as not all commands send a
        # newline.
        send_cmd = 'echo %s; ( %s ); echo \\\\n%s$?\n' % (
            _SHELL_OUTPUT_START_MARKER, command, _SHELL_OUTPUT_END_MARKER)

        # State for the write buffer.
        amt_written = 0

        with self._lock:
          # Enter select loop for subprocess to avoid deadlock problems
          # when reading/writing to children via pipes.
          start_found = False
          while True:
            if self._process.poll() is not None:
              raise device_errors.AdbShellCommandFailedError(
                  command, "ADB shell crashed", status=None,
                  device_serial=self._device_serial)

            # Only wake on stdin availability if the full command has not been
            # sent yet.
            write_list = []
            if amt_written < len(send_cmd):
              write_list = [self._process.stdin]

            (rlist, wlist, _) = select.select(
                [self._process.stdout],
                write_list,
                [])

            # Non-blocking write to the device. If select returns, then any
            # write smaller than select.PIPE_BUF is guaranteed not to block.
            if wlist:
              bytes_to_write = min(select.PIPE_BUF,
                                   len(send_cmd) - amt_written)
              part_to_write = send_cmd[amt_written : amt_written + bytes_to_write]
              self._process.stdin.write(part_to_write)
              self._process.stdin.flush()  # Ensure underlying stdio flushes.
              amt_written += bytes_to_write

            # Read pipe extracting between StArT and DoNe
            if rlist:
              output_line = self._process.stdout.readline()

              # On some versions of android (observed on marshmallow bot), adb
              # shell has a bug where the first line returned after a write
              # seems to be a corrupted buffer that often, but not always,
              # contains the shell prompt plus command written. Inserting an
              # explicit output start marker allows us to skip over these bad
              # lines.
              if not start_found:
                if output_line[:5] == _SHELL_OUTPUT_START_MARKER:
                  start_found = True
                continue

              if output_line[:4] == _SHELL_OUTPUT_END_MARKER:
                if include_status:
                  yield int(output_line[4:])
                break
              yield output_line

    def RunCommand(self, command, close=False, keepends=False, timeme=False):
      """Runs an ADB command and yields the output line by line.

      Args:
        command: Command to send.
        close: If true, terminates the persistent shell after the command.
        keepends: If False, output lines have trailing whitespace removed.

      Rasies:
        AdbShellCommandFailedError - if the persistent shell crashes.

      Returns:
        ([outline1, outline2], 0) - Array of output lines and the status code
      """
      output_iter = self.IterRunCommand(command, True, close, timeme=timeme)
      result = [line if keepends else line.rstrip() for line in output_iter]
      return (result[:-1], result[-1])

    def Stop(self):
      """Stops the ADB process if it is still running."""
      if self._process is not None:
        self._process.stdin.write('exit\n')
        self._process = None

    def EnsureStarted(self):
      """Ensures the shell is running and ready for commands.

      Will restart the shell in case it has crashed.
      """
      if self._process is not None:
        retcode = self._process.poll()
        # If no return code, shell process is alive and hopefully well.
        if retcode is None:
          return
        logging.warning("Adb PersistentShell crashed with code %d", retcode)
        self._process = None

      # self._process will always be None at this point.
      self.Start()
      self.WaitForReady()

  def __init__(self, device_serial, persistent_shell=False):
    """Initializes the AdbWrapper.

    Args:
      device_serial: The device serial number as a string.
      persistent_shell: If True, uses a long-running "adb shell" for executing
          commands
    """
    if not device_serial:
      raise ValueError('A device serial must be specified')
    self._device_serial = str(device_serial)
    self._persistent_shell_instance = None
    if persistent_shell:
      self._persistent_shell_instance = self.PersistentShell(self._device_serial)

  @classmethod
  def GetAdbPath(cls):
    return cls._adb_path.read()

  @classmethod
  def Version(cls):
    return cls._adb_version.read()

  @classmethod
  def _BuildAdbCmd(cls, args, device_serial, cpu_affinity=None):
    if cpu_affinity is not None:
      cmd = ['taskset', '-c', str(cpu_affinity)]
    else:
      cmd = []
    cmd.append(cls.GetAdbPath())
    if device_serial is not None:
      cmd.extend(['-s', device_serial])
    cmd.extend(args)
    return cmd

  # pylint: disable=unused-argument
  @classmethod
  @decorators.WithTimeoutAndConditionalRetries(_ShouldRetryAdbCmd)
  def _RunAdbCmd(cls, args, timeout=None, retries=None, device_serial=None,
                 check_error=True, cpu_affinity=None, additional_env=None):
    if timeout:
      remaining = timeout_retry.CurrentTimeoutThreadGroup().GetRemainingTime()
      if remaining:
        # Use a slightly smaller timeout than remaining time to ensure that we
        # have time to collect output from the command.
        timeout = 0.95 * remaining
      else:
        timeout = None
    env = cls._ADB_ENV.copy()
    if additional_env:
      env.update(additional_env)
    try:
      status, output = cmd_helper.GetCmdStatusAndOutputWithTimeout(
          cls._BuildAdbCmd(args, device_serial, cpu_affinity=cpu_affinity),
          timeout, env=env)
    except OSError as e:
      if e.errno in (errno.ENOENT, errno.ENOEXEC):
        raise device_errors.NoAdbError(msg=str(e))
      else:
        raise

    # Best effort to catch errors from adb; unfortunately adb is very
    # inconsistent with error reporting so many command failures present
    # differently.
    if status != 0 or (check_error and output.startswith('error:')):
      not_found_m = _DEVICE_NOT_FOUND_RE.match(output)
      device_waiting_m = _WAITING_FOR_DEVICE_RE.match(output)
      if (device_waiting_m is not None
          or (not_found_m is not None and
              not_found_m.group('serial') == device_serial)):
        raise device_errors.DeviceUnreachableError(device_serial)
      else:
        raise device_errors.AdbCommandFailedError(
            args, output, status, device_serial)

    return output
  # pylint: enable=unused-argument

  def _RunDeviceAdbCmd(self, args, timeout, retries, check_error=True):
    """Runs an adb command on the device associated with this object.

    Args:
      args: A list of arguments to adb.
      timeout: Timeout in seconds.
      retries: Number of retries.
      check_error: Check that the command doesn't return an error message. This
        does check the error status of adb but DOES NOT check the exit status
        of shell commands.

    Returns:
      The output of the command.
    """
    return self._RunAdbCmd(args, timeout=timeout, retries=retries,
                           device_serial=self._device_serial,
                           check_error=check_error)

  def _IterRunDeviceAdbCmd(self, args, iter_timeout, timeout,
                           check_error=True):
    """Runs an adb command and returns an iterator over its output lines.

    Args:
      args: A list of arguments to adb.
      iter_timeout: Timeout for each iteration in seconds.
      timeout: Timeout for the entire command in seconds.
      check_error: Check that the command succeeded. This does check the
        error status of the adb command but DOES NOT check the exit status
        of shell commands.

    Yields:
      The output of the command line by line.
    """
    return cmd_helper.IterCmdOutputLines(
        self._BuildAdbCmd(args, self._device_serial),
        iter_timeout=iter_timeout,
        timeout=timeout,
        env=self._ADB_ENV,
        check_status=check_error)


  def _Shell(self, command, timeout, retries):
    """Runs a command on the device by executing the "adb shell".

    This is a low-level wrapper for adb shell.

    Returns:
      (output, status)

    Raises:
      device_errors.AdbCommandFailedError: If the shell iteself crashes
    """
    args = ['shell', '( %s );echo %%$?' % command.rstrip()]
    output = self._RunDeviceAdbCmd(args, timeout, retries, check_error=False)
    output_end = output.rfind('%')

    try:
      return (output[:output_end], int(output[output_end + 1:]))
    except ValueError:
      logger.error('exit status of shell command %r missing.', command)
      raise device_errors.AdbShellCommandFailedError(
        command, output, status=None, device_serial=self._device_serial)


  def __eq__(self, other):
    """Consider instances equal if they refer to the same device.

    Args:
      other: The instance to compare equality with.

    Returns:
      True if the instances are considered equal, false otherwise.
    """
    return self._device_serial == str(other)

  def __str__(self):
    """The string representation of an instance.

    Returns:
      The device serial number as a string.
    """
    return self._device_serial

  def __repr__(self):
    return '%s(\'%s\')' % (self.__class__.__name__, self)

  # pylint: disable=unused-argument
  @classmethod
  def IsServerOnline(cls):
    status, output = cmd_helper.GetCmdStatusAndOutput(['pgrep', 'adb'])
    output = [int(x) for x in output.split()]
    logger.info('PIDs for adb found: %r', output)
    return status == 0
  # pylint: enable=unused-argument

  @classmethod
  def KillServer(cls, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES):
    cls._RunAdbCmd(['kill-server'], timeout=timeout, retries=retries)

  @classmethod
  def StartServer(cls, keys=None, timeout=DEFAULT_TIMEOUT,
                  retries=DEFAULT_RETRIES):
    """Starts the ADB server.

    Args:
      keys: (optional) List of local ADB keys to use to auth with devices.
      timeout: (optional) Timeout per try in seconds.
      retries: (optional) Number of retries to attempt.
    """
    additional_env = {}
    if keys:
      additional_env['ADB_VENDOR_KEYS'] = ':'.join(keys)
    # CPU affinity is used to reduce adb instability http://crbug.com/268450
    cls._RunAdbCmd(['start-server'], timeout=timeout, retries=retries,
                   cpu_affinity=0, additional_env=additional_env)

  @classmethod
  def GetDevices(cls, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES):
    """DEPRECATED. Refer to Devices(...) below."""
    # TODO(jbudorick): Remove this function once no more clients are using it.
    return cls.Devices(timeout=timeout, retries=retries)

  @classmethod
  def Devices(cls, desired_state=_READY_STATE, long_list=False,
              persistent_shell=False, timeout=DEFAULT_TIMEOUT,
              retries=DEFAULT_RETRIES):
    """Get the list of active attached devices.

    Args:
      desired_state: If not None, limit the devices returned to only those
        in the given state.
      long_list: Whether to use the long listing format.
      timeout: Timeout per try in seconds.
      retries: Number of retries to attempt.
      persistent_shell: If True, uses a single "adb shell" for running commands.

    Yields:
      AdbWrapper instances.
    """
    lines = cls._RawDevices(long_list=long_list, timeout=timeout,
                            retries=retries)
    if long_list:
      return [
        [AdbWrapper(line[0], persistent_shell=persistent_shell)] + line[1:]
        for line in lines
        if (len(line) >= 2 and (not desired_state or line[1] == desired_state))
      ]
    else:
      return [
        AdbWrapper(line[0], persistent_shell=persistent_shell)
        for line in lines
        if (len(line) == 2 and (not desired_state or line[1] == desired_state))
      ]

  @classmethod
  def _RawDevices(cls, long_list=False, timeout=DEFAULT_TIMEOUT,
                  retries=DEFAULT_RETRIES):
    cmd = ['devices']
    if long_list:
      cmd.append('-l')
    output = cls._RunAdbCmd(cmd, timeout=timeout, retries=retries)
    return [line.split() for line in output.splitlines()[1:]]

  def GetDeviceSerial(self):
    """Gets the device serial number associated with this object.

    Returns:
      Device serial number as a string.
    """
    return self._device_serial

  def Push(self, local, remote, sync=False,
           timeout=60 * 5, retries=DEFAULT_RETRIES):
    """Pushes a file from the host to the device.

    Args:
      local: Path on the host filesystem.
      remote: Path on the device filesystem.
      sync: (optional) Whether to only push files that are newer on the host.
        Not supported when using adb prior to 1.0.39.
      timeout: (optional) Timeout per try in seconds.
      retries: (optional) Number of retries to attempt.

    Raises:
      AdbVersionError if sync=True with versions of adb prior to 1.0.39.
    """
    VerifyLocalFileExists(local)

    if (du_version.LooseVersion(self.Version()) <
        du_version.LooseVersion('1.0.36')):

      # Different versions of adb handle pushing a directory to an existing
      # directory differently.

      # In the version packaged with the M SDK, 1.0.32, the following push:
      #   foo/bar -> /sdcard/foo/bar
      # where bar is an existing directory both on the host and the device
      # results in the contents of bar/ on the host being pushed to bar/ on
      # the device, i.e.
      #   foo/bar/A -> /sdcard/foo/bar/A
      #   foo/bar/B -> /sdcard/foo/bar/B
      #   ... etc.

      # In the version packaged with the N SDK, 1.0.36, the same push under
      # the same conditions results in a second bar/ directory being created
      # underneath the first bar/ directory on the device, i.e.
      #   foo/bar/A -> /sdcard/foo/bar/bar/A
      #   foo/bar/B -> /sdcard/foo/bar/bar/B
      #   ... etc.

      # In order to provide a consistent interface to clients, we check whether
      # the target is an existing directory on the device and, if so, modifies
      # the target passed to adb to emulate the behavior on 1.0.36 and above.

      # Note that this behavior may have started before 1.0.36; that's simply
      # the earliest version we've confirmed thus far.

      try:
        self.Shell('test -d %s' % remote, timeout=timeout, retries=retries)
        remote = posixpath.join(remote, posixpath.basename(local))
      except device_errors.AdbShellCommandFailedError:
        # The target directory doesn't exist on the device, so we can use it
        # without modification.
        pass

    push_cmd = ['push']

    if sync:
      push_cmd += ['--sync']
      if (du_version.LooseVersion(self.Version()) <
          du_version.LooseVersion('1.0.39')):
        # The --sync flag for `adb push` is a relatively recent addition.
        # We're not sure exactly which release first contained it, but it
        # exists at least as far back as 1.0.39.
        raise device_errors.AdbVersionError(
            push_cmd,
            desc='--sync not supported',
            actual_version=self.Version(),
            min_version='1.0.39')

    push_cmd += [local, remote]

    self._RunDeviceAdbCmd(push_cmd, timeout, retries)

  def Pull(self, remote, local, timeout=60 * 5, retries=DEFAULT_RETRIES):
    """Pulls a file from the device to the host.

    Args:
      remote: Path on the device filesystem.
      local: Path on the host filesystem.
      timeout: (optional) Timeout per try in seconds.
      retries: (optional) Number of retries to attempt.
    """
    cmd = ['pull', remote, local]
    self._RunDeviceAdbCmd(cmd, timeout, retries)
    try:
      VerifyLocalFileExists(local)
    except IOError:
      raise device_errors.AdbCommandFailedError(
          cmd,
          'File pulled from the device did not arrive on the host: %s' % local,
          device_serial=str(self))

  def StartShell(self, cmd):
    """Starts a subprocess on the device and returns a handle to the process.

    Args:
      args: A sequence of program arguments. The executable to run is the first
        item in the sequence.

    Returns:
      An instance of subprocess.Popen associated with the live process.
    """
    return cmd_helper.StartCmd(
        self._BuildAdbCmd(['shell'] + cmd, self._device_serial))

  def Shell(self, command, expect_status=0, timeme=False, timeout=DEFAULT_TIMEOUT,
            retries=DEFAULT_RETRIES):
    """Runs a shell command on the device.

    Args:
      command: A string with the shell command to run.
      expect_status: (optional) Check that the command's exit status matches
        this value. Default is 0. If set to None the test is skipped.
      timeout: (optional) Timeout per try in seconds.
      retries: (optional) Number of retries to attempt.

    Returns:
      The output of the shell command as a string.

    Raises:
      device_errors.AdbCommandFailedError: If the exit status doesn't match
        |expect_status|.
    """
    if self._persistent_shell:
      output, status = self._persistent_shell.RunCommand(command, keepends=True, timeme=timeme)
      output = ''.join(output).rstrip()

    else:
      output, status = self._Shell(command, timeout, retries)

    if expect_status is not None and status != expect_status:
      raise device_errors.AdbShellCommandFailedError(
          command, output, status=status, device_serial=self._device_serial)
    return output

  def IterShell(self, command, timeout):
    """Runs a shell command and returns an iterator over its output lines.

    The output lines are returned while the comman is still running.

    Args:
      command: A string with the shell command to run.
      timeout: Timeout in seconds.

    Yields:
      The output of the command line by line.
    """
    if self._persistent_shell:
      return self._persistent_shell.IterRunCommand(command, False)
    else:
      args = ['shell', command]
      return cmd_helper.IterCmdOutputLines(
        self._BuildAdbCmd(args, self._device_serial), timeout=timeout,
        env=self._ADB_ENV)

  def Ls(self, path, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES):
    """List the contents of a directory on the device.

    Args:
      path: Path on the device filesystem.
      timeout: (optional) Timeout per try in seconds.
      retries: (optional) Number of retries to attempt.

    Returns:
      A list of pairs (filename, stat) for each file found in the directory,
      where the stat object has the properties: st_mode, st_size, and st_time.

    Raises:
      AdbCommandFailedError if |path| does not specify a valid and accessible
          directory in the device, or the output of "adb ls" command is less
          than four columns
    """
    def ParseLine(line, cmd):
      cols = line.split(None, 3)
      if len(cols) < 4:
        raise device_errors.AdbCommandFailedError(
            cmd, line, "the output should be 4 columns, but is only %d columns"
            % len(cols), device_serial=self._device_serial)
      filename = cols.pop()
      stat = DeviceStat(*[int(num, base=16) for num in cols])
      return (filename, stat)

    cmd = ['ls', path]
    lines = self._RunDeviceAdbCmd(
        cmd, timeout=timeout, retries=retries).splitlines()
    if lines:
      return [ParseLine(line, cmd) for line in lines]
    else:
      raise device_errors.AdbCommandFailedError(
          cmd, 'path does not specify an accessible directory in the device',
          device_serial=self._device_serial)

  def Logcat(self, clear=False, dump=False, filter_specs=None,
             logcat_format=None, ring_buffer=None, iter_timeout=None,
             check_error=True, timeout=None, retries=DEFAULT_RETRIES):
    """Get an iterable over the logcat output.

    Args:
      clear: If true, clear the logcat.
      dump: If true, dump the current logcat contents.
      filter_specs: If set, a list of specs to filter the logcat.
      logcat_format: If set, the format in which the logcat should be output.
        Options include "brief", "process", "tag", "thread", "raw", "time",
        "threadtime", and "long"
      ring_buffer: If set, a list of alternate ring buffers to request.
        Options include "main", "system", "radio", "events", "crash" or "all".
        The default is equivalent to ["main", "system", "crash"].
      iter_timeout: If set and neither clear nor dump is set, the number of
        seconds to wait between iterations. If no line is found before the
        given number of seconds elapses, the iterable will yield None.
      check_error: Whether to check the exit status of the logcat command.
      timeout: (optional) If set, timeout per try in seconds. If clear or dump
        is set, defaults to DEFAULT_TIMEOUT.
      retries: (optional) If clear or dump is set, the number of retries to
        attempt. Otherwise, does nothing.

    Yields:
      logcat output line by line.
    """
    cmd = ['logcat']
    use_iter = True
    if clear:
      cmd.append('-c')
      use_iter = False
    if dump:
      cmd.append('-d')
      use_iter = False
    if logcat_format:
      cmd.extend(['-v', logcat_format])
    if ring_buffer:
      for buffer_name in ring_buffer:
        cmd.extend(['-b', buffer_name])
    if filter_specs:
      cmd.extend(filter_specs)

    if use_iter:
      return self._IterRunDeviceAdbCmd(
          cmd, iter_timeout, timeout, check_error=check_error)
    else:
      timeout = timeout if timeout is not None else DEFAULT_TIMEOUT
      output = self._RunDeviceAdbCmd(
          cmd, timeout, retries, check_error=check_error)
      return output.splitlines()

  def Forward(self, local, remote, allow_rebind=False,
              timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES):
    """Forward socket connections from the local socket to the remote socket.

    Sockets are specified by one of:
      tcp:<port>
      localabstract:<unix domain socket name>
      localreserved:<unix domain socket name>
      localfilesystem:<unix domain socket name>
      dev:<character device name>
      jdwp:<process pid> (remote only)

    Args:
      local: The host socket.
      remote: The device socket.
      allow_rebind: A boolean indicating whether adb may rebind a local socket;
        otherwise, the default, an exception is raised if the local socket is
        already being forwarded.
      timeout: (optional) Timeout per try in seconds.
      retries: (optional) Number of retries to attempt.
    """
    cmd = ['forward']
    if not allow_rebind:
      cmd.append('--no-rebind')
    cmd.extend([str(local), str(remote)])
    output = self._RunDeviceAdbCmd(cmd, timeout, retries).strip()
    if output:
      logger.warning('Unexpected output from "adb forward": %s', output)

  def ForwardRemove(self, local, timeout=DEFAULT_TIMEOUT,
                    retries=DEFAULT_RETRIES):
    """Remove a forward socket connection.

    Args:
      local: The host socket.
      timeout: (optional) Timeout per try in seconds.
      retries: (optional) Number of retries to attempt.
    """
    self._RunDeviceAdbCmd(['forward', '--remove', str(local)], timeout,
                          retries)

  def ForwardList(self, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES):
    """List all currently forwarded socket connections.

    Args:
      timeout: (optional) Timeout per try in seconds.
      retries: (optional) Number of retries to attempt.
    Returns:
      The output of adb forward --list as a string.
    """
    if (du_version.LooseVersion(self.Version()) >=
        du_version.LooseVersion('1.0.36')):
      # Starting in 1.0.36, this can occasionally fail with a protocol fault.
      # As this interrupts all connections with all devices, we instead just
      # return an empty list. This may give clients an inaccurate result, but
      # that's usually better than crashing the adb server.

      # TODO(jbudorick): Determine an appropriate upper version bound for this
      # once b/31811775 is fixed.
      return ''

    return self._RunDeviceAdbCmd(['forward', '--list'], timeout, retries)

  def JDWP(self, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES):
    """List of PIDs of processes hosting a JDWP transport.

    Args:
      timeout: (optional) Timeout per try in seconds.
      retries: (optional) Number of retries to attempt.

    Returns:
      A list of PIDs as strings.
    """
    return [a.strip() for a in
            self._RunDeviceAdbCmd(['jdwp'], timeout, retries).split('\n')]

  def Install(self, apk_path, forward_lock=False, allow_downgrade=False,
              reinstall=False, sd_card=False, timeout=60 * 2,
              retries=DEFAULT_RETRIES):
    """Install an apk on the device.

    Args:
      apk_path: Host path to the APK file.
      forward_lock: (optional) If set forward-locks the app.
      allow_downgrade: (optional) If set, allows for downgrades.
      reinstall: (optional) If set reinstalls the app, keeping its data.
      sd_card: (optional) If set installs on the SD card.
      timeout: (optional) Timeout per try in seconds.
      retries: (optional) Number of retries to attempt.
    """
    VerifyLocalFileExists(apk_path)
    cmd = ['install']
    if forward_lock:
      cmd.append('-l')
    if reinstall:
      cmd.append('-r')
    if sd_card:
      cmd.append('-s')
    if allow_downgrade:
      cmd.append('-d')
    cmd.append(apk_path)
    output = self._RunDeviceAdbCmd(cmd, timeout, retries)
    if 'Success' not in output:
      raise device_errors.AdbCommandFailedError(
          cmd, output, device_serial=self._device_serial)

  def InstallMultiple(self, apk_paths, forward_lock=False, reinstall=False,
                      sd_card=False, allow_downgrade=False, partial=False,
                      timeout=60 * 2, retries=DEFAULT_RETRIES):
    """Install an apk with splits on the device.

    Args:
      apk_paths: Host path to the APK file.
      forward_lock: (optional) If set forward-locks the app.
      reinstall: (optional) If set reinstalls the app, keeping its data.
      sd_card: (optional) If set installs on the SD card.
      allow_downgrade: (optional) Allow versionCode downgrade.
      partial: (optional) Package ID if apk_paths doesn't include all .apks.
      timeout: (optional) Timeout per try in seconds.
      retries: (optional) Number of retries to attempt.
    """
    for path in apk_paths:
      VerifyLocalFileExists(path)
    cmd = ['install-multiple']
    if forward_lock:
      cmd.append('-l')
    if reinstall:
      cmd.append('-r')
    if sd_card:
      cmd.append('-s')
    if allow_downgrade:
      cmd.append('-d')
    if partial:
      cmd.extend(('-p', partial))
    cmd.extend(apk_paths)
    output = self._RunDeviceAdbCmd(cmd, timeout, retries)
    if 'Success' not in output:
      raise device_errors.AdbCommandFailedError(
          cmd, output, device_serial=self._device_serial)

  def Uninstall(self, package, keep_data=False, timeout=DEFAULT_TIMEOUT,
                retries=DEFAULT_RETRIES):
    """Remove the app |package| from the device.

    Args:
      package: The package to uninstall.
      keep_data: (optional) If set keep the data and cache directories.
      timeout: (optional) Timeout per try in seconds.
      retries: (optional) Number of retries to attempt.
    """
    cmd = ['uninstall']
    if keep_data:
      cmd.append('-k')
    cmd.append(package)
    output = self._RunDeviceAdbCmd(cmd, timeout, retries)
    if 'Failure' in output or 'Exception' in output:
      raise device_errors.AdbCommandFailedError(
          cmd, output, device_serial=self._device_serial)

  def Backup(self, path, packages=None, apk=False, shared=False,
             nosystem=True, include_all=False, timeout=DEFAULT_TIMEOUT,
             retries=DEFAULT_RETRIES):
    """Write an archive of the device's data to |path|.

    Args:
      path: Local path to store the backup file.
      packages: List of to packages to be backed up.
      apk: (optional) If set include the .apk files in the archive.
      shared: (optional) If set buckup the device's SD card.
      nosystem: (optional) If set exclude system applications.
      include_all: (optional) If set back up all installed applications and
        |packages| is optional.
      timeout: (optional) Timeout per try in seconds.
      retries: (optional) Number of retries to attempt.
    """
    cmd = ['backup', '-f', path]
    if apk:
      cmd.append('-apk')
    if shared:
      cmd.append('-shared')
    if nosystem:
      cmd.append('-nosystem')
    if include_all:
      cmd.append('-all')
    if packages:
      cmd.extend(packages)
    assert bool(packages) ^ bool(include_all), (
        'Provide \'packages\' or set \'include_all\' but not both.')
    ret = self._RunDeviceAdbCmd(cmd, timeout, retries)
    VerifyLocalFileExists(path)
    return ret

  def Restore(self, path, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES):
    """Restore device contents from the backup archive.

    Args:
      path: Host path to the backup archive.
      timeout: (optional) Timeout per try in seconds.
      retries: (optional) Number of retries to attempt.
    """
    VerifyLocalFileExists(path)
    self._RunDeviceAdbCmd(['restore'] + [path], timeout, retries)

  def WaitForDevice(self, timeout=60 * 5, retries=DEFAULT_RETRIES):
    """Block until the device is online.

    Args:
      timeout: (optional) Timeout per try in seconds.
      retries: (optional) Number of retries to attempt.
    """
    self._RunDeviceAdbCmd(['wait-for-device'], timeout, retries)

  def GetState(self, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES):
    """Get device state.

    Args:
      timeout: (optional) Timeout per try in seconds.
      retries: (optional) Number of retries to attempt.

    Returns:
      One of 'offline', 'bootloader', or 'device'.
    """
    # TODO(jbudorick): Revert to using get-state once it doesn't cause a
    # a protocol fault.
    # return self._RunDeviceAdbCmd(['get-state'], timeout, retries).strip()

    lines = self._RawDevices(timeout=timeout, retries=retries)
    for line in lines:
      if len(line) >= 2 and line[0] == self._device_serial:
        return line[1]
    return 'offline'

  def GetDevPath(self, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES):
    """Gets the device path.

    Args:
      timeout: (optional) Timeout per try in seconds.
      retries: (optional) Number of retries to attempt.

    Returns:
      The device path (e.g. usb:3-4)
    """
    return self._RunDeviceAdbCmd(['get-devpath'], timeout, retries)

  def Remount(self, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES):
    """Remounts the /system partition on the device read-write."""
    self._RunDeviceAdbCmd(['remount'], timeout, retries)

  def Reboot(self, to_bootloader=False, timeout=60 * 5,
             retries=DEFAULT_RETRIES):
    """Reboots the device.

    Args:
      to_bootloader: (optional) If set reboots to the bootloader.
      timeout: (optional) Timeout per try in seconds.
      retries: (optional) Number of retries to attempt.
    """
    if to_bootloader:
      cmd = ['reboot-bootloader']
    else:
      cmd = ['reboot']
    self._RunDeviceAdbCmd(cmd, timeout, retries)

  def Root(self, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES):
    """Restarts the adbd daemon with root permissions, if possible.

    Args:
      timeout: (optional) Timeout per try in seconds.
      retries: (optional) Number of retries to attempt.
    """
    output = self._RunDeviceAdbCmd(['root'], timeout, retries)
    if 'cannot' in output:
      raise device_errors.AdbCommandFailedError(
          ['root'], output, device_serial=self._device_serial)

  def Emu(self, cmd, timeout=DEFAULT_TIMEOUT,
               retries=DEFAULT_RETRIES):
    """Runs an emulator console command.

    See http://developer.android.com/tools/devices/emulator.html#console

    Args:
      cmd: The command to run on the emulator console.
      timeout: (optional) Timeout per try in seconds.
      retries: (optional) Number of retries to attempt.

    Returns:
      The output of the emulator console command.
    """
    if isinstance(cmd, basestring):
      cmd = [cmd]
    return self._RunDeviceAdbCmd(['emu'] + cmd, timeout, retries)

  def DisableVerity(self, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES):
    """Disable Marshmallow's Verity security feature.

    Returns:
      The output of the disable-verity command as a string.
    """
    output = self._RunDeviceAdbCmd(['disable-verity'], timeout, retries)
    if output and not _VERITY_DISABLE_RE.search(output):
      raise device_errors.AdbCommandFailedError(
          ['disable-verity'], output, device_serial=self._device_serial)
    return output

  def EnableVerity(self, timeout=DEFAULT_TIMEOUT, retries=DEFAULT_RETRIES):
    """Enable Marshmallow's Verity security feature.

    Returns:
      The output of the enable-verity command as a string.
    """
    output = self._RunDeviceAdbCmd(['enable-verity'], timeout, retries)
    if output and not _VERITY_ENABLE_RE.search(output):
      raise device_errors.AdbCommandFailedError(
          ['enable-verity'], output, device_serial=self._device_serial)
    return output

  @property
  def _persistent_shell(self):
    if self._persistent_shell_instance is not None:
      self._persistent_shell_instance.EnsureStarted()
    return self._persistent_shell_instance

  @property
  def is_emulator(self):
    return _EMULATOR_RE.match(self._device_serial)

  @property
  def is_ready(self):
    try:
      return self.GetState() == _READY_STATE
    except device_errors.CommandFailedError:
      return False
