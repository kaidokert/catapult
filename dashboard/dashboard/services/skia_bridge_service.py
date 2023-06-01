# Copyright 2023 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import
from datetime import datetime
from dashboard.common import utils
from dashboard.models import graph_data
from dashboard.services import request

import logging
import json


SKIA_UPLOAD_URL = 'https://skia-bridge-dot-chromeperf.appspot.com/data/upload_queue'
if utils.IsStagingEnvironment():
  SKIA_UPLOAD_URL = 'https://skia-bridge-dot-chromeperf-stage.uc.r.appspot.com/data/upload_queue'


def SendRowsForSkiaUpload(rows, parent_test):
  if rows is None or len(rows) == 0:
    raise ValueError('Rows cannot be empty')

  if parent_test is None:
    raise ValueError('Parent test cannot be None')

  row_data = [ConvertRowForSkiaUpload(row, parent_test) for row in rows]
  request_data = {'rows': row_data}

  logging.info('Sending %i rows to skia bridge', len(row_data))
  response = request.Request(
      SKIA_UPLOAD_URL,
      headers={'Content-Type': 'application/json'},
      method='POST',
      body=json.dumps(request_data),
      use_auth=True)
  logging.info('Skia Bridge Response: %s', response)


def ConvertRowForSkiaUpload(row: graph_data.Row,
    parent_test: graph_data.TestMetadata):
  exact_row_properties = [
      'r_commit_pos',
      'timestamp',
      'd_count',
      'd_max',
      'd_min',
      'd_sum',
      'd_std',
      'd_avg',
      'value',
      'error',
      'a_benchmark_config',
      'a_build_uri',
      'a_tracing_uri',
      'a_stdio_uri',
      'a_bot_id',
      'a_os_detail_vers',
      'a_default_rev',
      'a_jobname',
      'r_chromium',
      'r_v8_rev',
      'r_webrtc_git',
      'r_chrome_version',
  ]

  def CopyItemAttrToDict(obj, properties, attr_is_property=False):
    prop_dict = {}
    for prop in properties:
      if hasattr(obj, prop):
        attr_value = getattr(obj, prop)
        if isinstance(attr_value, datetime):
          val = str(attr_value()) if attr_is_property else str(attr_value)
        else:
          val = attr_value() if attr_is_property else attr_value

        prop_dict[prop] = val
    return prop_dict

  row_item = CopyItemAttrToDict(row, exact_row_properties)
  test_item = {}
  test_item['test_path'] = utils.TestPath(parent_test.key)
  test_item['master_name'] = parent_test.master_name
  test_item['bot_name'] = parent_test.bot_name
  test_item['suite_name'] = parent_test.suite_name
  test_item['internal_only'] = parent_test.internal_only
  test_item['improvement_direction'] = parent_test.improvement_direction
  test_item['units'] = parent_test.units
  test_item['test_part1_name'] = parent_test.test_part1_name
  test_item['test_part2_name'] = parent_test.test_part2_name
  test_item['test_part3_name'] = parent_test.test_part3_name
  test_item['test_part4_name'] = parent_test.test_part4_name
  test_item['test_part5_name'] = parent_test.test_part5_name

  row_item['parent_test'] = test_item

  return row_item
