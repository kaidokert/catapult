# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""E2E Tests for the Sheriff Config Service

This test assumes a number of things:

  - We are running against an emulator for the datastore service.
  - We are mocking the luci-config service calls and responses.

We typically run this in the testing Docker container.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from tests.utils import HttpMockSequenceWithDiscovery
from google.cloud import datastore
import base64
import service
import time
import unittest
from unittest import mock


class LuciPollingTest(unittest.TestCase):

  def setUp(self):
    with open(
        'tests/sample-configs-get_project_configs.json') as sample_config_file:
      self.sample_config = sample_config_file.read()
    self.app = service.CreateApp({
        'environ': {
            'GOOGLE_CLOUD_PROJECT': 'chromeperf',
            'GAE_SERVICE': 'sheriff-config',
        },
        'datastore_client':
            datastore.Client(project='chromeperf'),
        'http':
            HttpMockSequenceWithDiscovery([({
                'status': '200'
            }, self.sample_config)]),
    })
    self.maxDiff = None

  def testPollAndMatch(self):
    client = self.app.test_client()
    response = client.get(
        '/configs/update', headers={'X-Forwarded-Proto': 'https'})
    self.assertEqual(response.status_code, 200)
    response = client.post(
        '/subscriptions/match',
        json={
            'path': 'Master/Bot/Test/Metric/Something',
            'stats': ['PCT_99'],
            'metadata': {
                'units': 'SomeUnit',
                'master': 'Master',
                'bot': 'Bot',
                'benchmark': 'Test',
                'metric_parts': ['Metric', 'Something'],
            }
        },
        headers={'X-Forwarded-Proto': 'https'})
    self.assertEqual(response.status_code, 200)
    response_proto = response.get_json()
    self.assertDictEqual(
        response_proto, {
            'subscriptions': [{
                'config_set': 'projects/other_project',
                'revision': '0123456789abcdff',
                'subscription': {
                    'name': 'Expected 1',
                    'monorail_project_id': 'non-chromium',
                    'contact_email': 'expected-1@example.com',
                    'bug_labels': ['Some-Label'],
                    'bug_components': ['Some>Component'],
                    'auto_triage': {
                        'enable': False
                    },
                    'auto_bisection': {
                        'enable': False
                    },
                    'rules': {},
                }
            }]
        })

  def makeMockHttpConfig(self, cfg_str):
    enc_cfg = base64.b64encode(cfg_str.encode('utf8')).decode('utf8')
    ret = ("""{
      "configs": [
        {
          "url": "https://example.com/project/sources/+/0123456789abcdef/configs/chromeperf-sheriff.cfg",
          "content": "%s",
          "content_hash": "v1:somehash",
          "config_set": "projects/v8",
          "revision": "0123456789abcdef"
        }
      ]
              }""" % enc_cfg)
    return ret

  def testPollAndMatchV8Perf(self):
    # pylint: enable=line-too-long
    config = self.makeMockHttpConfig(u"""
# V8-specific sheriff configurations.
#
# This file follows the proto definition at
# https://source.chromium.org/chromium/chromium/src/+/master:third_party/catapult/dashboard/dashboard/proto/sheriff.proto
subscriptions {
  name: "V8 Future Perf Sheriff"
  notification_email: "v8-future-perf-alerts@google.com"
  contact_email: "v8-future-perf-alerts@google.com"
  bug_components: ["Blink>JavaScript"]
  bug_labels: "Performance-Sheriff-V8"
  visibility: PUBLIC
  rules: {
    match: [
      { glob: "internal.client.v8/*/v8/ARES-6-Future/*" },
      { glob: "internal.client.v8/*/v8/Octane2.1-Future/*" },
      { glob: "internal.client.v8/*/v8/RuntimeStats/Group-Optimize*/*/*/*/*/Future" },
      { glob: "internal.client.v8/*/v8/RuntimeStats/Group-Optimize*/*/*/*/Future" },
      { glob: "internal.client.v8/*/v8/RuntimeStats/Group-Optimize*/*/*/Future" },
      { glob: "internal.client.v8/*/v8/RuntimeStats/Group-Optimize*/*/Future" }
    ]
  }
}
subscriptions {
  name: "V8 Memory Perf Sheriff"
  notification_email: "v8-memory-alerts@google.com"
  contact_email: "v8-memory-alerts@google.com"
  bug_components: ["Blink>JavaScript>GC"]
  bug_labels: "Performance-Sheriff-V8"
  visibility: PUBLIC
  rules: {
    match: [
      { glob: "ChromiumPerf/*/memory.desktop/memory:chrome:all_processes:reported_by_chrome:v8:allocated_objects_size_avg/*/*" },
      { glob: "ChromiumPerf/*/memory.desktop/memory:chrome:all_processes:reported_by_chrome:v8:effective_size_avg/*/*" },
      { glob: "ChromiumPerf/*/memory.desktop/memory:chrome:all_processes:reported_by_chrome:blink_gc:allocated_objects_size_avg/*/*" },
      { glob: "ChromiumPerf/*/memory.desktop/memory:chrome:all_processes:reported_by_chrome:blink_gc:effective_size_avg/*/*" },
      { glob: "ChromiumPerf/*/system_health.memory_desktop/memory:chrome:all_processes:reported_by_chrome:v8:allocated_objects_size_avg/*/*" },
      { glob: "ChromiumPerf/*/system_health.memory_desktop/memory:chrome:all_processes:reported_by_chrome:v8:effective_size_avg/*/*" },
      { glob: "ChromiumPerf/*/system_health.memory_desktop/memory:chrome:all_processes:reported_by_chrome:blink_gc:allocated_objects_size_avg/*/*" },
      { glob: "ChromiumPerf/*/system_health.memory_desktop/memory:chrome:all_processes:reported_by_chrome:blink_gc:effective_size_avg/*/*" },
      { glob: "ChromiumPerf/*/system_health.memory_mobile/memory:chrome:all_processes:reported_by_chrome:v8:allocated_objects_size_avg/*/*" },
      { glob: "ChromiumPerf/*/system_health.memory_mobile/memory:chrome:all_processes:reported_by_chrome:v8:effective_size_avg/*/*" },
      { glob: "ChromiumPerf/*/system_health.memory_mobile/memory:chrome:all_processes:reported_by_chrome:blink_gc:allocated_objects_size_avg/*/*" },
      { glob: "ChromiumPerf/*/system_health.memory_mobile/memory:chrome:all_processes:reported_by_chrome:blink_gc:effective_size_avg/*/*" },
      { glob: "ChromiumPerf/*/system_health.memory_mobile/memory:webview:all_processes:reported_by_chrome:v8:allocated_objects_size_avg/*/*" },
      { glob: "ChromiumPerf/*/system_health.memory_mobile/memory:webview:all_processes:reported_by_chrome:v8:effective_size_avg/*/*" },
      { glob: "ChromiumPerf/*/system_health.memory_mobile/memory:webview:all_processes:reported_by_chrome:blink_gc:allocated_objects_size_avg/*/*" },
      { glob: "ChromiumPerf/*/system_health.memory_mobile/memory:webview:all_processes:reported_by_chrome:blink_gc:effective_size_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/memory:chrome:renderer_processes:reported_by_chrome:v8:heap:allocated_objects_size_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/memory:chrome:renderer_processes:reported_by_chrome:v8:heap:allocated_objects_size_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/memory:chrome:renderer_processes:reported_by_chrome:blink_gc:allocated_objects_size_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/memory:chrome:renderer_processes:reported_by_chrome:blink_gc:allocated_objects_size_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/memory:chrome:renderer_processes:reported_by_chrome:v8:heap:effective_size_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/memory:chrome:renderer_processes:reported_by_chrome:v8:heap:effective_size_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/memory:chrome:renderer_processes:reported_by_chrome:blink_gc:effective_size_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/memory:chrome:renderer_processes:reported_by_chrome:blink_gc:effective_size_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/total:500ms_window:renderer_eqt:v8_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/total:500ms_window:renderer_eqt_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/unified-gc-total_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/unified-gc-total_sum/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/v8-gc-full-mark-compactor_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/v8-gc-full-mark-compactor_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/v8-gc-full-mark-compactor_sum/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/v8-gc-incremental-finalize_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/v8-gc-incremental-finalize_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/v8-gc-incremental-finalize_sum/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/v8-gc-incremental-step_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/v8-gc-incremental-step_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/v8-gc-incremental-step_sum/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/v8-gc-latency-mark-compactor_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/v8-gc-latency-mark-compactor_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/v8-gc-latency-mark-compactor_sum/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/v8-gc-scavenger_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/v8-gc-scavenger_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/v8-gc-scavenger_sum/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/v8-gc-total_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/v8-gc-total_sum/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/blink-gc-atomic-pause_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/blink-gc-atomic-pause_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/blink-gc-atomic-pause_sum/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/blink-gc-unified-marking-by-v8_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/blink-gc-unified-marking-by-v8_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/blink-gc-unified-marking-by-v8_sum/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/blink-gc-incremental-start_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/blink-gc-incremental-start_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/blink-gc-incremental-start_sum/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/blink-gc-incremental-step_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/blink-gc-incremental-step_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/blink-gc-incremental-step_sum/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/blink-gc-mark-background_sum/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/blink-gc-mark-foreground_sum/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/blink-gc-sweep-background_sum/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/blink-gc-sweep-foreground_sum/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/blink-gc-complete-sweep_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/blink-gc-complete-sweep_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/blink-gc-complete-sweep_sum/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/memory:chrome:renderer_processes:reported_by_chrome:v8:heap:allocated_objects_size_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/memory:chrome:renderer_processes:reported_by_chrome:v8:heap:allocated_objects_size_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/memory:chrome:renderer_processes:reported_by_chrome:blink_gc:allocated_objects_size_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/memory:chrome:renderer_processes:reported_by_chrome:blink_gc:allocated_objects_size_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/memory:chrome:renderer_processes:reported_by_chrome:v8:heap:effective_size_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/memory:chrome:renderer_processes:reported_by_chrome:v8:heap:effective_size_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/memory:chrome:renderer_processes:reported_by_chrome:blink_gc:effective_size_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/memory:chrome:renderer_processes:reported_by_chrome:blink_gc:effective_size_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/total:500ms_window:renderer_eqt:v8_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/total:500ms_window:renderer_eqt_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/unified-gc-total_sum/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/unified-gc-total_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/v8-gc-full-mark-compactor_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/v8-gc-full-mark-compactor_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/v8-gc-full-mark-compactor_sum/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/v8-gc-incremental-finalize_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/v8-gc-incremental-finalize_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/v8-gc-incremental-finalize_sum/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/v8-gc-incremental-step_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/v8-gc-incremental-step_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/v8-gc-incremental-step_sum/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/v8-gc-latency-mark-compactor_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/v8-gc-latency-mark-compactor_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/v8-gc-latency-mark-compactor_sum/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/v8-gc-scavenger_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/v8-gc-scavenger_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/v8-gc-scavenger_sum/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/v8-gc-total_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/v8-gc-total_sum/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/blink-gc-atomic-pause_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/blink-gc-atomic-pause_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/blink-gc-atomic-pause_sum/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/blink-gc-unified-marking-by-v8_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/blink-gc-unified-marking-by-v8_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/blink-gc-unified-marking-by-v8_sum/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/blink-gc-incremental-start_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/blink-gc-incremental-start_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/blink-gc-incremental-start_sum/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/blink-gc-incremental-step_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/blink-gc-incremental-step_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/blink-gc-incremental-step_sum/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/blink-gc-mark-background_sum/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/blink-gc-mark-foreground_sum/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/blink-gc-sweep-background_sum/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/blink-gc-sweep-foreground_sum/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/blink-gc-complete-sweep_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/blink-gc-complete-sweep_max/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/blink-gc-complete-sweep_sum/*/*" }
    ]
  }
  auto_triage: {
    rules: {
      match: {
        regex: ".+"
      }
    }
  }
  auto_bisection: {
    rules: {
      match: {
        regex: ".+"
      }
    }
  }
}
subscriptions {
  name: "V8 Perf Sheriff"
  notification_email: "v8-perf-alerts@google.com"
  contact_email: "v8-perf-alerts@google.com"
  bug_components: ["Blink>JavaScript"]
  bug_labels: "Performance-Sheriff-V8"
  visibility: PUBLIC
  rules: {
    match: [
      { glob: "ChromiumPerf/*/*/total:500ms_window:renderer_eqt:v8:compile:compile-unoptimize_max" },
      { glob: "ChromiumPerf/*/*/total:500ms_window:renderer_eqt:v8:compile:optimize_max" },
      { glob: "ChromiumPerf/*/*/total:500ms_window:renderer_eqt:v8:compile:parse_max" },
      { glob: "ChromiumPerf/*/*/total:500ms_window:renderer_eqt:v8:compile_max" },
      { glob: "ChromiumPerf/*/*/total:500ms_window:renderer_eqt:v8:execute_max" },
      { glob: "ChromiumPerf/*/*/total:500ms_window:renderer_eqt:v8:gc:full-mark-compactor_max" },
      { glob: "ChromiumPerf/*/*/total:500ms_window:renderer_eqt:v8:gc:incremental-marking_max" },
      { glob: "ChromiumPerf/*/*/total:500ms_window:renderer_eqt:v8:gc:latency-mark-compactor_max" },
      { glob: "ChromiumPerf/*/*/total:500ms_window:renderer_eqt:v8:gc:memory-mark-compactor_max" },
      { glob: "ChromiumPerf/*/*/total:500ms_window:renderer_eqt:v8:gc:scavenger_max" },
      { glob: "ChromiumPerf/*/*/total:500ms_window:renderer_eqt:v8:gc_max" },
      { glob: "ChromiumPerf/*/*/total:500ms_window:renderer_eqt:v8_max" },
      { glob: "ChromiumPerf/*/speedometer2/*/Speedometer2" },
      { glob: "ChromiumPerf/*/v8.google/v8_execution_cpu_total_avg" },
      { glob: "ChromiumPerf/*/v8.browsing_*/API:duration_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_*/Compile-Background:duration_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_*/Compile:duration_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_*/GC:duration_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_*/IC:duration_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_*/JavaScript:duration_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_*/Optimize:duration_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_*/Parse-Background:duration_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_*/Parse:duration_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_*/Total:duration_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_*/V8 C++:duration_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_*/V8-Only:duration_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_*/V8-Only-Main-Thread:duration_avg/*/*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/interactive:500ms_window:renderer_eqt:v8:*" },
      { glob: "ChromiumPerf/*/v8.browsing_desktop/total:500ms_window:renderer_eqt:v8:*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/interactive:500ms_window:renderer_eqt:v8:*" },
      { glob: "ChromiumPerf/*/v8.browsing_mobile/total:500ms_window:renderer_eqt:v8:*" },
      { glob: "ChromiumPerf/*/jetstream2/*/JetStream2" },
      { glob: "internal.client.v8/*/JSTests/BytecodeHandlers/*/*" },
      { glob: "internal.client.v8/*/JSTests/InterpreterEntryTrampoline/*/*" },
      { glob: "internal.client.v8/*/v8/*/JSTests/BytecodeHandlers/*/*" },
      { glob: "internal.client.v8/*/v8/Infra/Stability/*" },
      { glob: "internal.client.v8/*/v8/Infra/Stability/*/*" },
      { glob: "internal.client.v8/*/v8/Octane2.1-NoOpt/Ignition/*" },
      { glob: "internal.client.v8/*/v8/Octane2.1/*" },
      { glob: "internal.client.v8/*/v8/web-tooling-benchmark/*" },
      { glob: "internal.client.v8/*/v8/AreWeFastYet/*" },
      { glob: "internal.client.v8/*/v8/BigNum/*" },
      { glob: "internal.client.v8/*/v8/BigNum/*/*" },
      { glob: "internal.client.v8/*/v8/Compile/*" },
      { glob: "internal.client.v8/*/v8/Embenchen/*" },
      { glob: "internal.client.v8/*/v8/Emscripten/*" },
      { glob: "internal.client.v8/*/v8/JSBench/*" },
      { glob: "internal.client.v8/*/v8/JSTests/*" },
      { glob: "internal.client.v8/*/v8/JSTests/*/*" },
      { glob: "internal.client.v8/*/v8/JetStream/*" },
      { glob: "internal.client.v8/*/v8/KrakenOrig/*" },
      { glob: "internal.client.v8/*/v8/Massive/*" },
      { glob: "internal.client.v8/*/v8/Massive/*/*" },
      { glob: "internal.client.v8/*/v8/Promises/*" },
      { glob: "internal.client.v8/*/v8/RegExp/RegExp/*" },
      { glob: "internal.client.v8/*/v8/Ritz/*" },
      { glob: "internal.client.v8/*/v8/SixSpeed/*" },
      { glob: "internal.client.v8/*/v8/SixSpeed/*/*" },
      { glob: "internal.client.v8/*/v8/SunSpider/*" },
      { glob: "internal.client.v8/x64/v8/RuntimeStats/Group-API/duration/*/*" },
      { glob: "internal.client.v8/x64/v8/RuntimeStats/Group-Callback/duration/*/*" },
      { glob: "internal.client.v8/x64/v8/RuntimeStats/Group-Compile/duration/*/*" },
      { glob: "internal.client.v8/x64/v8/RuntimeStats/Group-GC/duration/*/*" },
      { glob: "internal.client.v8/x64/v8/RuntimeStats/Group-IC/duration/*/*" },
      { glob: "internal.client.v8/x64/v8/RuntimeStats/Group-JavaScript/duration/*/*" },
      { glob: "internal.client.v8/x64/v8/RuntimeStats/Group-Optimize/duration/*/*" },
      { glob: "internal.client.v8/x64/v8/RuntimeStats/Group-Parse/duration/*/*" },
      { glob: "internal.client.v8/x64/v8/RuntimeStats/Group-Runtime/duration/*/*" },
      { glob: "internal.client.v8/x64/v8/RuntimeStats/Group-Total-V8/duration/*/*" },
      { glob: "internal.client.v8/x64/v8/SixSpeed/*" },
      { glob: "internal.client.v8/x64/v8/SixSpeed/*/*" },
      { glob: "internal.client.v8/x64/v8/SunSpider/*" },
      { glob: "ChromiumPerf/*/v8.runtime_stats.top_25/API:count_avg/*" },
      { glob: "ChromiumPerf/*/v8.runtime_stats.top_25/API:duration_avg/*" },
      { glob: "ChromiumPerf/*/v8.runtime_stats.top_25/Callback:count_avg/*" },
      { glob: "ChromiumPerf/*/v8.runtime_stats.top_25/Callback:duration_avg/*" },
      { glob: "ChromiumPerf/*/v8.runtime_stats.top_25/Compile:count_avg/*" },
      { glob: "ChromiumPerf/*/v8.runtime_stats.top_25/Compile:duration_avg/*" },
      { glob: "ChromiumPerf/*/v8.runtime_stats.top_25/GC:count_avg/*" },
      { glob: "ChromiumPerf/*/v8.runtime_stats.top_25/GC:duration_avg/*" },
      { glob: "ChromiumPerf/*/v8.runtime_stats.top_25/IC:count_avg/*" },
      { glob: "ChromiumPerf/*/v8.runtime_stats.top_25/IC:duration_avg/*" },
      { glob: "ChromiumPerf/*/v8.runtime_stats.top_25/JavaScript:count_avg/*" },
      { glob: "ChromiumPerf/*/v8.runtime_stats.top_25/JavaScript:duration_avg/*" },
      { glob: "ChromiumPerf/*/v8.runtime_stats.top_25/Optimize:count_avg/*" },
      { glob: "ChromiumPerf/*/v8.runtime_stats.top_25/Optimize:duration_avg/*" },
      { glob: "ChromiumPerf/*/v8.runtime_stats.top_25/Parse:count_avg/*" },
      { glob: "ChromiumPerf/*/v8.runtime_stats.top_25/Parse:duration_avg/*" },
      { glob: "ChromiumPerf/*/v8.runtime_stats.top_25/Runtime:count_avg/*" },
      { glob: "ChromiumPerf/*/v8.runtime_stats.top_25/Runtime:duration_avg/*" }
    ]
  }
  auto_triage: {
    rules: {
      match: {
        regex: "^ChromiumPerf.+"
      }
    }
  }
  auto_bisection: {
    rules: {
      match: {
        # Only auto-bisect story-specific anomalies.
        regex: "^ChromiumPerf(.*\/){3,}.+"
      }
      exclude: [
         # Do not auto-bisect metric-level summary measurements.
        { regex: "^ChromiumPerf(.*\/){3,}total:.+" }
      ]
    }
  }
  # Ported from 'V8-noisy'.
  anomaly_configs {
    min_relative_change: 0.1
    rules {
      match: [
        { glob: "internal.client.v8/*/v8/JSTests/*" },
        { glob: "internal.client.v8/*/v8/JSTests/*/*" }
      ]
    }
  }
  # Ported from 'V8-perf-stability'.
  anomaly_configs {
    min_segment_size: 3
    rules {
      match: [
        { glob: "internal.client.v8/*/v8/Infra/Stability/*" },
        { glob: "internal.client.v8/*/v8/Infra/Stability/*/*" }
      ]
    }
  }
  # Ported from 'V8-general'.
  # FIXME: Potentially simplify this?
  anomaly_configs {
    min_relative_change: 0.03
    rules {
      match: [
        { glob: "internal.client.v8/*/v8/AreWeFastYet/*" },
        { glob: "internal.client.v8/*/v8/BigNum/*" },
        { glob: "internal.client.v8/*/v8/BigNum/*/*" },
        { glob: "internal.client.v8/*/v8/Closure/*" },
        { glob: "internal.client.v8/*/v8/Compile/*" },
        { glob: "internal.client.v8/*/v8/Embenchen/*" },
        { glob: "internal.client.v8/*/v8/Emscripten/*" },
        { glob: "internal.client.v8/*/v8/JSBench/*" },
        { glob: "internal.client.v8/*/v8/JetStream-Ignition/*" },
        { glob: "internal.client.v8/*/v8/JetStream/*" },
        { glob: "internal.client.v8/*/v8/KrakenOrig-Ignition/*" },
        { glob: "internal.client.v8/*/v8/KrakenOrig-TF/*" },
        { glob: "internal.client.v8/*/v8/KrakenOrig/*" },
        { glob: "internal.client.v8/*/v8/LoadTime-Ignition/*" },
        { glob: "internal.client.v8/*/v8/LoadTime/*" },
        { glob: "internal.client.v8/*/v8/MDV/*" },
        { glob: "internal.client.v8/*/v8/Massive-TF/*" },
        { glob: "internal.client.v8/*/v8/Massive-TF/*/*" },
        { glob: "internal.client.v8/*/v8/Massive/*" },
        { glob: "internal.client.v8/*/v8/Massive/*/*" },
        { glob: "internal.client.v8/*/v8/Memory/*" },
        { glob: "internal.client.v8/*/v8/Micro/*" },
        { glob: "internal.client.v8/*/v8/Octane2.1-Harmony/*" },
        { glob: "internal.client.v8/*/v8/Octane2.1-Ignition/*" },
        { glob: "internal.client.v8/*/v8/Octane2.1-NoOpt/*" },
        { glob: "internal.client.v8/*/v8/Octane2.1-NoOpt/*/*" },
        { glob: "internal.client.v8/*/v8/Octane2.1-TF-pr/*" },
        { glob: "internal.client.v8/*/v8/Octane2.1-TF/*" },
        { glob: "internal.client.v8/*/v8/Octane2.1-TF/*/*" },
        { glob: "internal.client.v8/*/v8/Octane2.1-pr/*" },
        { glob: "internal.client.v8/*/v8/Octane2.1/*" },
        { glob: "internal.client.v8/*/v8/Octane2.1ES6/*" },
        { glob: "internal.client.v8/*/v8/Promises/*" },
        { glob: "internal.client.v8/*/v8/PunchStartup-Ignition/*" },
        { glob: "internal.client.v8/*/v8/PunchStartup/*" },
        { glob: "internal.client.v8/*/v8/RegExp/RegExp/*" },
        { glob: "internal.client.v8/*/v8/Ritz/*" },
        { glob: "internal.client.v8/*/v8/SIMDJS/*" },
        { glob: "internal.client.v8/*/v8/SixSpeed/*" },
        { glob: "internal.client.v8/*/v8/SixSpeed/*/*" },
        { glob: "internal.client.v8/*/v8/SunSpider-Ignition/*" },
        { glob: "internal.client.v8/*/v8/SunSpider-TF/*" },
        { glob: "internal.client.v8/*/v8/SunSpider/*" },
        { glob: "internal.client.v8/*/v8/SunSpiderGolem/*" },
        { glob: "internal.client.v8/*/v8/TraceurES6/*" },
        { glob: "internal.client.v8/*/v8/Wasm/*" },
        { glob: "internal.client.v8/*/v8/Wasm/*/*" },
        { glob: "internal.client.v8/*/v8/web-tooling-benchmark/*" },
        { glob: "internal.client.v8/x64/v8/RuntimeStats/Group-API/duration/*/*" },
        { glob: "internal.client.v8/x64/v8/RuntimeStats/Group-Callback/duration/*/*" },
        { glob: "internal.client.v8/x64/v8/RuntimeStats/Group-Compile/duration/*/*" },
        { glob: "internal.client.v8/x64/v8/RuntimeStats/Group-GC/duration/*/*" },
        { glob: "internal.client.v8/x64/v8/RuntimeStats/Group-IC/duration/*/*" },
        { glob: "internal.client.v8/x64/v8/RuntimeStats/Group-JavaScript/duration/*/*" },
        { glob: "internal.client.v8/x64/v8/RuntimeStats/Group-Optimize/duration/*/*" },
        { glob: "internal.client.v8/x64/v8/RuntimeStats/Group-Parse/duration/*/*" },
        { glob: "internal.client.v8/x64/v8/RuntimeStats/Group-Runtime/duration/*/*" },
        { glob: "internal.client.v8/x64/v8/RuntimeStats/Group-Total-V8/duration/*/*" }
      ]
    }
  }
}
subscriptions {
  name: "V8 Perf Sheriff (testing)"
  notification_email: "sergiyb@google.com"
  contact_email: "sergiyb@google.com"
  bug_components: ["Blink>JavaScript"]
  bug_labels: "Performance-Sheriff-V8"
  rules: {
    match: [
      { glob: "internal.client.v8/Nokia1/v8.testing/AreWeFastYet/*" },
      { glob: "internal.client.v8/Nokia1/v8.testing/BigNum/*" },
      { glob: "internal.client.v8/Nokia1/v8.testing/Compile/*" },
      { glob: "internal.client.v8/Nokia1/v8.testing/Embenchen/*" },
      { glob: "internal.client.v8/Nokia1/v8.testing/Emscripten/*" },
      { glob: "internal.client.v8/Nokia1/v8.testing/JSBench/*" },
      { glob: "internal.client.v8/Nokia1/v8.testing/JSTests/*" },
      { glob: "internal.client.v8/Nokia1/v8.testing/JetStream/*" },
      { glob: "internal.client.v8/Nokia1/v8.testing/KrakenOrig/*" },
      { glob: "internal.client.v8/Nokia1/v8.testing/Massive/*" },
      { glob: "internal.client.v8/Nokia1/v8.testing/Octane2.1-NoOpt/*" },
      { glob: "internal.client.v8/Nokia1/v8.testing/Octane2.1-TF/*" },
      { glob: "internal.client.v8/Nokia1/v8.testing/Octane2.1/*" },
      { glob: "internal.client.v8/Nokia1/v8.testing/Promises/*" },
      { glob: "internal.client.v8/Nokia1/v8.testing/RegExp/RegExp/*" },
      { glob: "internal.client.v8/Nokia1/v8.testing/Ritz/*" },
      { glob: "internal.client.v8/Nokia1/v8.testing/SixSpeed/*" },
      { glob: "internal.client.v8/Nokia1/v8.testing/SunSpider/*" }
    ]
  }
}
subscriptions {
  name: "V8 Wasm Perf Sheriff"
  notification_email: "wasm-perf@google.com"
  contact_email: "wasm-perf@google.com"
  rules: {
    match: [
      { glob: "internal.client.v8/*/v8/Blazor/*" },
      { glob: "internal.client.v8/*/v8/Embenchen/*" },
      { glob: "internal.client.v8/*/v8/Emscripten/*" },
      { glob: "internal.client.v8/*/v8/JetStream-wasm/*" },
      { glob: "internal.client.v8/*/v8/Spec2k6/*/CodeSize" },
      { glob: "internal.client.v8/*/v8/Spec2k6/*/Compile" },
      { glob: "internal.client.v8/*/v8/Spec2k6/*/RelocSize" },
      { glob: "internal.client.v8/*/v8/Spec2k6/*/Run" },
      { glob: "internal.client.v8/*/v8/Unity/*/CodeSize" },
      { glob: "internal.client.v8/*/v8/Unity/*/Compile" },
      { glob: "internal.client.v8/*/v8/Unity/*/Instantiate" },
      { glob: "internal.client.v8/*/v8/Unity/*/RelocSize" },
      { glob: "internal.client.v8/*/v8/Unity/*/Runtime" },
      { glob: "internal.client.v8/*/v8/Wasm/AngryBots/*" },
      { glob: "internal.client.v8/*/v8/Wasm/AngryBots-Async/Compile" },
      { glob: "internal.client.v8/*/v8/Wasm/Epic-Liftoff-Async/*" },
      { glob: "internal.client.v8/*/v8/Wasm/Epic-Liftoff/*" },
      { glob: "internal.client.v8/*/v8/Wasm/Epic-Turbofan-Async/*" },
      { glob: "internal.client.v8/*/v8/Wasm/Epic-Turbofan/*" },
      { glob: "internal.client.v8/*/v8/Wasm/Import-Export-Wrappers-Microbench/*" },
      { glob: "internal.client.v8/*/v8/Wasm-SIMD/skcms/*" },
      { glob: "internal.client.v8/*/v8/Wasm-SIMD/simd-micro/*" },
      { glob: "internal.client.v8/*/v8/Wasm-SIMD/meet-segmentation-bench/*" }
    ]
  }
}
                                     """)
    app = service.CreateApp({
        'environ': {
            'GOOGLE_CLOUD_PROJECT': 'chromeperf',
            'GAE_SERVICE': 'sheriff-config',
        },
        'datastore_client': datastore.Client(project='chromeperf'),
        'http': HttpMockSequenceWithDiscovery([({
            'status': '200'
        }, config)]),
    })

    client = app.test_client()
    response = client.get(
        '/configs/update', headers={'X-Forwarded-Proto': 'https'})
    self.assertEqual(response.status_code, 200)

    def Test(path, triaged, bisected, anomalies):
      response = client.post(
          '/subscriptions/match',
          json={
              'path': path,
              'stats': ['PCT_99'],
              'metadata': {
                  'units': 'SomeUnit',
                  'master': 'Master',
                  'bot': 'Bot',
                  'benchmark': 'Test',
                  'metric_parts': ['Metric', 'Something'],
              }
          },
          headers={'X-Forwarded-Proto': 'https'})
      self.assertEqual(response.status_code, 200)
      response_proto = response.get_json()
      expected_sub = {
          'name': 'V8 Perf Sheriff',
          'notification_email': "v8-perf-alerts@google.com",
          'contact_email': 'v8-perf-alerts@google.com',
          'bug_labels': ['Performance-Sheriff-V8'],
          'bug_components': ['Blink>JavaScript'],
          'auto_triage': {
              'enable': triaged
          },
          'auto_bisection': {
              'enable': bisected
          },
          'rules': {},
          'visibility': 'PUBLIC',
      }
      if anomalies:
        expected_sub['anomaly_configs'] = [{
            'min_relative_change': 0.1,
            'rules': {}
        }]

      expected = {
          'subscriptions': [{
              'config_set': 'projects/v8',
              'revision': '0123456789abcdef',
              'subscription': expected_sub
          }]
      }
      self.assertDictEqual(response_proto, expected)

    Test('ChromiumPerf/*/speedometer2/*/Speedometer2', True, True, False)
    Test(
        'internal.client.v8/Atom_x64/v8/JSTests/ArraySortDifferentLengths/Sorted1000',
        False, False, True)

  def testPollAndMatchTriageBisect(self):
    client = self.app.test_client()
    response = client.get(
        '/configs/update', headers={'X-Forwarded-Proto': 'https'})
    self.assertEqual(response.status_code, 200)

    def Test(path, triaged, bisected):
      response = client.post(
          '/subscriptions/match',
          json={
              'path': 'Master/Bot/Test/Metric/Something_' + path,
              'stats': ['PCT_99'],
              'metadata': {
                  'units': 'SomeUnit',
                  'master': 'Master',
                  'bot': 'Bot',
                  'benchmark': 'Test',
                  'metric_parts': ['Metric', 'Something'],
              }
          },
          headers={'X-Forwarded-Proto': 'https'})
      self.assertEqual(response.status_code, 200)
      response_proto = response.get_json()
      self.assertDictEqual(
          response_proto, {
              'subscriptions': [{
                  'config_set': 'projects/other_project',
                  'revision': '0123456789abcdff',
                  'subscription': {
                      'name': 'Expected 1',
                      'monorail_project_id': 'non-chromium',
                      'contact_email': 'expected-1@example.com',
                      'bug_labels': ['Some-Label'],
                      'bug_components': ['Some>Component'],
                      'auto_triage': {
                          'enable': triaged
                      },
                      'auto_bisection': {
                          'enable': bisected
                      },
                      'rules': {},
                  }
              }]
          })

    Test('Triage_Bisect', True, True)
    Test('NoTriage_Bisect', False, False)
    Test('Triage_NoBisect', True, False)

  def testPollAndMatchMultiple(self):
    client = self.app.test_client()
    response = client.get(
        '/configs/update', headers={'X-Forwarded-Proto': 'https'})
    self.assertEqual(response.status_code, 200)
    response = client.post(
        '/subscriptions/match',
        json={
            'path': 'project/platform/not-important/memory_peak',
            'stats': ['PCT_99'],
            'metadata': {
                'units': 'SomeUnit',
                'master': 'Master',
                'bot': 'Bot',
                'benchmark': 'Test',
                'metric_parts': ['Metric', 'Something'],
            }
        },
        headers={'X-Forwarded-Proto': 'https'})
    self.assertEqual(response.status_code, 200)
    response_proto = response.get_json()
    self.assertDictEqual(
        response_proto, {
            'subscriptions': [{
                'config_set': 'projects/project',
                'revision': '0123456789abcdef',
                'subscription': {
                    'name': 'Config 1',
                    'contact_email': 'config-1@example.com',
                    'bug_labels': ['Some-Label'],
                    'bug_components': ['Some>Component'],
                    'auto_triage': {
                        'enable': False
                    },
                    'auto_bisection': {
                        'enable': False
                    },
                    'rules': {},
                }
            }, {
                'config_set': 'projects/project',
                'revision': '0123456789abcdef',
                'subscription': {
                    'name': 'Config 2',
                    'contact_email': 'config-2@example.com',
                    'bug_labels': ['Some-Label'],
                    'bug_components': ['Some>Component'],
                    'auto_triage': {
                        'enable': False
                    },
                    'auto_bisection': {
                        'enable': False
                    },
                    'rules': {},
                }
            }]
        })

  def testPollAndMatchPostFilter(self):
    client = self.app.test_client()
    response = client.get(
        '/configs/update', headers={'X-Forwarded-Proto': 'https'})
    self.assertEqual(response.status_code, 200)
    response = client.post(
        '/subscriptions/match',
        json={
            'path': 'Master/Bot/Test/Metric/Something_PostFilter',
            'stats': ['PCT_99'],
            'metadata': {
                'units': 'SomeUnit',
                'master': 'Master',
                'bot': 'Bot',
                'benchmark': 'Test',
                'metric_parts': ['Metric', 'Something'],
            }
        },
        headers={'X-Forwarded-Proto': 'https'})
    self.assertEqual(response.status_code, 404)

  def testPollAndMatchWithAnomalyConfig(self):
    client = self.app.test_client()
    response = client.get(
        '/configs/update', headers={'X-Forwarded-Proto': 'https'})
    self.assertEqual(response.status_code, 200)
    response = client.post(
        '/subscriptions/match',
        json={
            'path': 'Master/Bot/Test/Metric/WithAnomalyConfig',
            'stats': ['PCT_99'],
            'metadata': {
                'units': 'SomeUnit',
                'master': 'Master',
                'bot': 'Bot',
                'benchmark': 'Test',
                'metric_parts': ['Metric', 'WithAnomalyConfig'],
            }
        },
        headers={'X-Forwarded-Proto': 'https'})
    self.assertEqual(response.status_code, 200)
    response_proto = response.get_json()
    self.assertEqual(
        response_proto, {
            'subscriptions': [{
                'config_set': mock.ANY,
                'revision': mock.ANY,
                'subscription': {
                    'name': 'Expected 1',
                    'monorail_project_id': 'non-chromium',
                    'contact_email': 'expected-1@example.com',
                    'bug_labels': ['Some-Label'],
                    'bug_components': ['Some>Component'],
                    'auto_triage': {
                        'enable': False
                    },
                    'auto_bisection': {
                        'enable': False
                    },
                    'rules': {},
                    'anomaly_configs': [mock.ANY],
                }
            }]
        })

  def testPollAndMatchNone(self):
    client = self.app.test_client()
    response = client.get(
        '/configs/update', headers={'X-Forwarded-Proto': 'https'})
    self.assertEqual(response.status_code, 200)
    response = client.post(
        '/subscriptions/match',
        json={
            'path': 'NoMatch/Nothing/not-important/not-monitored',
            'stats': ['PCT_99'],
            'metadata': {
                'units': 'SomeUnit',
                'master': 'Master',
                'bot': 'Bot',
                'benchmark': 'Test',
                'metric_parts': ['Metric', 'Something'],
            }
        },
        headers={'X-Forwarded-Proto': 'https'})
    self.assertEqual(response.status_code, 404)

  def testMatchInvalidRequest(self):
    client = self.app.test_client()
    response = client.post(
        '/subscriptions/match',
        json={
            'invalid_key': 'foo',
            'path': 'NoMatch/Nothing/not-important/not-monitored',
            'stats': ['PCT_99'],
            'metadata': {
                'units': 'SomeUnit',
                'master': 'Master',
                'bot': 'Bot',
                'benchmark': 'Test',
                'metric_parts': ['Metric', 'Something'],
            }
        },
        headers={'X-Forwarded-Proto': 'https'})
    self.assertEqual(response.status_code, 400)

  def testListSubscriptions(self):
    app = service.CreateApp({
        'environ': {
            'GOOGLE_CLOUD_PROJECT': 'chromeperf',
            'GAE_SERVICE': 'sheriff-config',
        },
        'datastore_client':
            datastore.Client(project='chromeperf'),
        'http':
            HttpMockSequenceWithDiscovery([({
                'status': '200'
            }, self.sample_config), ({
                'status': '200'
            }, '{ "is_member": true }'),
                                           ({
                                               'status': '200'
                                           }, '{ "is_member": false }')]),
    })
    client = app.test_client()
    response = client.get(
        '/configs/update', headers={'X-Forwarded-Proto': 'https'})
    self.assertEqual(response.status_code, 200)
    response = client.post(
        '/subscriptions/list',
        json={'identity_email': 'any@internal.com'},
        headers={'X-Forwarded-Proto': 'https'})
    self.assertEqual(response.status_code, 200)
    self.assertDictEqual(
        response.get_json(), {
            'subscriptions': [{
                'config_set': 'projects/project',
                'revision': '0123456789abcdef',
                'subscription': {
                    'name': 'Config 1',
                    'contact_email': 'config-1@example.com',
                    'bug_labels': ['Some-Label'],
                    'bug_components': ['Some>Component'],
                    'auto_triage': {
                        'enable': False
                    },
                    'auto_bisection': {
                        'enable': False
                    },
                    'rules': {},
                }
            }, {
                'config_set': 'projects/project',
                'revision': '0123456789abcdef',
                'subscription': {
                    'name': 'Config 2',
                    'contact_email': 'config-2@example.com',
                    'bug_labels': ['Some-Label'],
                    'bug_components': ['Some>Component'],
                    'auto_triage': {
                        'enable': False
                    },
                    'auto_bisection': {
                        'enable': False
                    },
                    'rules': {},
                }
            }, {
                'config_set': 'projects/other_project',
                'revision': '0123456789abcdff',
                'subscription': {
                    'name': 'Expected 1',
                    'monorail_project_id': 'non-chromium',
                    'contact_email': 'expected-1@example.com',
                    'bug_labels': ['Some-Label'],
                    'bug_components': ['Some>Component'],
                    'auto_triage': {
                        'enable': False
                    },
                    'auto_bisection': {
                        'enable': False
                    },
                    'rules': {},
                }
            }]
        })
    response = client.post(
        '/subscriptions/list',
        json={'identity_email': 'any@public.com'},
        headers={'X-Forwarded-Proto': 'https'})
    self.assertEqual(response.status_code, 200)
    self.assertDictEqual(response.get_json(), {})

  def testPollAndWarmup(self):
    client = self.app.test_client()
    response = client.get(
        '/configs/update', headers={'X-Forwarded-Proto': 'https'})
    self.assertEqual(response.status_code, 200)
    response = client.get('/warmup', headers={'X-Forwarded-Proto': 'https'})
    self.assertEqual(response.status_code, 200)


class LuciContentChangesTest(unittest.TestCase):

  def setUp(self):
    with open(
        'tests/sample-configs-get_project_configs.json') as sample_config_file:
      self.sample_config = sample_config_file.read()
    self.maxDiff = None

  def AssertProjectConfigSet1Holds(self, client, expected_code):
    response = client.post(
        '/subscriptions/match',
        json={
            'path': 'Master/Bot/Test/Metric/Something',
            'stats': ['PCT_99'],
            'metadata': {
                'units': 'SomeUnit',
                'master': 'Master',
                'bot': 'Bot',
                'benchmark': 'Test',
                'metric_parts': ['Metric', 'Something'],
            }
        },
        headers={'X-Forwarded-Proto': 'https'})
    self.assertEqual(response.status_code, expected_code)
    if expected_code != 200:
      return
    response_proto = response.get_json()
    self.assertDictEqual(
        response_proto, {
            'subscriptions': [{
                'config_set': 'projects/other_project',
                'revision': '0123456789abcdff',
                'subscription': {
                    'name': 'Expected 1',
                    'monorail_project_id': 'non-chromium',
                    'contact_email': 'expected-1@example.com',
                    'bug_labels': ['Some-Label'],
                    'bug_components': ['Some>Component'],
                    'auto_triage': {
                        'enable': False
                    },
                    'auto_bisection': {
                        'enable': False
                    },
                    'rules': {},
                }
            }]
        })

  def AssertProjectConfigSet2Holds(self, client, expected_code):
    response = client.post(
        '/subscriptions/match',
        json={
            'path': 'project/platform/not-important/memory_peak',
            'stats': ['PCT_99'],
            'metadata': {
                'units': 'SomeUnit',
                'master': 'Master',
                'bot': 'Bot',
                'benchmark': 'Test',
                'metric_parts': ['Metric', 'Something'],
            }
        },
        headers={'X-Forwarded-Proto': 'https'})
    self.assertEqual(response.status_code, expected_code)
    if expected_code != 200:
      return
    response_proto = response.get_json()
    self.assertDictEqual(
        response_proto, {
            'subscriptions': [{
                'config_set': 'projects/project',
                'revision': '0123456789abcdef',
                'subscription': {
                    'name': 'Config 1',
                    'contact_email': 'config-1@example.com',
                    'bug_labels': ['Some-Label'],
                    'bug_components': ['Some>Component'],
                    'auto_triage': {
                        'enable': False
                    },
                    'auto_bisection': {
                        'enable': False
                    },
                    'rules': {},
                }
            }, {
                'config_set': 'projects/project',
                'revision': '0123456789abcdef',
                'subscription': {
                    'name': 'Config 2',
                    'contact_email': 'config-2@example.com',
                    'bug_labels': ['Some-Label'],
                    'bug_components': ['Some>Component'],
                    'auto_triage': {
                        'enable': False
                    },
                    'auto_bisection': {
                        'enable': False
                    },
                    'rules': {},
                }
            }]
        })

  def testPollAndEmptyConfigs(self):
    app = service.CreateApp({
        'environ': {
            'GOOGLE_CLOUD_PROJECT': 'chromeperf',
            'GAE_SERVICE': 'sheriff-config',
        },
        'datastore_client':
            datastore.Client(project='chromeperf'),
        'http':
            HttpMockSequenceWithDiscovery([({
                'status': '200'
            }, '{}')])
    })
    client = app.test_client()
    response = client.get(
        '/configs/update', headers={'X-Forwarded-Proto': 'https'})
    self.assertEqual(response.status_code, 200)

  def testPollConfigAddsAndRemoves(self):
    with open('tests/sample-configs-get_project_configs_reduced.json'
             ) as sample_config_file:
      sample_config_reduced = sample_config_file.read()
    app = service.CreateApp({
        'environ': {
            'GOOGLE_CLOUD_PROJECT': 'chromeperf',
            'GAE_SERVICE': 'sheriff-config',
        },
        'datastore_client':
            datastore.Client(project='chromeperf'),
        'http':
            HttpMockSequenceWithDiscovery([({
                'status': '200'
            }, self.sample_config), ({
                'status': '200'
            }, sample_config_reduced)]),
    })

    # Step 1: Get one configuration with two config sets.
    client = app.test_client()
    response = client.get(
        '/configs/update', headers={'X-Forwarded-Proto': 'https'})
    self.assertEqual(response.status_code, 200)

    self.AssertProjectConfigSet1Holds(client, 200)
    self.AssertProjectConfigSet2Holds(client, 200)

    # Step 2: Get another configuration, this time with just one config set.
    response = client.get(
        '/configs/update', headers={'X-Forwarded-Proto': 'https'})
    self.assertEqual(response.status_code, 200)

    # Update doesn't take effect because of caching
    self.AssertProjectConfigSet1Holds(client, 200)
    self.AssertProjectConfigSet2Holds(client, 200)

    # mocking utils.Time to invalid caching
    with mock.patch('utils.Time') as mock_time:
      mock_time.method.return_value = (time.time() + 60)
      self.AssertProjectConfigSet1Holds(client, 404)
      self.AssertProjectConfigSet2Holds(client, 200)

  def testInvalidContentPulled(self):
    subscription = """
subscriptions: {
  name: "Missing Email"
  bug_labels: ["Some-Label"]
  bug_components: ["Some>Component"]
  patterns: [{glob: "project/**"}]
}"""
    invalid_content = """
{
  "configs": [
    {
      "url": "https://example.com/p/s/+/0123456789abcde/chromeperf-sheriff.cfg",
      "content": "%s",
      "content_hash": "v1:somehash",
      "config_set": "projects/project",
      "revision": "0123456789abcdef"
    }
  ]
}""" % (base64.standard_b64encode(bytearray(subscription, 'utf-8')).decode(),)
    app = service.CreateApp({
        'environ': {
            'GOOGLE_CLOUD_PROJECT': 'chromeperf',
            'GAE_SERVICE': 'sheriff-config',
        },
        'datastore_client':
            datastore.Client(project='chromeperf'),
        'http':
            HttpMockSequenceWithDiscovery([({
                'status': '200'
            }, invalid_content), ({
                'status': '200'
            }, self.sample_config), ({
                'status': '200'
            }, invalid_content)]),
    })
    client = app.test_client()

    # Step 1: Get an invalid config.
    response = client.get(
        '/configs/update', headers={'X-Forwarded-Proto': 'https'})
    self.assertEqual(response.status_code, 500)

    # Step 2: Get a config that's valid.
    response = client.get(
        '/configs/update', headers={'X-Forwarded-Proto': 'https'})
    self.assertEqual(response.status_code, 200)

    self.AssertProjectConfigSet1Holds(client, 200)
    self.AssertProjectConfigSet2Holds(client, 200)

    # Step 3: Get a config that's invalid, but ensure that the valid config
    # holds.
    response = client.get(
        '/configs/update', headers={'X-Forwarded-Proto': 'https'})
    self.assertEqual(response.status_code, 500)
    self.AssertProjectConfigSet1Holds(client, 200)
    self.AssertProjectConfigSet2Holds(client, 200)
