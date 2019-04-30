# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# Support python3
from __future__ import absolute_import

from flask import Flask, request, jsonify

from dashboard.sheriff_config import validator

def CreateApp(test_config=None):
  """Factory for Flask App configuration."""
  app = Flask(__name__, instance_relative_config=True)

  if test_config is None:
    version = '0.1'
    domain = 'sheriff-config-dot-chromeperf.appspot.com'
  else:
    version = test_config.get('version', 'test')
    domain = test_config.get('domain', 'test-domain')

  @app.route('/validate', methods=['POST'])
  def Validate():  # pylint: disable=unused-variable
    validation_request = request.get_json()
    if validation_request is None:
      return u'Invalid request.', 400
    for member in ('config_set', 'path', 'content'):
      if member not in validation_request:
        return u'Missing \'%s\' member in request.' % (member), 400
    try:
      _ = validator.Validate(validation_request['content'])
    except validator.Error as error:
      return jsonify({
          'messages': [{
              'path': validation_request['path'],
              'severity': 'ERROR',
              'text': '%s' % (error)
          }]
      })
    return jsonify({})


  @app.route('/service-metadata')
  def ServiceMetadata():  # pylint: disable=unused-variable
    return jsonify({
        'version': version,
        'validation': {
            'patterns': [{
                'config_set': 'regex:.*',
                'path': 'regex:chromeperf-sheriff.cfg'
            }],
            'url': '%s/validate' % (domain)
        }
    })

  return app
