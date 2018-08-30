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


def UpdateBots(master_bots, internal_only, skip_correct=True):
  ndb.Future.wait_all(UpdateBotAsync(master, bot, internal_only, skip_correct)
                      for master, bot in master_bots)


@ndb.tasklet
def UpdateBotAsync(master, bot, internal_only, skip_correct=True):
  bot_entity = yield ndb.Key('Master', master, 'Bot', bot).get_async()
  bot_entity.internal_only = internal_only
  yield bot_entity.put_async()
  deferred.defer(UpdateTests, master, bot, start_cursor=None,
                 skip_correct=skip_correct, _queue=QUEUE_NAME)


def UpdateBotSync(master, bot, internal_only, skip_correct=True):
  UpdateBotAsync(master, bot, internal_only, skip_correct).get_result()


def UpdateTests(master, bot, start_cursor=None, skip_correct=True):
  datastore_hooks.SetPrivilegedRequest()
  internal_only = ndb.Key('Master', master, 'Bot', bot).get().internal_only
  logging.info('%s/%s internal_only=%s', master, bot, internal_only)

  @ndb.tasklet
  def HandleTest(test):
    deferred.defer(UpdateAnomalies, test.test_path, _queue=QUEUE_NAME)
    if test.internal_only != internal_only:
      test.internal_only = internal_only
      yield test.put_async()

  query = graph_data.TestMetadata.query(
      graph_data.TestMetadata.master_name == master,
      graph_data.TestMetadata.bot_name == bot)
  if skip_correct:
    query = query.filter(
        graph_data.TestMetadata.internal_only == (not internal_only))
  count, next_cursor = utils.IterateQueryAsync(
      query, start_cursor, HandleTest).get_result()
  logging.info('%d tests', count)

  if next_cursor:
    logging.info('continuing')
    deferred.defer(UpdateTests, master, bot, next_cursor, _queue=QUEUE_NAME)


def UpdateAnomalies(test_path):
  datastore_hooks.SetPrivilegedRequest()
  test = utils.TestKey(test_path).get()
  bot = ndb.Key('Master', test.master_name, 'Bot', test.bot_name).get()
  logging.info('UpdateAnomalies %r internal_only=%r',
               test_path, bot.internal_only)
  anomalies, _, _ = anomaly.Anomaly.QueryAsync(
      test=test_path, internal_only=not bot.internal_only).get_result()
  for entity in anomalies:
    entity.internal_only = bot.internal_only
  ndb.put_multi(anomalies)
  logging.info('updated %d anomalies', len(anomalies))
