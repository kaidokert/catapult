# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Provides the web interface for changing internal_only property of a Bot."""

import logging

from google.appengine.ext import deferred
from google.appengine.ext import ndb

from dashboard import add_point_queue
from dashboard.common import datastore_hooks
from dashboard.common import request_handler
from dashboard.common import stored_object
from dashboard.common import utils
from dashboard.models import anomaly
from dashboard.models import graph_data


QUEUE_NAME = 'migrate-queue'


class ChangeInternalOnlyHandler(request_handler.RequestHandler):
  """Changes internal_only property of Bot, TestMetadata, and Row."""

  def get(self):
    """Renders the UI for selecting bots."""
    masters = {}
    bots = graph_data.Bot.query().fetch()
    for bot in bots:
      master_name = bot.key.parent().string_id()
      bot_name = bot.key.string_id()
      bots = masters.setdefault(master_name, [])
      bots.append({
          'name': bot_name,
          'internal_only': bot.internal_only,
      })
    logging.info('MASTERS: %s', masters)

    self.RenderHtml('change_internal_only.html', {
        'masters': masters,
    })

  def post(self):
    """Updates the selected bots internal_only property.

    POST requests will be made by the task queue; tasks are added to the task
    queue either by a kick-off POST from the front-end form, or by this handler
    itself.

    Request parameters:
      internal_only: "true" if turning on internal_only, else "false".
      bots: Bots to update. Multiple bots parameters are possible; the value
          of each should be a string like "MasterName/platform-name".

    Outputs:
      A message to the user if this request was started by the web form,
      or an error message if something went wrong, or nothing.
    """
    # /change_internal_only should be only accessible if one has administrator
    # privileges, so requests are guaranteed to be authorized.
    datastore_hooks.SetPrivilegedRequest()

    internal_only_string = self.request.get('internal_only')
    if internal_only_string == 'true':
      internal_only = True
    elif internal_only_string == 'false':
      internal_only = False
    else:
      self.ReportError('No internal_only field')
      return

    master_bots = [master_bot.split('/')
                   for master_bot in self.request.get_all('bots')]
    if master_bots:
      UpdateBotWhitelist(master_bots, internal_only)
      ndb.Future.wait_all([UpdateBot(master, bot, internal_only)
                           for master, bot in master_bots])

    self.RenderHtml('result.html', {'headline': (
        'Updating internal_only. This may take some time depending on the data '
        'to update. Check the task queue to determine whether the job is still '
        'in progress.')})


def UpdateBotWhitelist(master_bots, internal_only):
  bot_whitelist = set(stored_object.Get(add_point_queue.BOT_WHITELIST_KEY))
  changing_names = {b[1] for b in master_bots}
  if internal_only:
    bot_whitelist = [b for b in bot_whitelist if b not in changing_names]
  else:
    bot_whitelist = changing_names.union(bot_whitelist)
  stored_object.Set(add_point_queue.BOT_WHITELIST_KEY, sorted(bot_whitelist))


@ndb.tasklet
def UpdateBot(master, bot, internal_only):
  bot_entity = yield ndb.Key('Master', master, 'Bot', bot).get_async()
  bot_entity.internal_only = internal_only
  yield bot_entity.put_async()
  deferred.defer(UpdateTests, master, bot, _queue=QUEUE_NAME)


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
  anomalies, _, _ = anomaly.Anomaly.QueryAsync(
      test=test_path, internal_only=not bot.internal_only).get_result()
  for entity in anomalies:
    entity.internal_only = bot.internal_only
  ndb.put_multi(anomalies)
