# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging

from google.appengine.ext import deferred
from google.appengine.ext import ndb

from dashboard.common import datastore_hooks
from dashboard.models import anomaly
from dashboard.models import graph_data


QUEUE_NAME = 'migrate-queue'
PAGE_LIMIT = 5000


@ndb.synctasklet
def UpdateBots(master_bots, internal_only):
  """Change internal_only for many Bots in parallel.

  This is not called anywhere because admins run this in dev_console.
  The Bots' TestMetadata and Anomalies are also updated.
  """
  yield [UpdateBotAsync(master, bot, internal_only)
         for master, bot in master_bots]


@ndb.synctasklet
def UpdateBotSync(master, bot, internal_only):
  """Change a Bot's internal_only.

  This is not called anywhere because admins run this in dev_console.
  The Bot's TestMetadata and Anomalies are also updated.
  """
  yield UpdateBotAsync(master, bot, internal_only)


@ndb.tasklet
def UpdateBotAsync(master, bot, internal_only):
  """Change a Bot's internal_only.

  The Bot's TestMetadata and Anomalies are also updated.
  """
  bot_entity = yield ndb.Key('Master', master, 'Bot', bot).get_async()
  bot_entity.internal_only = internal_only
  yield bot_entity.put_async()
  deferred.defer(UpdateTests, master, bot, _queue=QUEUE_NAME)
  deferred.defer(UpdateAnomalies, master, bot, _queue=QUEUE_NAME)


def UpdateTests(master, bot, start_cursor=None):
  """Update TestMetadata.internal_only to match their Bot's internal_only.
  """
  datastore_hooks.SetPrivilegedRequest()
  internal_only = graph_data.Bot.GetInternalOnlySync(master, bot)
  logging.info('%s/%s internal_only=%s', master, bot, internal_only)
  query = graph_data.TestMetadata.query(
      graph_data.TestMetadata.master_name == master,
      graph_data.TestMetadata.bot_name == bot,
      graph_data.TestMetadata.internal_only == (not internal_only))
  tests, next_cursor, more = query.fetch_page(
      PAGE_LIMIT, start_cursor=start_cursor)
  for test in tests:
    test.internal_only = internal_only
  ndb.put_multi(tests)
  logging.info('%d tests', len(tests))
  if next_cursor:
    logging.info('continuing')
    deferred.defer(UpdateTests, master, bot, next_cursor, _queue=QUEUE_NAME)
  else:
    logging.info('complete')


def UpdateAnomalies(master, bot, start_cursor=None):
  """Update Anomaly.internal_only to match their Bot's internal_only.
  """
  datastore_hooks.SetPrivilegedRequest()
  internal_only = graph_data.Bot.GetInternalOnlySync(master, bot)
  anomalies, next_cursor, _ = anomaly.Anomaly.QuerySync(
      master_name=master, bot_name=bot,
      internal_only=(not internal_only), limit=PAGE_LIMIT)
  for entity in anomalies:
    entity.internal_only = internal_only
  ndb.put_multi(anomalies)
  logging.info('updated %d anomalies', len(anomalies))
  if next_cursor:
    logging.info('continuing')
    deferred.defer(UpdateAnomalies, master, bot, next_cursor, _queue=QUEUE_NAME)
  else:
    logging.info('complete')
