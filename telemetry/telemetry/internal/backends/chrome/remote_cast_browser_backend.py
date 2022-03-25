# Copyright 2022 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import sys

import pexpect # pylint: disable=import-error

from telemetry.internal.backends.chrome import cast_browser_backend
from telemetry.internal.backends.chrome import minidump_finder
from telemetry.internal.forwarders import cast_forwarder

# _CAST_DEPLOY_PATH is relative to _CAST_ROOT
_CAST_DEPLOY_PATH = 'data/debug/google'
_CAST_ROOT = '/apps/castshell'


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

  def _CreateForwarderFactory(self):
    return cast_forwarder.CastForwarderFactory(self._ip_addr)

  def _ReadReceiverName(self):
    raise NotImplementedError

  def _SendCommand(self, ssh, command, prompt=None):
    """Uses ssh session to send command.

    If one of the expected prompts is output, return the prompt. If not, a
    ExceptionPexpect exception is thrown."""

    prompt = prompt or []
    prompt.extend([ssh.PROMPT, 'bash-.*[$#]'])
    ssh.sendline(command)
    return ssh.expect(prompt)

  def _StopNativeCast(self):
    ssh = self._platform_backend.GetSSHSession()
    self._SendCommand(ssh, 'systemctl stop castshell')
    self._SendCommand(ssh, 'killall core_runtime_bin')

  def _StopSDKCast(self):
    ssh = self._platform_backend.GetSSHSession()
    self._SendCommand(ssh, 'killall cast_core')
    self._SendCommand(ssh, 'killall platform_app')

  def _StopConjure(self):
    ssh = self._platform_backend.GetSSHSession()
    conjure_block = '/tmp/conjure_block.sh'

    # Put temporary script on top of the Conjure start script and kill process:
    if self._CheckExistenceOnDevice(ssh, conjure_block):
      self._SendCommand(
          ssh,
          r'echo -e "#\!/bin/sh\nwhile true ; do sleep 5 ; done" >%s' %
          conjure_block)
    self._SendCommand(
        ssh,
        'mount -o bind %s /vendor/cast_root/application/chromium/conjure.sh' %
        conjure_block)
    self._SendCommand(ssh, 'killall conjure')

  def _StopCast(self):
    self._StopNativeCast()
    self._StopSDKCast()
    self._StopConjure()

  def _GetCastDirSSHSession(self):
    """Get ssh session with _CAST_ROOT as root and _CAST_DEPLOY_PATH as cwd."""
    ssh = self._platform_backend.GetSSHSession()
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
        logfile=sys.stdout.buffer)

  def _InstallCastCore(self):
    ssh = self._GetCastDirSSHSession()
    cast_core_tar = 'cast_core_qa_package_tar.tar'
    self._ScpToDevice(os.path.join(self._output_dir, cast_core_tar),
                      os.path.join(_CAST_ROOT, _CAST_DEPLOY_PATH))
    if self._CheckExistenceOnDevice(ssh, 'cast_core'):
      self._SendCommand(ssh, 'rm -rf cast_core')
    self._SendCommand(ssh, 'tar xf %s' % cast_core_tar)
    self._SendCommand(ssh, 'rm -rf %s' % cast_core_tar)

  def _CheckExistenceOnDevice(self, ssh, dest):
    """Check file/dir exists on device."""
    resp = self._SendCommand(
        ssh,
        '[[ -a %s ]]; echo result_$?' % dest,
        ['result_0', 'result_1'])
    if resp == 0:
      return True
    return False

  def _InstallCastWebRuntime(self):
    ssh = self._GetCastDirSSHSession()
    self._SendCommand(ssh, 'cd %s && umask 0022' % _CAST_DEPLOY_PATH)
    if self._CheckExistenceOnDevice(ssh, 'cast_runtime'):
      self._SendCommand(ssh, 'rm -rf cast_runtime')
    self._SendCommand(ssh, 'mkdir cast_runtime && chmod 0755 cast_runtime')
    self._ScpToDevice(
        self._runtime_exe,
        os.path.join(_CAST_ROOT, _CAST_DEPLOY_PATH, 'cast_runtime'))
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

    self._dump_finder = minidump_finder.MinidumpFinder(
        self.browser.platform.GetOSName(),
        self.browser.platform.GetArchName())
    self._cast_core_process = self._GetCastDirSSHSession()
    self._SendCommand(self._cast_core_process, 'cd cast_core')
    cast_core_command = [
        'LD_LIBRARY_PATH=/system/lib:/lib',
        'HOME=%s' % os.path.join(_CAST_ROOT, _CAST_DEPLOY_PATH),
        './bin/cast_core',
        '--force_all_apps_discoverable',
        '--remote-debugging-port=%d' % cast_browser_backend.DEVTOOLS_PORT,
    ]
    self._cast_core_process.sendline(' '.join(cast_core_command))

    self._browser_process = self._GetCastDirSSHSession()
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
    self._StopSDKCast()
