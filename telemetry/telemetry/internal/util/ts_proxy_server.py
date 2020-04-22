# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Start and stop tsproxy."""

from py_utils import ts_proxy_server


class TsProxyServer(object):
  """Start and Stop Tsproxy.

  TsProxy provides basic latency, download and upload traffic shaping. This
  class provides a programming API to the tsproxy script in
  telemetry/third_party/tsproxy/tsproxy.py
  """

  def __init__(self, host_ip=None, http_port=None, https_port=None):
    """Initialize TsProxyServer.
    """
    self._ts_proxy_server = ts_proxy_server.TsProxyServer(
        host_ip=host_ip, http_port=http_port, https_port=https_port)

  @property
  def port(self):
    return self.ts_proxy_server.port()

  def StartServer(self, timeout=10, retries=None):
    """Start TsProxy server and verify that it started.
    """
    self._ts_proxy_server.StartServer(timeout, retries)

  def UpdateOutboundPorts(self, http_port, https_port, timeout=5):
    self._ts_proxy_server.UpdateOutboundPorts(http_port, https_port, timeout)

  def UpdateTrafficSettings(
      self, round_trip_latency_ms=None,
      download_bandwidth_kbps=None, upload_bandwidth_kbps=None, timeout=20):
    """Update traffic settings of the proxy server.

    Notes that this method only updates the specified parameter
    """
    self._ts_proxy_server.UpdateTrafficSettings(round_trip_latency_ms,
                                                download_bandwidth_kbps,
                                                upload_bandwidth_kbps,
                                                timeout)
  def StopServer(self):
    """Stop TsProxy Server."""
    return self._ts_proxy_server.StopServer()

  def __enter__(self):
    """Add support for with-statement."""
    self.StartServer()
    return self

  def __exit__(self, unused_exc_type, unused_exc_val, unused_exc_tb):
    """Add support for with-statement."""
    self.StopServer()

