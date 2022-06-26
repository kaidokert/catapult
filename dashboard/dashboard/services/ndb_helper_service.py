# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Encapsulates a simplistic interface to the buildbucket service."""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from dashboard.services import request

BASE_URL = 'https://ndb-helper-dot-chromeperf-stage.uc.r.appspot.com/'


def GetJob(job_id, query_string):
  return request.RequestJson(
      BASE_URL + 'api/job/' + job_id + '?' + query_string, method='GET')
