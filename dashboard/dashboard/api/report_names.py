# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from dashboard.api import api_request_handler
# pylint: disable=unused-import
# Module imported for its side effects: registering static report templates.
from dashboard.common import system_health_report
# pylint: enable=unused-import
from dashboard.models import report_template


class ReportNamesHandler(api_request_handler.ApiRequestHandler):

  def _AllowAnonymous(self):
    return True

  def AuthorizedPost(self):
    return report_template.List()
