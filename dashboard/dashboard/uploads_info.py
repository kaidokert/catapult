# Copyright 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""URL endpoint for getting information about histogram upload proccess."""
from __future__ import absolute_import

import logging

from dashboard.api import api_request_handler
from dashboard.models import upload_completion_token


class UploadInfoHandler(api_request_handler.ApiRequestHandler):

  def _CheckUser(self):
    self._CheckIsInternalUser()

  def _GenerateResponse(self, token, measurements=None):
    measurements = measurements or []
    result = {
        'token': token.key.id(),
        'file': token.temporary_staging_file_path,
        'created': str(token.creation_time),
        'lastUpdated': str(token.update_time),
        'state': upload_completion_token.StateToString(token.state),
    }
    if measurements:
      result['measurements'] = []
    for measurement in measurements:
      result['measurements'].append({
          'name': measurement.key.id(),
          'state': upload_completion_token.StateToString(measurement.state),
      })
    return result

  def Get(self, *args):
    assert len(args) == 1

    token_id = args[0]
    token = upload_completion_token.Token.get_by_id(token_id)
    if token is None:
      logging.info('Upload completion token not found. Token id: %s', token_id)
      raise api_request_handler.NotFoundError

    measurements = token.GetMeasurements()
    return self._GenerateResponse(token, measurements)
