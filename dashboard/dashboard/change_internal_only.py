# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from google.appengine.datastore import datastore_query
from google.appengine.ext import deferred
from google.appengine.ext import ndb

from dashboard import add_point_queue
from dashboard.common import stored_object
from dashboard.models import anomaly
from dashboard.models import graph_data

# Number of Row entities to process at once.
_MAX_ROWS_TO_PUT = 25

# Number of TestMetadata entities to process at once.
_MAX_TESTS_TO_PUT = 25

# Which queue to use for tasks started by this handler. Must be in queue.yaml.
_QUEUE_NAME = 'migrate-queue'


# This function is not called anywhere except dev_console:
# https://chromeperf.appspot.com/_ah/dev_console/interactive
# from dashboard.change_internal_only import ChangeInternalOnly
# ChangeInternalOnly(False, [bot_names])
def ChangeInternalOnly(internal_only=True, bot_names=(), test_key_urlsafe='',
                       cursor=None):
  if bot_names and len(bot_names) > 1:
    _UpdateMultipleBots(bot_names, internal_only)
  elif bot_names and len(bot_names) == 1:
    _UpdateBot(bot_names[0], internal_only, cursor=cursor)
  elif test_key_urlsafe:
    _UpdateTest(test_key_urlsafe, internal_only)


def _UpdateBotWhitelist(bot_master_names, internal_only):
  """Updates the global bot_whitelist object, otherwise subsequent add_point
  calls will overwrite our work."""
  bot_whitelist = stored_object.Get(add_point_queue.BOT_WHITELIST_KEY)
  bot_names = [b.split('/')[1] for b in bot_master_names]

  if internal_only:
    bot_whitelist = [b for b in bot_whitelist if b not in bot_names]
  else:
    bot_whitelist.extend(bot_names)
    bot_whitelist = list(set(bot_whitelist))
  bot_whitelist.sort()

  stored_object.Set(add_point_queue.BOT_WHITELIST_KEY, bot_whitelist)


def _UpdateMultipleBots(bot_names, internal_only):
  """Kicks off update tasks for individual bots and their tests."""

  _UpdateBotWhitelist(bot_names, internal_only)

  for bot_name in bot_names:
    deferred.defer(ChangeInternalOnly, internal_only, [bot_name],
                   _queue=_QUEUE_NAME)


def _UpdateBot(bot_name, internal_only, cursor=None):
  """Starts updating internal_only for the given bot and associated data."""
  master, bot = bot_name.split('/')
  bot_key = ndb.Key('Master', master, 'Bot', bot)

  if not cursor:
    # First time updating for this Bot.
    bot_entity = bot_key.get()
    if bot_entity.internal_only != internal_only:
      bot_entity.internal_only = internal_only
      bot_entity.put()
  else:
    cursor = datastore_query.Cursor(urlsafe=cursor)

  # Fetch a certain number of TestMetadata entities starting from cursor. See:
  # https://developers.google.com/appengine/docs/python/ndb/queryclass

  # Start update tasks for each existing subordinate TestMetadata.
  test_query = graph_data.TestMetadata.query(
      graph_data.TestMetadata.master_name == master,
      graph_data.TestMetadata.bot_name == bot)
  test_keys, next_cursor, more = test_query.fetch_page(
      _MAX_TESTS_TO_PUT, start_cursor=cursor, keys_only=True)

  for test_key in test_keys:
    deferred.defer(ChangeInternalOnly, internal_only,
                   test_key_urlsafe=test_key.urlsafe(), _queue=_QUEUE_NAME)

  if more:
    deferred.defer(ChangeInternalOnly, internal_only, [bot_name],
                   cursor=next_cursor.urlsafe(), _queue=_QUEUE_NAME)


def _UpdateTest(test_key_urlsafe, internal_only):
  """Updates the given TestMetadata and associated Row entities."""
  test_key = ndb.Key(urlsafe=test_key_urlsafe)

  # First time updating for this TestMetadata.
  test_entity = test_key.get()
  if test_entity.internal_only != internal_only:
    test_entity.internal_only = internal_only
    test_entity.put()

  # Update all of the Anomaly entities for this test.
  # Assuming that this should be fast enough to do in one request
  # for any one test.
  anomalies, _, _ = anomaly.Anomaly.QueryAsync(test=test_key).get_result()
  for anomaly_entity in anomalies:
    if anomaly_entity.internal_only != internal_only:
      anomaly_entity.internal_only = internal_only
  ndb.put_multi(anomalies)
