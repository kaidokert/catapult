#!/usr/bin/env python
# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import unittest

from devil import devil_env
from devil.android import device_errors
from devil.android import file_hasher

with devil_env.SysPath(devil_env.PYMOCK_PATH):
  import mock  # pylint: disable=import-error

TEST_OUT_DIR = os.path.join('test', 'out', 'directory')
HOST_FILE_HASHER_EXECUTABLE = os.path.join(TEST_OUT_DIR, 'file_hasher_bin_host')
FILE_HASHER_DIST = os.path.join(TEST_OUT_DIR, 'file_hasher_dist')


class FileHasherTest(unittest.TestCase):
  def setUp(self):
    mocked_attrs = {
        'file_hasher_host': HOST_FILE_HASHER_EXECUTABLE,
        'file_hasher_device': FILE_HASHER_DIST,
    }
    self._patchers = [
        mock.patch(
            'devil.devil_env._Environment.FetchPath',
            mock.Mock(side_effect=lambda a, device=None: mocked_attrs[a])),
        mock.patch('os.path.exists', new=mock.Mock(return_value=True)),
    ]
    for p in self._patchers:
      p.start()

    device = mock.NonCallableMock()
    device.MAX_ADB_OUTPUT_LENGTH = 9999
    device.RunShellCommand = mock.Mock(side_effect=Exception())
    device.adb = mock.NonCallableMock()
    device.adb.Push = mock.Mock()
    self._mock_device = device

  def tearDown(self):
    for p in self._patchers:
      p.stop()

  def testCalculateHostHashes_singlePath(self):
    test_paths = ['/test/host/file.dat']
    mock_get_cmd_output = mock.Mock(return_value='0123456789abcdef')
    with mock.patch('devil.utils.cmd_helper.GetCmdOutput',
                    new=mock_get_cmd_output):
      out = file_hasher.CalculateHostHashes(test_paths)
      self.assertEquals(1, len(out))
      self.assertTrue('/test/host/file.dat' in out)
      self.assertEquals('0123456789abcdef', out['/test/host/file.dat'])
      mock_get_cmd_output.assert_called_once_with(
          [HOST_FILE_HASHER_EXECUTABLE, '-gz', mock.ANY])

  def testCalculateHostHashes_list(self):
    test_paths = ['/test/host/file0.dat', '/test/host/file1.dat']
    mock_get_cmd_output = mock.Mock(
        return_value='0123456789abcdef\n123456789abcdef0\n')
    with mock.patch('devil.utils.cmd_helper.GetCmdOutput',
                    new=mock_get_cmd_output):
      out = file_hasher.CalculateHostHashes(test_paths)
      self.assertEquals(2, len(out))
      self.assertTrue('/test/host/file0.dat' in out)
      self.assertEquals('0123456789abcdef', out['/test/host/file0.dat'])
      self.assertTrue('/test/host/file1.dat' in out)
      self.assertEquals('123456789abcdef0', out['/test/host/file1.dat'])
      mock_get_cmd_output.assert_called_once_with(
          [HOST_FILE_HASHER_EXECUTABLE, '-gz', mock.ANY])

  def testCalculateDeviceHashes_noPaths(self):
    self._mock_device.RunShellCommand = mock.Mock(side_effect=Exception())

    out = file_hasher.CalculateDeviceHashes([], self._mock_device)
    self.assertEquals(0, len(out))

  def testCalculateDeviceHashes_singlePath(self):
    test_paths = ['/storage/emulated/legacy/test/file.dat']

    device_file_hasher_output = [
        '0123456789abcdef',
    ]
    self._mock_device.RunShellCommand = mock.Mock(
        return_value=device_file_hasher_output)

    with mock.patch('os.path.getsize', return_value=1337):
      out = file_hasher.CalculateDeviceHashes(test_paths, self._mock_device)
      self.assertEquals(1, len(out))
      self.assertTrue('/storage/emulated/legacy/test/file.dat' in out)
      self.assertEquals('0123456789abcdef',
                        out['/storage/emulated/legacy/test/file.dat'])
      self.assertEquals(1,
                        len(self._mock_device.RunShellCommand.call_args_list))

  def testCalculateDeviceHashes_list(self):
    test_paths = [
        '/storage/emulated/legacy/test/file0.dat',
        '/storage/emulated/legacy/test/file1.dat'
    ]
    device_file_hasher_output = [
        '0123456789abcdef',
        '123456789abcdef0',
    ]
    self._mock_device.RunShellCommand = mock.Mock(
        return_value=device_file_hasher_output)

    with mock.patch('os.path.getsize', return_value=1337):
      out = file_hasher.CalculateDeviceHashes(test_paths, self._mock_device)
      self.assertEquals(2, len(out))
      self.assertTrue('/storage/emulated/legacy/test/file0.dat' in out)
      self.assertEquals('0123456789abcdef',
                        out['/storage/emulated/legacy/test/file0.dat'])
      self.assertTrue('/storage/emulated/legacy/test/file1.dat' in out)
      self.assertEquals('123456789abcdef0',
                        out['/storage/emulated/legacy/test/file1.dat'])
      self.assertEquals(1,
                        len(self._mock_device.RunShellCommand.call_args_list))

  def testCalculateDeviceHashes_singlePath_linkerWarning(self):
    # See crbug/479966
    test_paths = ['/storage/emulated/legacy/test/file.dat']

    device_file_hasher_output = [
        'WARNING: linker: /data/local/tmp/file_hasher/file_hasher_bin: '
        'unused DT entry: type 0x1d arg 0x15db',
        'THIS_IS_NOT_A_VALID_CHECKSUM_ZZZ some random text',
        '0123456789abcdef',
    ]
    self._mock_device.RunShellCommand = mock.Mock(
        return_value=device_file_hasher_output)

    with mock.patch('os.path.getsize', return_value=1337):
      out = file_hasher.CalculateDeviceHashes(test_paths, self._mock_device)
      self.assertEquals(1, len(out))
      self.assertTrue('/storage/emulated/legacy/test/file.dat' in out)
      self.assertEquals('0123456789abcdef',
                        out['/storage/emulated/legacy/test/file.dat'])
      self.assertEquals(1,
                        len(self._mock_device.RunShellCommand.call_args_list))

  def testCalculateDeviceHashes_list_fileMissing(self):
    test_paths = [
        '/storage/emulated/legacy/test/file0.dat',
        '/storage/emulated/legacy/test/file1.dat'
    ]
    device_file_hasher_output = [
        '0123456789abcdef',
        '',
    ]
    self._mock_device.RunShellCommand = mock.Mock(
        return_value=device_file_hasher_output)

    with mock.patch('os.path.getsize', return_value=1337):
      out = file_hasher.CalculateDeviceHashes(test_paths, self._mock_device)
      self.assertEquals(2, len(out))
      self.assertTrue('/storage/emulated/legacy/test/file0.dat' in out)
      self.assertEquals('0123456789abcdef',
                        out['/storage/emulated/legacy/test/file0.dat'])
      self.assertTrue('/storage/emulated/legacy/test/file1.dat' in out)
      self.assertEquals('', out['/storage/emulated/legacy/test/file1.dat'])
      self.assertEquals(1,
                        len(self._mock_device.RunShellCommand.call_args_list))

  def testCalculateDeviceHashes_requiresBinary(self):
    test_paths = ['/storage/emulated/legacy/test/file.dat']

    device_file_hasher_output = [
        'WARNING: linker: /data/local/tmp/file_hasher/file_hasher_bin: '
        'unused DT entry: type 0x1d arg 0x15db',
        'THIS_IS_NOT_A_VALID_CHECKSUM_ZZZ some random text',
        '0123456789abcdef',
    ]
    error = device_errors.AdbShellCommandFailedError('cmd', 'out', 2)
    self._mock_device.RunShellCommand = mock.Mock(side_effect=(error, '',
                                                    device_file_hasher_output))

    with mock.patch('os.path.isdir',
                    return_value=True), (mock.patch('os.path.getsize',
                                                    return_value=1337)):
      out = file_hasher.CalculateDeviceHashes(test_paths, self._mock_device)
      self.assertEquals(1, len(out))
      self.assertTrue('/storage/emulated/legacy/test/file.dat' in out)
      self.assertEquals('0123456789abcdef',
                        out['/storage/emulated/legacy/test/file.dat'])
      self.assertEquals(3,
                        len(self._mock_device.RunShellCommand.call_args_list))
      self._mock_device.adb.Push.assert_called_once_with(
          'test/out/directory/file_hasher_dist', '/data/local/tmp/file_hasher')


if __name__ == '__main__':
  unittest.main(verbosity=2)
