# Copyright 2022 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import os
import pexpect # pylint: disable=import-error
import sys

from pexpect import pxssh # pylint: disable=import-error
from telemetry.internal.backends.chrome import cast_browser_backend
from telemetry.internal.backends.chrome import minidump_finder

_CAST_DEPLOY_PATH = 'data/debug/google'
_CAST_ROOT = '/apps/castshell'
_CAST_TARGET_DIR = '/data/app/castshell/google'
_MERGED_CFG_PATH_DST = '/data/app/castshell/vizio/google/cast_core/conf'
_UMOUNT_CMD = 'while umount {path}; do echo "Unmounted!"; done'


class RemoteCastBrowserBackend(cast_browser_backend.CastBrowserBackend):
  def __init__(self, cast_platform_backend, browser_options,
               browser_directory, profile_directory, casting_tab):
    self._ip_addr = cast_platform_backend.ip_addr
    super(RemoteCastBrowserBackend, self).__init__(
        cast_platform_backend,
        browser_options=browser_options,
        browser_directory=browser_directory,
        profile_directory=profile_directory,
        casting_tab=casting_tab)

  def _ReadReceiverName(self):
    raise NotImplementedError

  def _GetSSHSession(self):
    ssh = pxssh.pxssh()
    ssh.login(self._ip_addr, username='root', password='root')
    return ssh

  def _SendCommand(self, ssh, command, prompt=None):
    cmd_prompt = [ssh.PROMPT, 'bash-.*[$#]']
    if prompt:
      cmd_prompt.extend(prompt)
    ssh.sendline(command)
    return ssh.expect(cmd_prompt)

  def _StopNativeCast(self):
    ssh = self._GetSSHSession()
    self._SendCommand(ssh, 'systemctl stop castshell')
    self._SendCommand(ssh, 'killall core_runtime_bin')

  def _StopSDKCast(self):
    ssh = self._GetSSHSession()
    self._SendCommand(ssh, 'killall -9 crash_uploader')
    self._SendCommand(ssh, 'killall platform_app')

  def _StopCast(self):
    self._StopNativeCast()
    self._StopSDKCast()

  def _EnterCastDir(self):
    ssh = self._GetSSHSession()
    self._SendCommand(ssh, 'su', ['Password:'])
    self._SendCommand(ssh, 'root')
    self._SendCommand(ssh, 'setenforce 0')
    self._SendCommand(ssh, 'chroot %s' % _CAST_ROOT)
    self._SendCommand(ssh, 'mkdir -p %s' % _CAST_DEPLOY_PATH)
    self._SendCommand(ssh, 'cd %s' % _CAST_DEPLOY_PATH)
    return ssh

  def _ScpToDevice(self, source, dest):
    scp_opts = [
        '-o UserKnownHostsFile=/dev/null', '-o ConnectTimeout=30',
        '-o ServerAliveInterval=2', '-o ServerAliveCountMax=2',
        '-o StrictHostKeyChecking=no'
    ]
    scp_cmd = 'scp %s %s %s' % (
        ' '.join(scp_opts),
        source,
        'root@%s:%s' % (self._ip_addr, dest),
    )
    pexpect.run(
        scp_cmd,
        events={'(?i)password:': 'root\n'},
        timeout=300,
        logfile=sys.stdout.buffer,
        withexitstatus=True)

  def _InstallCastCore(self):
    ssh = self._EnterCastDir()
    self._ScpToDevice(self._output_dir,
                      os.path.join(_CAST_ROOT, _CAST_DEPLOY_PATH))
    if self._CheckExistenceOnDevice(ssh, 'cast_core'):
      self._SendCommand(ssh, 'rm -rf cast_core')
    self._SendCommand(ssh, 'tar xf %s' % self._output_dir)
    self._SendCommand(ssh, 'rm -rf %s' % self._output_dir)

  def _CheckExistenceOnDevice(self, ssh, dest):
    """Check file/dir exists on device."""
    resp = self._SendCommand(
        ssh,
        '[[ -a %s ]]; echo result_$?' % dest,
        ['result_0', 'result_1'])
    if resp == 2:
      return True
    return False

  def _InstallCastWebRuntime(self):
    ssh = self._GetSSHSession()
    deploy_path = os.path.join(_CAST_ROOT, _CAST_DEPLOY_PATH)
    self._SendCommand(ssh, 'cd %s && umask 0022' % deploy_path)
    if self._CheckExistenceOnDevice(ssh, 'cast_runtime'):
      self._SendCommand(ssh, 'rm -rf cast_runtime')
    self._SendCommand(ssh, 'mkdir cast_runtime && chmod 0755 cast_runtime')
    self._ScpToDevice(
        self._runtime_exe,
        os.path.join(deploy_path, 'cast_runtime'))
    self._SendCommand(
        ssh,
        'cd cast_runtime && unzip %(cwr)s && rm %(cwr)s' %
        {'cwr': os.path.basename(self._runtime_exe)})
    self._SendCommand(
        ssh,
        'find . -type f | xargs chmod 0644 && ' \
        'chmod 0755 core_runtime dumpstate lib/*')

  def Start(self, startup_args):
    self._StopCast()
    self._InstallCastCore()
    self._InstallCastWebRuntime()

    # Cast Core needs to start with a fixed devtools port.
    self._devtools_port = 9222

    self._dump_finder = minidump_finder.MinidumpFinder(
        self.browser.platform.GetOSName(),
        self.browser.platform.GetArchName())
    self._cast_core_process = self._EnterCastDir()
    self._SendCommand(self._cast_core_process, 'cd %s' % _CAST_DEPLOY_PATH)
    cast_core_command = [
        'LD_LIBRARY_PATH=/system/lib:/lib',
        'HOME=%s' % os.path.join(_CAST_ROOT, _CAST_DEPLOY_PATH),
        './bin/cast_core',
        '--force_all_apps_discoverable',
        '--remote-debugging-port=%d' % self._devtools_port,
    ]
    self._cast_core_process.sendline(' '.join(cast_core_command))

    self._browser_process = self._EnterCastDir()
    self._SendCommand(self._browser_process, 'cd %s' % _CAST_DEPLOY_PATH)
    runtime_command = [
        'HOME=%s' % os.path.join(_CAST_ROOT, _CAST_DEPLOY_PATH),
        './bin/platform_app',
        '--config', 'conf/platform_app_config_sdk.json'
    ]
    self._browser_process.sendline(' '.join(runtime_command))
    self._ReadReceiverName()
    self._WaitForSink()
    self._casting_tab.action_runner.Navigate('about:blank')
    self._casting_tab.action_runner.tab.StartTabMirroring(self._receiver_name)
    self.BindDevToolsClient()

  def GetPid(self):
    return self._browser_process.pid

  def Background(self):
    raise NotImplementedError

  def Close(self):
    super(RemoteCastBrowserBackend, self).Close()

    if self._browser_process:
      logging.info('Shutting down Cast browser.')
      self._browser_process.close()
      self._browser_process = None
    if self._cast_core_process:
      self._cast_core_process.close()
      self._cast_core_process = None
    self._StopSDKCast()
