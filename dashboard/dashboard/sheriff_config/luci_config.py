# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""API Wrapper for the luci-config service."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import base64
import json
from googleapiclient.discovery import build
from google.cloud import datastore

# The Root of the luci-config API service.
API_ROOT = 'https://luci-config.appspot.com/_ah/api'

# The path which we will look for in projects.
SHERIFF_CONFIG_PATH = 'chromeperf-sheriff.cfg'


class Error(Exception):
  """All errors associated with the luci_config module."""

  def __init__(self, error):
    self.error = error
    super(Error, self).__init__()


class FetchError(Error):

  def __str__(self):
    return 'Failed fetching project configs: %s' % (self.error)


class ConfigError(Error):

  def __str__(self):
    return 'Failed discovering supported methods: %s' % (self.error)


class InvalidConfigError(Error):

  def __init__(self, config, fields):
    super(InvalidConfigError, self).__init__(None)
    self.fields = fields
    self.config = config

  def __str__(self):
    return 'Config (%r) missing required fields: %r' % (self.config,
                                                        self.fields)


class InvalidConfigFieldError(Error):

  def __init__(self, error, config):
    super(InvalidConfigFieldError, self).__init__(error)
    self.config = config

  def __str__(self):
    return 'Config (%r) content decoding error: %s' % (self.config, self.error)


class PutFailure(Error):

  def __str__(self):
    return 'Failed call to put: %s' % (self.error)


class GetFailure(Error):

  def __str__(self):
    return 'Failed call to get: %s' % (self.error)


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


def StoreConfigs(client, configs):
  """Takes configuration dictionaries and persists them in the datastore.

  Args:
    client: The client for accessing the storage API.
    configs: The config objects we'd like to store.

  Raises:
    InvalidConfigError: raised when config has missing required fields.
    InvalidConfigFieldError: raised when the content is not a decodable base64
      encoded JSON document.

  Returns:
    None
  """
  if not configs or len(configs) == 0:
    raise ValueError('Configs must not be empty nor None.')

  required_fields = set(
      ('config_set', 'content', 'revision', 'url', 'content_hash'))

  # We group the Subscription instances along a SubscriptionIndex entity. A
  # SubscriptionIndex will always have the latest version of the subscription
  # configurations, for easy lookup, as a list. We will only update the
  # SubscriptionIndex if there were any new revisions in the configuration sets
  # that we've gotten.
  subscription_index_key = client.key('SubscriptionIndex', 'global')

  def Transform(config):
    missing_fields = required_fields.difference(set(config.keys()))
    if len(missing_fields):
      raise InvalidConfigError(config, missing_fields)

    # We use a combination of the config set, revision, and content_hash to
    # identify this particular configuration.
    key = client.key(
        'Subscription',
        ':'.join(
            (config['config_set'], config['revision'], config['content_hash'])),
        parent=subscription_index_key)
    try:
      decoded_content = json.loads(base64.standard_b64decode(config['content']))
    except json.JSONDecodeError as error:
      raise InvalidConfigFieldError(config, error)

    entity = datastore.Entity(
        key=key, exclude_from_indexes=['raw_content', 'decoded_content', 'url'])
    entity.update(config)
    entity.update({'decoded_content': decoded_content})
    return (key, entity)

  entities = dict(Transform(config) for config in configs)
  with client.transaction():
    # First, lookup the keys for each of the entities to see whether all of them
    # have already been stored. This allows us to avoid performing write
    # operations that end up not doing any updates.
    missing_entities = []
    try:
      if len(entities) > 1:
        found_entities = client.get_multi(
            entities.keys(), missing=missing_entities)
      else:
        for key in entities.keys():
          found_entities = [client.get(key, missing=missing_entities)]
    except ValueError as error:
      raise GetFailure(error)

    # Short circuit when we find no missing keys.
    if len(missing_entities) == 0:
      return None

    # Next, we only put the entities that were missing from our earlier get.
    try:
      for found_entity in found_entities:
        del entities[found_entity.key]

      if len(entities) > 1:
        client.put_multi(entities.values())
      elif len(entities) == 1:
        for entity in entities.values():
          client.put(entity)
      else:
        raise ValueError('Failed to write data: %r' % (entities))
    except ValueError as error:
      raise PutFailure(error)

    # From here we'll update an entity in the datastore which lists the grouped
    # keys in the datastore. This will serve as an index on the latest set of
    # configurations.
    subscription_index = datastore.Entity(
        key=subscription_index_key, exclude_from_indexes=['config_sets'])
    subscription_index.update({
        'config_sets': [
            ':'.join((config['config_set'], config['revision'],
                      config['content_hash'])) for config in configs
        ]
    })
    client.put(subscription_index)
