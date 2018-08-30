# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging

from google.appengine.ext import deferred
from google.appengine.ext import ndb

from dashboard.common import datastore_hooks
from dashboard.common import utils
from dashboard.models import anomaly
from dashboard.models import graph_data


# These functions are not called anywhere -- admins run them in dev_console.


QUEUE_NAME = 'migrate-queue'


def UpdateBots(master_bots, internal_only):
  ndb.Future.wait_all(UpdateBotAsync(master, bot, internal_only)
                      for master, bot in master_bots)


@ndb.synctasklet
def UpdateBotSync(master, bot, internal_only):
  yield UpdateBotAsync(master, bot, internal_only)


@ndb.tasklet
def UpdateBotAsync(master, bot, internal_only):
  bot_entity = yield ndb.Key('Master', master, 'Bot', bot).get_async()
  bot_entity.internal_only = internal_only
  yield bot_entity.put_async()
  deferred.defer(UpdateTests, master, bot, _queue=QUEUE_NAME)
  deferred.defer(UpdateAnomalies, master, bot, _queue=QUEUE_NAME)


def UpdateTests(master, bot, start_cursor=None):
  datastore_hooks.SetPrivilegedRequest()
  internal_only = graph_data.Bot.GetInternalOnlySync(master, bot)
  logging.info('%s/%s internal_only=%s', master, bot, internal_only)

  def HandleTest(test):
    if test.internal_only == internal_only:
      return None
    test.internal_only = internal_only
    return test.put_async()

  query = graph_data.TestMetadata.query(
      graph_data.TestMetadata.master_name == master,
      graph_data.TestMetadata.bot_name == bot)
  query = query.filter(
      graph_data.TestMetadata.internal_only == (not internal_only))
  count, next_cursor = utils.IterateQueryAsync(
      query, start_cursor, HandleTest).get_result()
  logging.info('%d tests', count)
  if next_cursor:
    logging.info('continuing')
    deferred.defer(UpdateTests, master, bot, next_cursor, _queue=QUEUE_NAME)


def UpdateAnomalies(master, bot, start_cursor=None):
  datastore_hooks.SetPrivilegedRequest()
  internal_only = graph_data.Bot.GetInternalOnlySync(master, bot)
  anomalies, next_cursor, _ = anomaly.Anomaly.QueryAsync(
      master_name=master, bot_name=bot,
      internal_only=not internal_only, limit=1000).get_result()
  for entity in anomalies:
    entity.internal_only = internal_only
  ndb.put_multi(anomalies)
  logging.info('updated %d anomalies', len(anomalies))
  if next_cursor:
    logging.info('continuing')
    deferred.defer(UpdateAnomalies, master, bot, next_cursor, _queue=QUEUE_NAME)
