# Copyright 2022 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import
import builtins
import io
import os
import shutil
import subprocess
import tempfile
import time
import unittest
import mock

from telemetry.core import linux_based_interface
from telemetry.testing import options_for_unittests
from telemetry.util import cmd_util


class LinuxBasedInterfaceHelperMethodsTest(unittest.TestCase):

  @mock.patch.object(cmd_util, 'GetAllCmdOutput')
  def testGetAllCmdOutputCallsAndDecodes(self, mock_get_output):
    mock_stdout = mock.create_autospec(bytes, instance=True)
    mock_stdout.decode.return_value = 'decoded stdout'
    mock_stderr = mock.create_autospec(bytes, instance=True)
    mock_stderr.decode.return_value = 'decoded stderr'
    mock_get_output.return_value = (mock_stdout, mock_stderr)

    stdout, stderr = linux_based_interface.GetAllCmdOutput(['forward', 'me'])

    self.assertEqual(stdout, 'decoded stdout')
    self.assertEqual(stderr, 'decoded stderr')

    mock_stdout.decode.assert_called_once_with('utf-8')
    mock_stderr.decode.assert_called_once_with('utf-8')

    mock_get_output.assert_called_once_with(['forward', 'me'], None, False)

    mock_get_output.reset_mock()
    linux_based_interface.GetAllCmdOutput(['forward', 'me'],
                                          quiet=True,
                                          cwd='some/dir')
    mock_get_output.assert_called_once_with(['forward', 'me'], 'some/dir', True)

  @mock.patch.object(cmd_util, 'StartCmd')
  def testStartCmdForwardsArgs(self, mock_start):
    ret = mock.Mock()
    mock_start.return_value = ret

    self.assertEqual(linux_based_interface.StartCmd('cmd'), ret)

    mock_start.assert_called_once_with('cmd', None, False)

    mock_start.reset_mock()
    self.assertEqual(
        linux_based_interface.StartCmd(
            'another cmd', quiet=True, cwd='some/other/dir'), ret)
    mock_start.assert_called_once_with('another cmd', 'some/other/dir', True)

  def testUnquoteRemovesExternalQuotes(self):
    # For some reason, this use-case is supported.
    self.assertEqual(linux_based_interface._Unquote(0), 0)
    self.assertEqual(linux_based_interface._Unquote({}), {})
    self.assertEqual(linux_based_interface._Unquote([]), [])

    self.assertEqual(linux_based_interface._Unquote("'foo\""), "foo")
    self.assertEqual(linux_based_interface._Unquote('foo"""""'), "foo")
    self.assertEqual(linux_based_interface._Unquote("'''''''foo'\"'"), "foo")

    # This will even work for alternating quotes, no matter how many.
    self.assertEqual(linux_based_interface._Unquote("'\"'\"'\"foo'\"'"), "foo")


class LinuxBasedInterfaceTest(unittest.TestCase):

  def _GetLBI(self, remote=None, remote_ssh_port=None, ssh_identity=None):
    # TODO(crbug.com/1344930): Rename these flags.
    remote = remote or options_for_unittests.GetCopy().cros_remote
    remote_ssh_port = remote_ssh_port or options_for_unittests.GetCopy(
    ).cros_remote_ssh_port
    ssh_identity = ssh_identity or options_for_unittests.GetCopy(
    ).cros_ssh_identity

    return linux_based_interface.LinuxBasedInterface(remote, remote_ssh_port,
                                                     ssh_identity)

  def _GetLocalLBI(self):
    return linux_based_interface.LinuxBasedInterface()

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  def testLocal(self, unused_mock):
    with self._GetLocalLBI() as lbi:
      self.assertTrue(lbi.local)
      self.assertIsNone(lbi.hostname)

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  def testLocalIsFalseIfHostname(self, unused_mock):
    with self._GetLBI(remote='some address') as lbi:
      self.assertFalse(lbi.local)
      self.assertEqual(lbi.hostname, 'some address')

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  def testCallsOpenConnectionOnInitRemote(self, mock_open):
    with self._GetLBI(remote='address'):
      mock_open.assert_called_once_with()

  @mock.patch.object(subprocess, 'call')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'FormSSHCommandLine')
  def testOpenConnection(self, mock_call, mock_form_ssh):
    with self._GetLocalLBI() as lbi:
      # Check that local will return immediately.
      self.assertTrue(lbi.local)
      lbi.OpenConnection()
      self.assertEqual(mock_call.call_count, 0)
      self.assertEqual(mock_form_ssh.call_count, 0)

    mock_call.reset_mock()
    mock_form_ssh.reset_mock()

    # Test remote case calls OpenConnection on start.
    with self._GetLBI(remote='address') as lbi:
      mock_form_ssh.assert_called_once()
      mock_call.assert_called_once()

      self.assertTrue(lbi._master_connection_open)

      # Assert no duplicate calls if already open.
      lbi.OpenConnection()
      self.assertEqual(mock_form_ssh.call_count, 1)
      self.assertEqual(mock_call.call_count, 1)

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  def testFormSSHCommandLineLocal(self, unused_mock):
    with self._GetLocalLBI() as lbi:
      self.assertEqual(
          lbi.FormSSHCommandLine(['some', 'args']), ['sh', '-c', 'some args'])

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  def testFormSSHCommandLineRemote(self, unused_conn):
    with self._GetLBI(remote='address') as lbi:
      lbi._DEFAULT_SSH_CONNECTION_TIMEOUT = 42
      lbi._DEFAULT_SSH_COMMAND = ['fizz', 'buzz']
      lbi._ssh_args = ['-o SomeOptions', '-o ToAdd']
      lbi._ssh_control_file = 'some_file'
      lbi._ssh_port = 8222
      lbi._ssh_identity = 'foo-bar'

      result = lbi.FormSSHCommandLine(['some', 'args'])
      formed = ' '.join(result)

      # Ensure the correct components are present
      # SSH command
      self.assertIn('fizz buzz', formed)
      # Default timeout
      self.assertIn('-o ConnectTimeout=42', formed)
      # Control file (if no port-forwarding)
      self.assertIn('-S some_file', formed)
      # SSH Args.
      self.assertIn('-o SomeOptions -o ToAdd', formed)
      # Check root and SSH port
      self.assertIn('root@address', formed)
      self.assertIn('-p8222', formed)
      # SSH Identity
      self.assertIn('-i foo-bar', formed)
      # args given.
      self.assertIn('some args', formed)

      # Timeout override, extra_args, and port_forward
      result = lbi.FormSSHCommandLine(
          ['some', 'args'],
          connect_timeout=57,
          port_forward=True,
          extra_ssh_args=['additional', 'ssh', 'args'])
      formed = ' '.join(result)
      # Default timeout
      self.assertIn('-o ConnectTimeout=57', formed)
      # Control file not present if  port-forwarding
      self.assertNotIn('-S some_file', formed)
      # extra args given.
      self.assertIn('additional ssh args', formed)

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  def testRemoveSSHWarnings(self, unused_mock):
    with self._GetLBI() as lbi:
      filter_string = ('Warning: Permanently added something to '
                       'the list of known hosts.\n\n')
      test_string = filter_string + 'Output from some command'

      self.assertEqual(
          lbi._RemoveSSHWarnings(test_string), 'Output from some command')

      test_string = filter_string.replace(
          'something', 'another address with whitespace') + 'foo'
      self.assertEqual(lbi._RemoveSSHWarnings(test_string), 'foo')

      # Does not remove.
      test_string = filter_string.replace('something to', 'something') + 'foo'
      self.assertEqual(lbi._RemoveSSHWarnings(test_string), test_string)

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'FormSSHCommandLine')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     '_RemoveSSHWarnings')
  @mock.patch.object(linux_based_interface, 'GetAllCmdOutput')
  def testRunCmdOnDeviceUsesArgsCorrectly(self, mock_get_output,
                                          mock_remove_warnings, mock_form_ssh,
                                          unused_mock):
    with self._GetLBI() as lbi:
      mock_form_ssh.return_value = ['some', 'args']
      mock_get_output.return_value = ('stdout', 'stderr')
      mock_remove_warnings.return_value = 'filtered stderr'

      stdout, stderr = lbi.RunCmdOnDevice(['additional', 'args'],
                                          cwd='/some/dir',
                                          quiet=True,
                                          connect_timeout=57,
                                          port_forward=True)
      self.assertEqual(stdout, 'stdout')
      self.assertEqual(stderr, 'filtered stderr')

      mock_form_ssh.assert_called_once_with(['additional', 'args'],
                                            connect_timeout=57,
                                            port_forward=True)
      mock_get_output.assert_called_once_with(['some', 'args'],
                                              cwd='/some/dir',
                                              quiet=True)
      mock_remove_warnings.asset_called_once_with('stderr')

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'RunCmdOnDevice')
  def testTryLoginRunsEcho(self, mock_run_cmd, unused_mock):
    with self._GetLBI(remote='address') as lbi:
      lbi._REMOTE_USER = 'foo_user'
      mock_run_cmd.return_value = ('foo_user\n', '')
      lbi.TryLogin()

      mock_run_cmd.assert_called_once_with(['echo', '$USER'],
                                           quiet=mock.ANY,
                                           connect_timeout=mock.ANY)

      mock_run_cmd.return_value = 'bad user', ''
      self.assertRaises(linux_based_interface.LoginException, lbi.TryLogin)

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'RunCmdOnDevice')
  def testTryLoginErrors(self, mock_run_cmd, unused_mock):
    with self._GetLBI(remote='address') as lbi:
      mock_run_cmd.return_value = ('', 'random error')

      self.assertRaisesRegex(linux_based_interface.LoginException,
                             'logging into address, got random error',
                             lbi.TryLogin)

      mock_run_cmd.return_value = ('', lbi._HOST_KEY_ERROR)
      self.assertRaisesRegex(linux_based_interface.LoginException,
                             'address host key verification failed',
                             lbi.TryLogin)
      mock_run_cmd.return_value = ('', lbi._TIMEOUT_ERROR)
      self.assertRaisesRegex(linux_based_interface.LoginException,
                             '[tT]imed out', lbi.TryLogin)
      mock_run_cmd.return_value = ('', lbi._PRIV_KEY_PROTECTIONS_ERROR)
      self.assertRaisesRegex(linux_based_interface.LoginException,
                             '[pP]ermissions.*are too open', lbi.TryLogin)
      mock_run_cmd.return_value = ('', lbi._SSH_AUTH_ERROR)
      self.assertRaisesRegex(linux_based_interface.LoginException,
                             '[nN]eed to set up ssh auth', lbi.TryLogin)
      mock_run_cmd.return_value = ('', lbi._HOSTNAME_RESOLUTION_ERROR)
      self.assertRaisesRegex(linux_based_interface.DNSFailureException,
                             '[uU]nable to resolve the hostname for: address',
                             lbi.TryLogin)

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'RunCmdOnDevice')
  def testFileExistsOnDevice(self, mock_run_cmd, unused_mock):
    with self._GetLBI(remote='address') as lbi:
      mock_run_cmd.return_value = ('1\n', '')
      self.assertTrue(lbi.FileExistsOnDevice('foo'))

      # Check that file existence is called.
      self.assertIn('test -e foo', ' '.join(mock_run_cmd.call_args[0][0]))

      # Check bad stdout returns False.
      mock_run_cmd.return_value = ('', '')
      self.assertFalse(lbi.FileExistsOnDevice('foo'))

      # Check that errors are raised if stderr.
      mock_run_cmd.return_value = ('1\n', 'some stderr boohoo')
      self.assertRaisesRegex(OSError, '[uU]nexpected error: some stderr boohoo',
                             lbi.FileExistsOnDevice, 'foo')

      # Specific failure case.
      mock_run_cmd.return_value = ('1\n', 'Connection timed out')
      self.assertRaisesRegex(OSError, 'wasn\'t responding to ssh',
                             lbi.FileExistsOnDevice, 'foo')

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  @mock.patch.object(linux_based_interface, 'GetAllCmdOutput')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     '_FormSCPToRemote')
  def testPushFileLocal(self, mock_form_scp, mock_run_cmd, unused_mock):
    with self._GetLocalLBI() as lbi:
      self.assertTrue(lbi.local)
      mock_run_cmd.return_value = ('no error but who cares about stdout', '')

      lbi.PushFile('foo', 'remote_foo')

      self.assertRegex(' '.join(mock_run_cmd.call_args[0][0]),
                       r'cp.*foo\sremote_foo')
      self.assertEqual(mock_form_scp.call_count, 0)

      mock_run_cmd.return_value = ('error in stderr!', 'stderr')

      self.assertRaises(OSError, lbi.PushFile, 'foo', 'remote_foo')

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  @mock.patch.object(linux_based_interface, 'GetAllCmdOutput')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     '_FormSCPToRemote')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     '_RemoveSSHWarnings')
  @mock.patch.object(os.path, 'abspath')
  def testPushFileRemote(self, mock_abspath, mock_ssh_warnings, mock_form_scp,
                         mock_run_cmd, unused_mock):
    with self._GetLBI(remote='address') as lbi:
      self.assertFalse(lbi.local)
      mock_run_cmd.return_value = ('stdout do not care',
                                   'stderr but will get filtered')
      mock_abspath.return_value = '/some/abs/path/to/foo'
      mock_form_scp.return_value = 'the scp cmd'.split(' ')
      mock_ssh_warnings.return_value = ''

      lbi.PushFile('foo', 'remote_foo')

      # abspath is called in ctor
      mock_abspath.assert_has_calls([mock.call('foo')])
      mock_form_scp.assert_called_once_with(
          '/some/abs/path/to/foo', 'remote_foo', extra_scp_args=mock.ANY)
      mock_run_cmd.assert_called_once_with(
          'the scp cmd'.split(' '), quiet=mock.ANY)
      mock_ssh_warnings.assert_called_once_with('stderr but will get filtered')

      mock_ssh_warnings.return_value = 'error in stderr!'

      self.assertRaises(OSError, lbi.PushFile, 'foo', 'remote_foo')

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface, 'PushFile')
  @mock.patch.object(tempfile, 'NamedTemporaryFile')
  def testPushContents(self, mock_tempfile, mock_push_file, unused_mock):
    with self._GetLocalLBI() as lbi:

      class NamedStringIO(io.StringIO):

        def __init__(self, name):
          super().__init__()
          self.name = name

      output = NamedStringIO(name='the_temp_file_name')

      mock_tempfile.return_value.__enter__.return_value = output

      lbi.PushContents('foo contents', 'remote_file')
      # assert writeable.
      self.assertIn('w', mock_tempfile.call_args[1]['mode'])
      self.assertEqual(output.getvalue(), 'foo contents')
      mock_push_file.assert_called_once_with(output.name, 'remote_file')

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     '_FormSCPFromRemote')
  @mock.patch.object(linux_based_interface, 'GetAllCmdOutput')
  @mock.patch.object(os.path, 'abspath')
  @mock.patch.object(shutil, 'copyfile')
  def testGetFileLocal(self, mock_copyfile, mock_abspath, mock_cmd, mock_scp,
                       unused_mock):
    with self._GetLocalLBI() as lbi:
      self.assertTrue(lbi.local)
      mock_abspath.return_value = '/local/file/abspath'

      lbi.GetFile('remote/file', 'local/file')

      # Ensure there is no SCP'ing in local case.
      self.assertEqual(mock_scp.call_count, 0)
      self.assertEqual(mock_cmd.call_count, 0)

      # Verify copy is called.
      mock_abspath.assert_called_once_with('local/file')
      mock_copyfile.assert_called_once_with('remote/file',
                                            '/local/file/abspath')

      mock_copyfile.reset_mock()
      mock_abspath.reset_mock()

      mock_abspath.return_value = '/identical/file'
      # Assert raises error if identical files calling copy.
      self.assertRaises(OSError, lbi.GetFile, '/identical/file',
                        '/identical/file')

      mock_copyfile.reset_mock()
      mock_abspath.reset_mock()
      mock_abspath.return_value = '/local/file/dir'

      # Copying from one dir to local dir/relative dir should be possible.
      lbi.GetFile('/path/in/other/dir')

      # basename is used to call the abspath.
      mock_abspath.assert_called_once_with('dir')
      mock_copyfile.assert_called_once_with('/path/in/other/dir',
                                            '/local/file/dir')

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     '_FormSCPFromRemote')
  @mock.patch.object(linux_based_interface, 'GetAllCmdOutput')
  @mock.patch.object(os.path, 'abspath')
  @mock.patch.object(shutil, 'copyfile')
  def testGetFileRemote(self, mock_copyfile, mock_abspath, mock_cmd, mock_scp,
                        unused_mock):
    with self._GetLBI(remote='address') as lbi:
      self.assertFalse(lbi.local)
      mock_abspath.return_value = '/local/file/abspath'
      lbi._disable_strict_filenames = False
      mock_scp.return_value = 'some scp command'.split(' ')
      mock_cmd.return_value = ('no stderr', '')

      lbi.GetFile('remote/file', 'local/file')

      # Ensure there is no SCP'ing in local case.
      self.assertEqual(mock_copyfile.call_count, 0)

      mock_scp.assert_called_once_with(
          'remote/file', '/local/file/abspath', extra_scp_args=[])
      mock_cmd.assert_called_once_with(
          'some scp command'.split(' '), quiet=mock.ANY)

      mock_cmd.return_value = ('stderr incoming!', 'stderr')
      self.assertRaises(OSError, lbi.GetFile, 'does it matter', 'at all')

      mock_cmd.reset_mock()
      mock_scp.reset_mock()

      # Check that edge case with filename mismatch is dealt with.
      mock_cmd.side_effect = [('stderr incoming!',
                               'filename does not match request'),
                              ('stderr works!', '')]
      mock_scp.side_effect = [
          'first scp command'.split(' '), 'second scp command'.split(' ')
      ]

      self.assertFalse(lbi._disable_strict_filenames)
      lbi.GetFile('remote/file', 'local/file')
      self.assertTrue(lbi._disable_strict_filenames)

      mock_scp.assert_has_calls([
          mock.call('remote/file', '/local/file/abspath', extra_scp_args=[]),
          mock.call(
              'remote/file', '/local/file/abspath', extra_scp_args=['-T'])
      ])
      mock_cmd.assert_has_calls([
          mock.call('first scp command'.split(' '), quiet=mock.ANY),
          mock.call('second scp command'.split(' '), quiet=mock.ANY),
      ])

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface, 'GetFile')
  @mock.patch.object(tempfile, 'NamedTemporaryFile')
  @mock.patch.object(builtins, 'open')
  def testGetFileContents(self, mock_open, mock_named_temp, mock_getfile,
                          unused_mock):
    with self._GetLBI(remote='address') as lbi:
      some_mock = mock.Mock()
      some_mock.name = 'foo'
      mock_named_temp.return_value.__enter__.return_value = some_mock

      fake_file = io.StringIO('these are file contents')

      mock_open.return_value.__enter__.return_value = fake_file

      self.assertEqual(
          lbi.GetFileContents('path/to/some/file'), 'these are file contents')

      # Check that we got a temp file created
      mock_named_temp.assert_called_once_with(mode='w')
      mock_getfile.assert_called_once_with('path/to/some/file', 'foo')
      # Check that it was opened for reading.
      mock_open.assert_called_once_with('foo', 'r', encoding=mock.ANY)

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'RunCmdOnDevice')
  @mock.patch.object(time, 'time')
  def testGetDeviceHostClockOffset(self, mock_time, mock_run_cmd, unused_mock):
    with self._GetLocalLBI() as lbi:
      self.assertIsNone(lbi._device_host_clock_offset)
      # Device time. Expects string.
      mock_run_cmd.return_value = '1053', 'ignored stderr'

      # Host time.
      mock_time.return_value = 1000

      self.assertEqual(lbi.GetDeviceHostClockOffset(), 53)

      # Offset is now cached.
      self.assertEqual(lbi._device_host_clock_offset, 53)

      # Offset cannot be updated. If it did, the offset would be 0.
      mock_time.return_value = 1053
      self.assertEqual(lbi.GetDeviceHostClockOffset(), 53)

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'RunCmdOnDevice')
  def testHasSystemD(self, mock_cmd, unused_mock):
    with self._GetLocalLBI() as lbi:
      mock_cmd.return_value = 'ignored', ''

      self.assertTrue(lbi.HasSystemd())

      mock_cmd.assert_called_once_with(['systemctl'], quiet=mock.ANY)

      mock_cmd.reset_mock()
      mock_cmd.return_value = 'ignored', 'some error'

      self.assertFalse(lbi.HasSystemd())

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'RunCmdOnDevice')
  def testListProcesses(self, mock_cmd, unused_mock):
    ps_output = """
    1       0 /sbin/init splash               S
    2       0 [kthreadd]                      S
    3       2 [rcu_gp]                        I
    4       2 [rcu_par_gp]                    I
    5       2 [netns]                         I
    7       2 [kworker/0:0H-events_highpri]   I
"""
    expected_procs_parsed = [
        (1, '/sbin/init splash', 0, 'S'),
        (2, '[kthreadd]', 0, 'S'),
        (3, '[rcu_gp]', 2, 'I'),
        (4, '[rcu_par_gp]', 2, 'I'),
        (5, '[netns]', 2, 'I'),
        (7, '[kworker/0:0H-events_highpri]', 2, 'I'),
    ]
    with self._GetLocalLBI() as lbi:
      mock_cmd.return_value = ps_output, ''

      self.assertEqual(lbi.ListProcesses(), expected_procs_parsed)
      self.assertIn('/bin/ps', mock_cmd.call_args[0][0])

      mock_cmd.return_value = ps_output, 'stderr'
      self.assertRaises(AssertionError, lbi.ListProcesses)

      mock_cmd.return_value = ps_output + '\nThis line will cause issues', ''
      self.assertRaises(AssertionError, lbi.ListProcesses)

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'GetChromeProcess')
  def testGetChromePid(self, mock_get_proc, unused_mock):
    with self._GetLocalLBI() as lbi:
      mock_get_proc.return_value = {
          'pid': 42,
          'path': '/path/to/chrome',
          'args': ['some', 'args']
      }

      self.assertEqual(lbi.GetChromePid(), 42)

      mock_get_proc.assert_called_once()

      mock_get_proc.return_value = None
      self.assertIsNone(lbi.GetChromePid())

      mock_get_proc.return_value = {'path': 'a/path', 'args': ['some', 'args']}
      self.assertIsNone(lbi.GetChromePid())

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface, 'ListProcesses')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'RunCmdOnDevice')
  def testKillAllMatching(self, mock_run_cmd, mock_list, unused_mock):
    with self._GetLocalLBI() as lbi:
      mock_list.return_value = [
          (0, 'some cmd', 'unused', 'unused'),
          (1, 'some other cmd', 'unused', 'unused'),
          (2, 'some new cmd', 'unused', 'unused'),
          (3, 'cmd', 'unused', 'unused'),
      ]

      removed = []
      count = 0

      def predicate_kill_every_other(cmd):
        del cmd
        nonlocal count
        if count % 2:
          count += 1
          return True
        count += 1
        return False

      predicate_kill_all = lambda a: True
      predicate_kill_none = lambda a: False

      self.assertEqual(lbi.KillAllMatching(predicate_kill_none), 0)
      self.assertEqual(mock_run_cmd.call_count, 0)

      mock_run_cmd.reset_mock()
      self.assertEqual(lbi.KillAllMatching(predicate_kill_all), 4)
      mock_run_cmd.assert_called_once_with(['kill', '-KILL', 0, 1, 2, 3],
                                           quiet=mock.ANY)

      mock_run_cmd.reset_mock()
      num_kills = lbi.KillAllMatching(predicate_kill_every_other)
      removed = [1, 3]
      self.assertEqual(num_kills, len(removed))
      mock_run_cmd.assert_called_once_with(
          ['kill', '-KILL'] + removed, quiet=mock.ANY)

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'RunCmdOnDevice')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface, 'HasSystemd')
  def testIsServiceRunning(self, mock_systemd, mock_cmd, unused_mock):
    with self._GetLocalLBI() as lbi:
      # Test default case.
      mock_systemd.return_value = False

      self.assertRaisesRegex(AssertionError, 'system does not have systemd',
                             lbi.IsServiceRunning, 'foo-service')

      mock_systemd.assert_called_once_with()
      self.assertEqual(mock_cmd.call_count, 0)
      mock_systemd.reset_mock()

      # Test stderr from cmd will throw error.
      mock_systemd.return_value = True
      mock_cmd.return_value = 'MainPID=0', 'some stderr'
      self.assertRaisesRegex(AssertionError, 'some stderr',
                             lbi.IsServiceRunning, 'foo-service')
      mock_cmd.assert_called_once_with(
          ['systemctl', 'show', '-p', 'MainPID', 'foo-service'], quiet=mock.ANY)

      # Test PID=0 returns false
      mock_cmd.return_value = 'MainPID=0', ''
      self.assertFalse(lbi.IsServiceRunning('foo-service'))

      # Test PID!=0 returns True
      mock_cmd.return_value = 'MainPID=53', ''
      self.assertTrue(lbi.IsServiceRunning('foo-service'))

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'RunCmdOnDevice')
  def testGetRemotePort(self, mock_cmd, unused_mock):
    netstat_output = ("""Active Internet connections (servers and established)
Proto Recv-Q Send-Q Local Address           Foreign Address         State
tcp        0      0 127.0.0.1:19080         0.0.0.0:*               LISTEN
tcp        0      0 127.0.0.2:6697          0.0.0.0:*               LISTEN
tcp        0      0 127.0.0.1:9557          0.0.0.0:*               LISTEN
""", 'ignored stderr')

    with self._GetLocalLBI() as lbi:
      lbi._reserved_ports = []
      mock_cmd.return_value = netstat_output

      # Port given will be largest port in use +1
      # This includes previously reserved ports
      self.assertEqual(lbi.GetRemotePort(), 19081)
      self.assertEqual(lbi._reserved_ports, [19081])
      mock_cmd.assert_called_once_with(['netstat', '-ant'])

      self.assertEqual(lbi.GetRemotePort(), 19082)

      lbi._reserved_ports.append(30000)
      self.assertEqual(lbi.GetRemotePort(), 30001)
      self.assertEqual(lbi._reserved_ports, [19081, 19082, 30000, 30001])

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'RunCmdOnDevice')
  def testIsHTTPServerRunningOnPort(self, mock_cmd, unused_mock):
    with self._GetLocalLBI() as lbi:
      mock_cmd.return_value = 'some stdout from wget', 'Connection refused'

      self.assertFalse(lbi.IsHTTPServerRunningOnPort(5000))

      # Don't care about timeout period being there.
      args = mock_cmd.call_args[0][0]
      self.assertIn('wget', args)
      self.assertIn('localhost:5000', args)

      mock_cmd.reset_mock()
      mock_cmd.return_value = ('Connection somewhere not refused',
                               'Connection NOT refused')

      self.assertTrue(lbi.IsHTTPServerRunningOnPort(8008))

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'RunCmdOnDevice')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface, 'GetFile')
  def testTakeScreenshotFailsIfBadStdout(
      self,
      unused_mock_get_file,
      mock_run_cmd,
      unused_mock,
  ):
    with self._GetLocalLBI() as lbi:
      self.assertTrue(lbi.local)
      mock_run_cmd.side_effect = [
          ('making a directory', ''),
          # This line causes the failure => value!=0
          ('screenshot return value:25', ''),
          ('making a directory', ''),
          ('copying a file', ''),
      ]

      self.assertFalse(lbi.TakeScreenshot('/path/to/foo'))

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'RunCmdOnDevice')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface, 'GetFile')
  def testTakeScreenshotLocallyMakesDirectoryAndCopiesFile(
      self,
      unused_mock_get_file,
      mock_run_cmd,
      unused_mock,
  ):
    with self._GetLocalLBI() as lbi:
      self.assertTrue(lbi.local)
      mock_run_cmd.side_effect = [
          ('making a directory', ''),
          ('screenshot return value:0', ''),
          ('making a directory', ''),
          ('copying a file', ''),
      ]

      self.assertTrue(lbi.TakeScreenshot('/path/to/foo'))

      mock_run_cmd.assert_has_calls([
          mock.call('mkdir -p /var/log/screenshots'.split(' ')),
          mock.call((lbi._SCREENSHOT_BINARY +
                     ' /var/log/screenshots/foo && echo').split(' ') +
                    ['screenshot return value:$?']),
          mock.call('mkdir -p /path/to'.split(' ')),
          mock.call('cp /var/log/screenshots/foo /path/to/foo'.split(' '))
      ])

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'RunCmdOnDevice')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface, 'GetFile')
  @mock.patch.object(os.path, 'exists')
  @mock.patch.object(os, 'makedirs')
  def testTakeScreenshotRemoteMakesDirectoryAndCopiesFile(
      self, mock_mkdirs, mock_exists, mock_get_file, mock_run_cmd, unused_mock):
    for dir_exists_case in [True, False]:
      with self.subTest(dir_exists=dir_exists_case):
        with self._GetLBI(remote='address') as lbi:
          self.assertFalse(lbi.local)
          mock_run_cmd.side_effect = [
              ('making a directory', ''),
              ('screenshot return value:0', ''),
          ]
          mock_exists.return_value = dir_exists_case

          self.assertTrue(lbi.TakeScreenshot('/path/to/foo'))

          mock_run_cmd.assert_has_calls([
              mock.call('mkdir -p /var/log/screenshots'.split(' ')),
              mock.call((lbi._SCREENSHOT_BINARY +
                         ' /var/log/screenshots/foo && echo').split(' ') +
                        ['screenshot return value:$?']),
          ])
          # Check that it created the directory if it didn't exist.
          mock_exists.assert_called_once_with('/path/to')
          if dir_exists_case:
            mock_mkdirs.assert_not_called()
          else:
            mock_mkdirs.assert_called_once_with('/path/to')
          mock_get_file.assert_called_once_with('/var/log/screenshots/foo',
                                                '/path/to/foo')

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'RunCmdOnDevice')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface, 'GetFile')
  @mock.patch.object(os.path, 'exists')
  @mock.patch.object(os, 'makedirs')
  def testTakeScreenshotRemoteWithErrorLogsIt(self, unused_mkdirs, mock_exists,
                                              unused_get_file, mock_run_cmd,
                                              unused_mock):
    with self._GetLBI(remote='address') as lbi:
      self.assertFalse(lbi.local)
      mock_run_cmd.side_effect = [
          ('making a directory', ''),
          ('screenshot return value:0', ''),
      ]
      mock_exists.side_effect = OSError
      with self.assertLogs(level='ERROR') as log:
        lbi.TakeScreenshot('/some/path')
        self.assertIn(('Unable to pull screenshot file '
                       '/var/log/screenshots/path to /some/path'),
                      log.output[0])

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'TakeScreenshot')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'RunCmdOnDevice')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'FileExistsOnDevice')
  def testTakeScreenshotWithPrefixSucceeds(self, mock_file_exists, mock_run_cmd,
                                           mock_screenshot, unused_mock):
    with self._GetLocalLBI() as lbi:
      mock_file_exists.return_value = False

      self.assertTrue(lbi.TakeScreenshotWithPrefix('test-prefix'))

      screenshot_file = '/tmp/telemetry/screenshots/test-prefix-0.png'
      mock_file_exists.assert_called_once_with(screenshot_file)
      mock_screenshot.assert_called_once_with(screenshot_file)
      mock_run_cmd.assert_called_once_with(
          ['mkdir', '-p', '/tmp/telemetry/screenshots/'])

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'TakeScreenshot')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'RunCmdOnDevice')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'FileExistsOnDevice')
  def testTakeScreenshotWithPrefixFailsIfFull(self, mock_file_exists,
                                              mock_run_cmd, mock_screenshot,
                                              unused_mock):
    with self._GetLocalLBI() as lbi:
      # Simulate as if there were too many screenshots.
      mock_file_exists.side_effect = [True, True]

      self.assertFalse(lbi.TakeScreenshotWithPrefix('test-prefix'))

      mock_run_cmd.assert_called_once_with(
          ['mkdir', '-p', '/tmp/telemetry/screenshots/'])

      # Assert there were no screenshots - disc is "full"
      self.assertEqual(mock_screenshot.call_count, 0)

      screenshot_file = '/tmp/telemetry/screenshots/test-prefix-%d.png'
      mock_file_exists.assert_has_calls(
          [mock.call(screenshot_file % 0),
           mock.call(screenshot_file % 1)])

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'RunCmdOnDevice')
  def testGetArchName(self, mock_cmd, unused_mock):
    with self._GetLocalLBI() as lbi:
      mock_cmd.return_value = 'foo-arch\n', 'ignored stderr'
      self.assertEqual(lbi.GetArchName(), 'foo-arch')
      mock_cmd.assert_called_once_with(['uname', '-m'])

      # Check that its cached.
      self.assertIsNotNone(lbi._arch_name)
      mock_cmd.return_value = 'buzz-arch\n', 'ignored stderr'
      self.assertEqual(lbi.GetArchName(), 'foo-arch')
      mock_cmd.assert_called_once_with(['uname', '-m'])

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'GetFileContents')
  def testLsbReleaseValue(self, mock_contents, unused_mock):
    example_contents = """DISTRIB_CODENAME=buzzian
DISTRIB_DESCRIPTION="Debian GNU/Linux buzzian"
DISTRIB_ID=Debian
DISTRIB_RELEASE=buzzian
ANOTHER_PROPERTY=foobuntu
"""
    with self._GetLocalLBI() as lbi:
      mock_contents.return_value = example_contents
      self.assertEqual(
          lbi.LsbReleaseValue('DISTRIB_DESCRIPTION', 'default'),
          '"Debian GNU/Linux buzzian"')
      mock_contents.assert_called_once_with('/etc/lsb-release')
      self.assertEqual(
          lbi.LsbReleaseValue('DISTRIB_CODENAME', 'default'), 'buzzian')
      self.assertEqual(lbi.LsbReleaseValue('DISTRIB_ID', 'default'), 'Debian')
      self.assertEqual(
          lbi.LsbReleaseValue('DISTRIB_RELEASE', 'default'), 'buzzian')
      self.assertEqual(
          lbi.LsbReleaseValue('ANOTHER_PROPERTY', 'default'), 'foobuntu')
      self.assertEqual(
          lbi.LsbReleaseValue('DNE_PROPERTY', 'default'), 'default')

  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'OpenConnection')
  @mock.patch.object(linux_based_interface.LinuxBasedInterface,
                     'CloseConnection')
  def testOpenAndCloseAreCalled(self, mock_close, mock_open):
    with self._GetLBI(remote='address'):
      mock_open.assert_called_once_with()
      self.assertEqual(mock_close.call_count, 0)

    mock_open.assert_called_once_with()
    mock_close.assert_called_once_with()
