# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from py_utils import atexit_with_log
import logging
import subprocess

from telemetry.core import util
from telemetry.internal import forwarders

from devil.android import device_errors
from devil.android import forwarder


class AndroidForwarderFactory(forwarders.ForwarderFactory):

  def __init__(self, device):
    super(AndroidForwarderFactory, self).__init__()
    self._device = device

  def Create(self, port_pair,  # pylint: disable=arguments-differ
             reverse=False):
    try:
      if reverse:
        return AndroidForwarder(self._device, port_pair)
      else:
        return AndroidReverseForwarder(self._device, port_pair)
    except Exception:
      logging.exception(
          'Failed to map local_port=%r to remote_port=%r (reverse=%r).',
          port_pair.local_port, port_pair.remote_port, reverse)

      def ListCurrentAdbConnections():
        """Currently forwarded connections"""
        return self._device.adb.ForwardList().splitlines()

      def ListHostTcpPortsInUse():
        """Host tcp ports in use"""
        return subprocess.check_output(['netstat -t']).splitlines()

      def ListDeviceUnixDomainSocketsInUse():
        """Device unix domain socets in use"""
        return self.device.ReadFile('/proc/net/unix', as_root=True,
                                    force_pull=True).splitlines()

      def ListWebPageReplayInstances():
        """Alive webpagereplay instances"""
        for line in subprocess.check_output(['ps', '-ef']).splitlines():
          if 'webpagereplay' in line:
            yield line

      def ListDeviceTcpPortsInUse():
        """Possibly relevant device tcp ports in use"""
        proc_net_tcp_target = ':%s ' % hex(port_pair.remote_port)[2:]
        for line in self._device.ReadFile(
            '/proc/net/tcp', as_root=True, force_pull=True).splitlines():
          if proc_net_tcp_target in line:
            yield line

      def ListRelevantLsofEntries():
        """Possibly relevant lsof entries"""
        lsof_target = str(port_pair.remote_port)
        for line in self._device.RunShellCommand(
            ['lsof'], as_root=True, check_return=True):
          if lsof_target in line:
            yield line

      debug_infos = [
          ListCurrentAdbConnections,
          ListHostTcpPortsInUse,
          ListDeviceUnixDomainSocketsInUse,
          ListWebPageReplayInstances,
      ]
      if port_pair.remote_port:
        debug_infos.extend([
            ListDeviceTcpPortsInUse,
            ListRelevantLsofEntries,
        ])

      _LogDebugInfos(debug_infos)
      raise


def _LogDebugInfos(debug_infos):
  for list_debug_lines in debug_infos:
    logging.warning('%s:', list_debug_lines.__doc__)
    try:
      for line in list_debug_lines():
        logging.warning('  %s', line)
    except Exception:  # pylint: disable=broad-except
      logging.warning('Exception raised during %s.', list_debug_lines.__name__)


class AndroidForwarder(forwarders.Forwarder):
  """Use host_forwarder to map a known local port with a remote (device) port.

  The remote port may be 0, in such case the forwarder will automatically
  chose an available port.

  See:
  - chromium:/src/tools/android/forwarder2
  - catapult:/devil/devil/android/forwarder.py
  """

  def __init__(self, device, port_pair):
    super(AndroidForwarder, self).__init__(port_pair)
    self._device = device
    forwarder.Forwarder.Map(
        [(port_pair.remote_port, port_pair.local_port)], self._device)
    self._port_pair = (
        forwarders.PortPair(
            port_pair.local_port,
            forwarder.Forwarder.DevicePortForHostPort(port_pair.local_port)))
    atexit_with_log.Register(self.Close)
    # TODO(tonyg): Verify that each port can connect to host.

  def Close(self):
    if self._forwarding:
      forwarder.Forwarder.UnmapDevicePort(
          self._port_pair.remote_port, self._device)
    super(AndroidForwarder, self).Close()


class AndroidReverseForwarder(forwarders.Forwarder):
  """Use adb forward to map a known remote (device) port with a local port.

  The local port may be 0, in such case the forwarder will automatically
  chose an available port.

  See:
  - catapult:/devil/devil/android/sdk/adb_wrapper.py
  """

  def __init__(self, device, port_pair):
    super(AndroidReverseForwarder, self).__init__(port_pair)
    local_port, remote_port = port_pair
    assert remote_port, 'Remove port must be given'
    if not local_port:
      local_port = util.GetUnreservedAvailableLocalPort()
    self._device = device
    self._device.adb.Forward('tcp:%d' % local_port, remote_port)
    self._port_pair = forwarders.PortPair(local_port, remote_port)

  def Close(self):
    if self._forwarding:
      # This used to run `adb forward --list` to check that the requested
      # port was actually being forwarded to self._device. Unfortunately,
      # starting in adb 1.0.36, a bug (b/31811775) keeps this from working.
      # For now, try to remove the port forwarding and ignore failures.
      local_address = 'tcp:%d' % self._port_pair.local_port
      try:
        self._device.adb.ForwardRemove(local_address)
      except device_errors.AdbCommandFailedError:
        logging.critical(
            'Attempted to unforward %s but failed.', local_address)
    super(AndroidReverseForwarder, self).Close()
