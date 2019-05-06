"""API Wrapper for the luci-config service."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from googleapiclient.discovery import build
import google.auth


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


def CreateConfigClient(api_root=API_ROOT, api='config', version='v1'):
  discovery_url = '%s/discovery/v1/apis/%s/%s/rest' % (api_root, api, version)
  credentials, _ = google.auth.default()
  service = build(
      api, version, discoveryServiceUrl=discovery_url, credentials=credentials)
  return service


def FindAllSheriffConfigs(service):
  """Finds all the project configs for chromeperf sheriffs."""
  try:
    configs = service.configs().get_project_configs(
        path=SHERIFF_CONFIG_PATH).execute()
  except Exception as e:
    raise FetchError(e)
  return configs
