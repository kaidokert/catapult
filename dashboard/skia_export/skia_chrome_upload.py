# Copyright 2023 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Entry-point for pipeline which uploads Datastore Row entities to Skia Perf GCS.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from skia_export import skia_pipeline

CHROMEPERF_PROPERTY_MAP = {
  'masters': ['ChromeFYIInternal', 'ChromiumAndroid', 'ChromiumChrome',
    'ChromiumChromiumos', 'ChromiumClang', 'ChromiumFuchsia', 'ChromiumGPUFYI',
    'ChromiumPerf', 'ChromiumPerfFyi', 'ChromiumPerfPGO', 'TryServerChromiumFuchsia',
    'TryserverChromiumChromiumOS', 'ChromiumFuchsiaFyi', 'TryserverChromiumAndroid',
    'ChromiumAndroidFyi', 'ChromiumFYI', 'ChromiumPerfFyi.all'],
  'public_bucket_name': 'chrome-perf-public',
  'internal_bucket_name': 'chrome-perf-non-public',
  'ingest_folder': 'ingest'
}

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  skia_pipeline.main(properties=CHROMEPERF_PROPERTY_MAP)
