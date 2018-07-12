# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from dashboard.api import api_request_handler
from dashboard.models import report_template


class ReportNamesHandler(api_request_handler.ApiRequestHandler):

  def _AllowAnonymous(self):
    return True

  def AuthorizedPost(self):
    templates = report_template.ReportTemplate.query().fetch()
    templates = [
        {
            'id': template.key.id(),
            'name': template.name,
            'modified': template.modified.isoformat(),
        }
        for template in templates]
    return sorted(templates, key=lambda d: d['name'])
