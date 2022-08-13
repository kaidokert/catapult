# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Base class for request handlers that display charts."""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import json

from dashboard.common import request_handler
from dashboard.common import utils
from dashboard import revision_info_client

if utils.IsRunningFlask():
  """Base class for requests which display a chart."""

  def ChartHandlerRenderHtml(template_file, template_values, status=200):
    """Fills in template values for pages that show charts."""
    template_values.update(_ChartHandlerGetChartValues())
    template_values['revision_info'] = json.dumps(
        template_values['revision_info'])
    return request_handler.RequestHandlerRenderHtml(template_file,
                                                    template_values, status)

  def ChartHandlerRenderStaticHtml(filename):
    return request_handler.RequestHandlerRenderStaticHtml(filename)

  def ChartHandlerGetDynamicVariables(self, template_values, request_path=None):
    template_values.update(_ChartHandlerGetChartValues)
    return request_handler.RequestHandlerGetDynamicVariable(
        template_values, request_path)

  def _ChartHandlerGetChartValues():
    return {'revision_info': revision_info_client.GetRevisionInfoConfig()}

else:

  class ChartHandler(request_handler.RequestHandler):
    """Base class for requests which display a chart."""

    def RenderHtml(self, template_file, template_values, status=200):
      """Fills in template values for pages that show charts."""
      template_values.update(self._GetChartValues())
      template_values['revision_info'] = json.dumps(
          template_values['revision_info'])
      # TODO(https://crbug.com/1262292): Change to super() after Python2 trybots retire.
      # pylint: disable=super-with-arguments
      return super(ChartHandler, self).RenderHtml(template_file,
                                                  template_values, status)

    def GetDynamicVariables(self, template_values, request_path=None):
      template_values.update(self._GetChartValues())
      # TODO(https://crbug.com/1262292): Change to super() after Python2 trybots retire.
      # pylint: disable=super-with-arguments
      super(ChartHandler, self).GetDynamicVariables(template_values,
                                                    request_path)

    def _GetChartValues(self):
      return {'revision_info': revision_info_client.GetRevisionInfoConfig()}
