# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import datetime
import json
import unittest
import uuid

from google.appengine.ext import ndb

from dashboard.api import api_auth
from dashboard.api import warmup
from dashboard.common import testing_common
from dashboard.models import anomaly
from dashboard.models import graph_data
from dashboard.models import histogram
from dashboard.models import sheriff
from tracing.value.diagnostics import reserved_infos


class WarmupTest(testing_common.TestCase):

  def setUp(self):
    super(WarmupTest, self).setUp()
    self.SetUpApp([('/_ah/warmup', warmup.WarmupHandler)])
    self.SetCurrentClientIdOAuth(api_auth.OAUTH_CLIENT_ID_WHITELIST[0])
    sheriff.Sheriff(
        id='Taylor',
        email=testing_common.INTERNAL_USER.email()).put()
    self.SetCurrentUserOAuth(None)

  def testClear(self):
    XXX

  def testFakeData(self):
    XXX

  def testUntriage(self):
    XXX
