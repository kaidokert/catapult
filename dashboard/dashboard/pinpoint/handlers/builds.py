# Copyright 2024 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import logging

from flask import request
from dashboard.common import bot_configurations
from dashboard.api import api_request_handler
from dashboard.api import api_auth
from dashboard.common import cloud_metric
from dashboard.common import utils
from dashboard.pinpoint.models.change import Commit
from dashboard.services import buildbucket_service


def _CheckUser():
  if utils.IsDevAppserver():
    return
  api_auth.Authorize()
  if not utils.IsTryjobUser():
    raise api_request_handler.ForbiddenError()


# @api_request_handler.RequestHandlerDecoratorFactory(_CheckUser)
@cloud_metric.APIMetric("pinpoint", "/api/builds/get")
def RecentBuildsGet(bot_configuration: str):
  logging.info('Trying to get most recent builds for %s', bot_configuration)
  bot_config = bot_configurations.Get(bot_configuration)
  logging.info('Bot config: %s', bot_config)
  builds_response = buildbucket_service.GetBuilds('chrome', 'try', bot_config['builder'])
  return builds_response