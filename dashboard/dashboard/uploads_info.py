# Copyright 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""URL endpoint for getting information about histogram upload proccess."""
from __future__ import absolute_import

import logging

from dashboard.api import api_request_handler
from dashboard.models import histogram
from dashboard.models import upload_completion_token
from tracing.value import histogram as histogram_module
from tracing.value.diagnostics import diagnostic_ref


class UploadInfoHandler(api_request_handler.ApiRequestHandler):
  """Request handler to get information about upload completion tokens."""

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
      info = {
          'name': measurement.key.id(),
          'state': upload_completion_token.StateToString(measurement.state),
          'monitored': measurement.monitored,
          'lastUpdated': str(measurement.update_time),
      }
      if measurement.histogram is not None:
        histogram_entity = measurement.histogram.get()
        attached_histogram = histogram_module.Histogram.FromDict(
            histogram_entity.data)
        info['diagnostics'] = []
        for name, diagnostic in attached_histogram.diagnostics.items():
          if not isinstance(diagnostic, diagnostic_ref.DiagnosticRef):
            info['diagnostics'].append({
                'name': name,
                'value': diagnostic.AsDict()
            })
          else:
            original_diagnostic_guid = diagnostic.guid
            original_diagnostic = histogram.SparseDiagnostic.get_by_id(
                original_diagnostic_guid)
            info['diagnostics'].append({
                'name': name,
                'value': {
                    'type': 'DiagnosticRef',
                    'original_value': original_diagnostic.data
                }
            })

      result['measurements'].append(info)
    return result

  def Get(self, *args):
    """Returns json, that describes state of the token.

    Can be called by get request to /uploads/<token_id> or
    /uploads/<token_id>/full_info.

    Response is json of the form:
    {
      "token": "...",
      "file": "...",
      "created": "...",
      "lastUpdated": "...",
      "state": "PENDING|PROCESSING|FAILED|COMPLETED",
      "measurements": [
        {
          "name": "...",
          "state": "PROCESSING|FAILED|COMPLETED",
          "monitored": True|False,
          "lastUpdated": "...",
          "diagnostics": [
            {
              "name": "...",
              "value": {
                "type": "GenericSet|Breakdown|RelatedEventSet|DateRange|...",
                "guid": "...",
                ...
              }
            },
            {
              "name": "...",
              "value": {
                "type": "DiagnosticRef",
                "original_value": {
                  "type": "GenericSet|Breakdown|RelatedEventSet|DateRange|...",
                  "guid": "...",
                  ...
                }
              }
            },
            ...
          ]
        },
        ...
      ]
    }
    Description of the fields:
      - token: Token id from the request.
      - file: Temporary staging file path, where /add_histogram request data is
        stored during the PENDING stage. For more information look at
        /add_histogram api.
      - created: Date and time of creation.
      - lastUpdated: Date and time of last update.
      - state: Aggregated state of the token and all associated measurements.
      - measurements: List of jsons, that describes measurements, associated
        with the token. If there is no such measurements the field will be
        absent. The field will be present only if /uploads/<id>/full_info api
        was called.
        - name: The path  of the measurement. It is a fully-qualified path in
          the Dashboard.
        - state: State of the measurement.
        - monitored: A boolean indicating whether the path is monitored by a
          sheriff configuration.
        - lastUpdated: Date and time of last update.
        - diagnostics: List of diagnostics, associated to the histogram, that
          is represented by the measurement. This field will be present in
          response only after the histogram has been added to Datastore.
          - name: Name of the diagnostic.
          - value: Json representation of the diagnostic. Defined by
            tracing.value.diagnostics.diagnostic.Diagnostic.AsDict().
            Exception is diagnostic of type DiagnosticRef. For such diagnostic
            the value will contain "original_value" field, that contains the
            AsDict() representation of a refferenced diagnostic.
            - type: Type of the diagnostic. Always present in the value.

    Meaning of some common error codes:
      - 403: The user is not authorized to check on the status of an upload.
      - 404: Token could not be found. It is either expired or the token is
        invalid.
    """
    assert len(args) == 2

    token_id = args[0]
    token = upload_completion_token.Token.get_by_id(token_id)
    if token is None:
      logging.error('Upload completion token not found. Token id: %s', token_id)
      raise api_request_handler.NotFoundError

    measurements = None
    # /uploads/<token_id>/full_info api was called.
    is_full_info = args[1] is not None
    if is_full_info:
      measurements = token.GetMeasurements()
    return self._GenerateResponse(token, measurements)
