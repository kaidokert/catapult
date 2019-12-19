# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Policies to ensure internal or restricted information won't be leaked."""

# Support python3
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import sheriff_pb2


def FilterSubscriptionsByPolicy(request, configs):
  def IsPrivate(config):
    _, _, subscription = config
    return subscription.visibility == sheriff_pb2.Subscription.INTERNAL_ONLY
  privates = map(IsPrivate, configs)
  if any(privates) and not all(privates):
    logging.warning("Private sheriff overlaps with public: %s", request.path)
    configs = [c for c in configs if IsPrivate]
  return configs
