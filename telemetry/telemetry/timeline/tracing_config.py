# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from telemetry.timeline import atrace_config
from telemetry.timeline import chrome_trace_config
from telemetry.timeline import simpleperf_config


class TracingConfig(object):
  """Tracing config is the configuration for tracing in Telemetry.

  TracingConfig configures tracing in Telemetry. It contains tracing options
  that control which core tracing system should be enabled. If a tracing
  system requires additional configuration, e.g., what to trace, then it is
  typically configured in its own config class. TracingConfig provides
  interfaces to access the configuration for those tracing systems.

  Options:
      enable_atrace_trace: a boolean that specifies whether to enable
          atrace tracing.
      enable_cpu_trace: a boolean that specifies whether to enable cpu tracing.
      enable_chrome_trace: a boolean that specifies whether to enable
          chrome tracing.
      enable_platform_display_trace: a boolean that specifies whether to
          platform display tracing.
      enable_android_graphics_memtrack: a boolean that specifies whether
          to enable the memtrack_helper daemon to track graphics memory on
          Android (see goo.gl/4Y30p9). Doesn't have any effects on other OSs.
      enable_battor_trace: a boolean that specifies whether to enable BattOr
          tracing.
      enable_simpleperf: a boolean that specifies whether to enable simpleperf
          profiling.
      trace_navigation: a boolean that specifies whether to enable tracing
          during page navigation.
      trace_interactions: a boolean that specifies whether to enable tracing
          during page interactions.

  Detailed configurations:
      atrace_config: Stores configuration options specific to Atrace.
      chrome_trace_config: Stores configuration options specific to
          Chrome trace.
      simpleperf_config: Stores configuration options specific to simpleperf.
  """

  def __init__(self):
    self._enable_atrace_trace = False
    self._enable_platform_display_trace = False
    self._enable_android_graphics_memtrack = False
    self._enable_battor_trace = False
    self._enable_cpu_trace = False
    self._enable_chrome_trace = False
    self._enable_simpleperf = False
    self._trace_navigation = False
    self._trace_interactions = False

    self._atrace_config = atrace_config.AtraceConfig()
    self._chrome_trace_config = chrome_trace_config.ChromeTraceConfig()
    self._simpleperf_config = simpleperf_config.SimpleperfConfig()

  @property
  def enable_atrace_trace(self):
    return self._enable_atrace_trace

  @enable_atrace_trace.setter
  def enable_atrace_trace(self, value):
    self._enable_atrace_trace = value

  @property
  def enable_cpu_trace(self):
    return self._enable_cpu_trace

  @enable_cpu_trace.setter
  def enable_cpu_trace(self, value):
    self._enable_cpu_trace = value

  @property
  def enable_platform_display_trace(self):
    return self._enable_platform_display_trace

  @enable_platform_display_trace.setter
  def enable_platform_display_trace(self, value):
    self._enable_platform_display_trace = value

  @property
  def enable_android_graphics_memtrack(self):
    return self._enable_android_graphics_memtrack

  @enable_android_graphics_memtrack.setter
  def enable_android_graphics_memtrack(self, value):
    self._enable_android_graphics_memtrack = value

  @property
  def enable_battor_trace(self):
    return self._enable_battor_trace

  @enable_battor_trace.setter
  def enable_battor_trace(self, value):
    self._enable_battor_trace = value

  @property
  def enable_chrome_trace(self):
    return self._enable_chrome_trace

  @enable_chrome_trace.setter
  def enable_chrome_trace(self, value):
    self._enable_chrome_trace = value

  @property
  def enable_simpleperf(self):
    return self._enable_simpleperf

  @enable_simpleperf.setter
  def enable_simpleperf(self, value):
    self._enable_simpleperf = value

  @property
  def trace_navigation(self):
    return self._trace_navigation

  @trace_navigation.setter
  def trace_navigation(self, value):
    self._trace_navigation = value

  @property
  def trace_interactions(self):
    return self._trace_interactions

  @trace_interactions.setter
  def trace_interactions(self, value):
    self._trace_interactions = value

  @property
  def atrace_config(self):
    return self._atrace_config

  @property
  def chrome_trace_config(self):
    return self._chrome_trace_config

  @property
  def simpleperf_config(self):
    return self._simpleperf_config
