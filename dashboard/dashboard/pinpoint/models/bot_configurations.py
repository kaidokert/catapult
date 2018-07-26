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
def AliasesesAsync():
  aliaseses = []
  configurations = yield namespaced_stored_object.GetAsync(
      BOT_CONFIGURATIONS_KEY)
  if not configurations:
    raise ndb.Return(aliaseses)

  for name, configuration in configurations.iteritems():
    if 'alias' in configuration:
      aliaseses.append([name, configuration['alias']])

  # Merge intersecting aliases. If 'a' is aka 'b' and 'b' is aka 'c' then 'a' is
  # aka 'c'.
  for sort_index in range(2):
    aliaseses.sort(key=lambda pair, si=sort_index: pair[si])
    i = 1
    while i < len(aliaseses):
      prev_aliases = aliaseses[i - 1]
      cur_aliases = aliaseses[i]
      if not any(alias in cur_aliases for alias in prev_aliases):
        i += 1
        continue
      # Merge cur_aliases into prev_aliases and remove cur_aliases from
      # aliaseses.
      for alias in cur_aliases:
        if alias not in prev_aliases:
          prev_aliases.append(alias)
      aliaseses.pop(i)

  raise ndb.Return(aliaseses)


def List():
  bot_configurations = namespaced_stored_object.Get(BOT_CONFIGURATIONS_KEY)
  canonical_names = [name for name, value in bot_configurations.iteritems()
                     if 'alias' not in value]
  return sorted(canonical_names, key=string.lower)
