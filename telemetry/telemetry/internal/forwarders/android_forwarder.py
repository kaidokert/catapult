# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from py_utils import atexit_with_log
import logging
import subprocess

from telemetry.core import util
from telemetry.internal import forwarders

from devil.android import device_errors
try:
  from devil.android import forwarder
except ImportError as exc:
  # Module is not importable e.g. on Windows hosts.
  logging.warning('Failed to import devil.android.forwarder: %s', exc)


class AndroidForwarderFactory(forwarders.ForwarderFactory):

  def __init__(self, device):
    super(AndroidForwarderFactory, self).__init__()
    self._device = device

  # TODO(#1977): Make API consistent accross forwarders.
  def Create(self, port_pair,  # pylint: disable=arguments-differ
             reverse=False):
    try:
      if reverse:
        raise Exception('boom!')
        # return AndroidReverseForwarder(self._device, port_pair)
      else:
        return AndroidForwarder(self._device, port_pair)
    except Exception:
      logging.exception(
          'Failed to map local_port=%r to remote_port=%r (reverse=%r).',
          port_pair.local_port, port_pair.remote_port, reverse)
      _LogExtraDebugInformation(
          self._ListCurrentAdbConnections,
          self._ListWebPageReplayInstances,
          self._ListHostTcpPortsInUse,
          self._ListDeviceTcpPortsInUse,
          self._ListDeviceUnixDomainSocketsInUse,
          self._ListDeviceLsofEntries,
      )
      raise

  def _ListCurrentAdbConnections(self):
    """Current adb connections"""
    return self._device.adb.ForwardList().splitlines()

  def _ListWebPageReplayInstances(self):
    """WebPageReplay instances"""
    lines = subprocess.check_output(['ps', '-ef']).splitlines()
    return (line for line in lines if 'webpagereplay' in line)

  def _ListHostTcpPortsInUse(self):
    """Host tcp ports in use"""
    return subprocess.check_output(['netstat', '-t']).splitlines()

  def _ListDeviceTcpPortsInUse(self):
    """Device tcp ports in use"""
    return self._device.ReadFile('/proc/net/tcp', as_root=True,
                                 force_pull=True).splitlines()

  def _ListDeviceUnixDomainSocketsInUse(self):
    """Device unix domain socets in use"""
    return self._device.ReadFile('/proc/net/unix', as_root=True,
                                 force_pull=True).splitlines()

  def _ListDeviceLsofEntries(self):
    """Device lsof entries"""
    return self._device.RunShellCommand(['lsof'], as_root=True,
                                        check_return=True)


def _LogExtraDebugInformation(*args):
  if logging.getEffectiveLevel() > logging.DEBUG:
    logging.warning('Increase verbosity to see more debug information.')
    return

  logging.debug('== Dumping possibly useful debug information ==')
  for get_debug_lines in args:
    logging.debug('- %s:', get_debug_lines.__doc__)
    try:
      for line in get_debug_lines():
        logging.debug('  - %s', line)
    except Exception:  # pylint: disable=broad-except
      logging.exception(
          'Ignoring exception raised during %s.', get_debug_lines.__name__)
  logging.debug('===============================================')


class AndroidForwarder(forwarders.Forwarder):
  """Use host_forwarder to map a known local port with a remote (device) port.

  The remote port may be 0, in such case the forwarder will automatically
  choose an available port.

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
  choose an available port.

  See:
  - catapult:/devil/devil/android/sdk/adb_wrapper.py
  """

  def __init__(self, device, port_pair):
    super(AndroidReverseForwarder, self).__init__(port_pair)
    self._device = device
    local_port, remote_port = port_pair
    assert remote_port, 'Remote port must be given'
    if not local_port:
      local_port = util.GetUnreservedAvailableLocalPort()
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
