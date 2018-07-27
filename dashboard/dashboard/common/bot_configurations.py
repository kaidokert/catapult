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

  # If 'a' is aka 'b' and 'b' is aka 'c', then 'a' is aka 'c'.
  # If the user asks for 'c', then they also need 'a' and 'b'.
  alias_map = {}
  for name, configuration in configurations.iteritems():
    if 'alias' in configuration:
      alias = configuration['alias']
      alias_map.setdefault(name, set()).add(alias)
      alias_map.setdefault(alias, set()).add(name)
  while any(name in alias_map for name in aliases):
    for name in aliases:
      aliases = aliases.union(alias_map.pop(name, set()))

  raise ndb.Return(aliases)


def List():
  bot_configurations = namespaced_stored_object.Get(BOT_CONFIGURATIONS_KEY)
  canonical_names = [name for name, value in bot_configurations.iteritems()
                     if 'alias' not in value]
  return sorted(canonical_names, key=string.lower)
