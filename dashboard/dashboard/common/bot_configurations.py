# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import string

from google.appengine.ext import ndb

from dashboard.common import namespaced_stored_object


BOT_CONFIGURATIONS_KEY = 'bot_configurations'


def Get(name):
  configurations = namespaced_stored_object.Get(BOT_CONFIGURATIONS_KEY)
  configuration = configurations[name]
  if 'alias' in configuration:
    return configurations[configuration['alias']]
  return configuration


@ndb.tasklet
def GetAliasesAsync(bot):
  aliases = set([bot])
  configurations = yield namespaced_stored_object.GetAsync(
      BOT_CONFIGURATIONS_KEY)
  if not configurations:
    raise ndb.Return(aliases)

  alias_map = {}  # canonical: [aliases]
  for name, configuration in configurations.iteritems():
    if 'alias' in configuration:
      canonical = configuration['alias']
      alias_map.setdefault(canonical, {canonical}).add(name)
      if bot == name:
        bot = canonical

  raise ndb.Return(alias_map.get(bot, {bot}))


def List():
  bot_configurations = namespaced_stored_object.Get(BOT_CONFIGURATIONS_KEY)
  canonical_names = [name for name, value in bot_configurations.iteritems()
                     if 'alias' not in value]
  return sorted(canonical_names, key=string.lower)
