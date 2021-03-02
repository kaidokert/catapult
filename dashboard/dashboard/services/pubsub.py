# Copyright 2021 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Simple client for posting pub/sub messages through Cloud Pub/Sub."""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import base64
import functools

from apiclient import discovery

from dashboard.common import utils


class PubSubClient(object):

  @classmethod
  def GetClient(cls, topic, **kwargs):
    cached_service = getattr(PubSubClient.GetClient, '_cached_service', None)
    if cached_service == None:
      cached_service = utils.Retries(
          3, functools.wraps(discovery.build, 'pubsub', 'v1', **kwargs))
      setattr(PubSubClient.GetClient, '_cached_service', cached_service)
    return cls(cached_service, topic)

  def __init__(self, service, topic):
    if service is None:
      raise ValueError('service argument is required')
    if not topic:
      raise ValueError('topic must not be empty')
    self.service = service
    self.topic = topic

  def Post(self, data):
    """Post a message to the configured topic.

    Args:
      - data: a string that will be Base64 encoded.
    """
    self.service.projects().topics().publish(
        topic=self.topic,
        body={
            'messages': [{
                'data': base64.b64encode(data),
            }],
        }).execute()
