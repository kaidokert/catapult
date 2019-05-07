# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""API Wrapper for the luci-config service."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from googleapiclient.discovery import build

# The Root of the luci-config API service.
API_ROOT = 'https://luci-config.appspot.com/_ah/api'

# The path which we will look for in projects.
SHERIFF_CONFIG_PATH = 'chromeperf-sheriff.cfg'


class Error(Exception):
  """All errors associated with the luci_config module."""


class FetchError(Error):

  def __init__(self, error):
    self.error = error
    super(FetchError, self).__init__()

  def __str__(self):
    return 'Failed fetching project configs: %s' % (self.error)


class ConfigError(Error):

  def __init__(self, error):
    self.error = error
    super(ConfigError, self).__init__()

  def __str__(self):
    return 'Failed discovering supported methods: %s' % (self.error)


def CreateConfigClient(http, api_root=API_ROOT, api='config', version='v1'):
  """Factory function for a creating a config client.

  This uses the discovery API to generate a service object corresponding to the
  API we're using from luci-config.

  Args:
    http: a fully configured HTTP client/request
    api_root: the URL through which the API will be configured (default:
      API_ROOT)
    api: the service name (default: 'config')
    version: the version of the API (default: 'v1')
  """
  discovery_url = '%s/discovery/v1/apis/%s/%s/rest' % (api_root, api, version)
  try:
    service = build(api, version, discoveryServiceUrl=discovery_url, http=http)
  except Exception as e:
    raise ConfigError(e)
  return service


def FindAllSheriffConfigs(service):
  """Finds all the project configs for chromeperf sheriffs."""
  try:
    configs = service.get_project_configs(path=SHERIFF_CONFIG_PATH).execute()
  except Exception as e:
    raise FetchError(e)
  return configs
