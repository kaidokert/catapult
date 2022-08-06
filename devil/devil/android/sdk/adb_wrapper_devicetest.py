#!/usr/bin/env python

# Copyright 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Tests for the AdbWrapper class."""
from __future__ import print_function

import os
import tempfile
import time
import unittest

from devil.android import device_test_case
from devil.android import device_errors
from devil.android.sdk import adb_wrapper


class TestAdbWrapper(device_test_case.DeviceTestCase):
  def setUp(self):
    super(TestAdbWrapper, self).setUp()
    self._adb = adb_wrapper.AdbWrapper(self.serial)
    self._adb.WaitForDevice()

  @staticmethod
  def _MakeTempFile(contents):
    """Make a temporary file with the given contents.

    Args:
      contents: string to write to the temporary file.

    Returns:
      The absolute path to the file.
    """
    fi, path = tempfile.mkstemp()
    with os.fdopen(fi, 'w') as f:
      f.write(contents)
    return path

  def testDeviceUnreachable(self):
    with self.assertRaises(device_errors.DeviceUnreachableError):
      bad_adb = adb_wrapper.AdbWrapper('device_gone')
      bad_adb.Shell('echo test')

  def testShell(self):
    output = self._adb.Shell('echo test', expect_status=0)
    self.assertEqual(output.strip(), 'test')
    output = self._adb.Shell('echo test')
    self.assertEqual(output.strip(), 'test')
    with self.assertRaises(device_errors.AdbCommandFailedError):
      self._adb.Shell('echo test', expect_status=1)

  # We need to access the device serial number here in order
  # to create the persistent shell and check the process.
  # pylint: disable=protected-access
  def testPersistentShell(self):
    serial = self._adb.GetDeviceSerial()
    with self._adb.PersistentShell(serial) as pshell:
      (res1, code1) = pshell.RunCommand('echo TEST')
      (res2, code2) = pshell.RunCommand('echo TEST2')
      self.assertEqual(len(res1), 1)
      self.assertEqual(res1[0], 'TEST')
      self.assertEqual(res2[-1], 'TEST2')
      self.assertEqual(code1, 0)
      self.assertEqual(code2, 0)

  def testPersistentShellKillAdbs(self):
    self._adb = adb_wrapper.AdbWrapper(self.serial, persistent_shell=True)
    self._adb.WaitForDevice()
    self.assertEqual(2, len(self._adb._all_persistent_shells))
    self.assertEqual(2, self._adb._persistent_shells.qsize())
    self._adb.KillPersistentAdbs()
    self.assertEqual(0, len(self._adb._all_persistent_shells))
    self.assertEqual(0, self._adb._persistent_shells.qsize())

  def testPersistentShellRunCommandClose(self):
    self._adb = adb_wrapper.AdbWrapper(self.serial, persistent_shell=True)
    self._adb.WaitForDevice()
    self.assertEqual(2, len(self._adb._all_persistent_shells))
    self.assertEqual(2, self._adb._persistent_shells.qsize())
    output, status = self._adb._get_a_shell().RunCommand('echo FOOBAR',
                                                         close=False)
    self.assertEqual(output[0], 'FOOBAR')
    self.assertEqual(status, 0)
    found_none = False
    for shell in self._adb._all_persistent_shells:
      if shell._process is None:
        found_none = True
        break
    self.assertFalse(found_none)

    # Run a command with a close=True, and then check that a persistent shell
    # has a process set to None.
    output, status = self._adb._get_a_shell().RunCommand('echo FOOBAR',
                                                         close=True)
    self.assertEqual(output[0], 'FOOBAR')
    self.assertEqual(status, 0)
    found_none = False
    for shell in self._adb._all_persistent_shells:
      if shell._process is None:
        found_none = True
        break
    self.assertTrue(found_none)

  def testPersistentShellRunCommandKeepEnds(self):
    self._adb = adb_wrapper.AdbWrapper(self.serial, persistent_shell=True)
    self._adb.WaitForDevice()
    output, status = self._adb._get_a_shell().RunCommand('echo FOOBAR')
    self.assertEqual(output[0], 'FOOBAR')
    self.assertEqual(status, 0)
    output, status = self._adb._get_a_shell().RunCommand('echo FOOBAR\n',
                                                         keepends=False)
    self.assertEqual(output[0], 'FOOBAR')
    self.assertEqual(status, 0)
    output, status = self._adb._get_a_shell().RunCommand('echo FOOBAR\n',
                                                         keepends=True)
    self.assertEqual(output[0], 'FOOBAR\n')
    self.assertEqual(status, 0)

  # pylint: enable=protected-access
  def testPushLsPull(self):
    path = self._MakeTempFile('foo')
    device_path = '/data/local/tmp/testfile.txt'
    local_tmpdir = os.path.dirname(path)
    self._adb.Push(path, device_path)
    files = dict(self._adb.Ls('/data/local/tmp'))
    self.assertTrue('testfile.txt' in files)
    self.assertEqual(3, files['testfile.txt'].st_size)
    self.assertEqual(self._adb.Shell('cat %s' % device_path), 'foo')
    self._adb.Pull(device_path, local_tmpdir)
    with open(os.path.join(local_tmpdir, 'testfile.txt'), 'r') as f:
      self.assertEqual(f.read(), 'foo')

  def testInstall(self):
    path = self._MakeTempFile('foo')
    with self.assertRaises(device_errors.AdbCommandFailedError):
      self._adb.Install(path)

  def testForward(self):
    with self.assertRaises(device_errors.AdbCommandFailedError):
      self._adb.Forward(0, 0)

  def testUninstall(self):
    with self.assertRaises(device_errors.AdbCommandFailedError):
      self._adb.Uninstall('some.nonexistant.package')

  def testRebootWaitForDevice(self):
    self._adb.Reboot()
    print('waiting for device to reboot...')
    while self._adb.GetState() == 'device':
      time.sleep(1)
    self._adb.WaitForDevice()
    self.assertEqual(self._adb.GetState(), 'device')
    print('waiting for package manager...')
    while True:
      try:
        android_path = self._adb.Shell('pm path android')
      except device_errors.AdbShellCommandFailedError:
        android_path = None
      if android_path and 'package:' in android_path:
        break
      time.sleep(1)

  def testRootRemount(self):
    self._adb.Root()
    while True:
      try:
        self._adb.Shell('start')
        break
      except device_errors.DeviceUnreachableError:
        time.sleep(1)
    self._adb.Remount()


if __name__ == '__main__':
  unittest.main()
