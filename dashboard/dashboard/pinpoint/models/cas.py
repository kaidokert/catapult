# Copyright 2021 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Model for storing information to look up CAS from RBE.

A CAS reference is a way to refer the build result of RBE in CAS
(Content-Address-Storage).
"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import datetime

from google.appengine.ext import ndb

# TODO(fancl): Determine how long will cas instances perserve a build.
CAS_EXPIRY_DURATION = datetime.timedelta(days=58)


def Get(builder_name, change, target):
  """Retrieve an cas reference from the Datastore.

  Args:
    builder_name: The name of the builder that produced the cas reference.
    change: The Change the cas reference was built at.
    target: The compile target the cas reference is for.

  Returns:
    A tuple containing the cas_instance and cas_digest as strings.
  """
  entity = ndb.Key(CASReference, _Key(builder_name, change, target)).get()
  if not entity:
    raise KeyError('No cas reference with builder %s, '
                   'change %s, and target %s.' %
                   (builder_name, change, target))

  if entity.created + CAS_EXPIRY_DURATION < datetime.datetime.utcnow():
    raise KeyError('Cas reference with builder %s, '
                   'change %s, and target %s was '
                   'found, but is expired.' % (builder_name, change, target))

  return entity.cas_instance, entity.cas_digest


def Put(cas_references):
  """Add CASReference to the Datastore.

  This function takes multiple entries to do a batched Datstore put.

  Args:
    cas_references: An iterable of tuples. Each tuple is of the form
        (builder_name, change, target, cas_instance, cas_digest).
  """
  entities = []
  for cas_reference in cas_references:
    builder_name, change, target, cas_instance, cas_digest = cas_reference
    entity = CASReference(
        cas_instance=cas_instance,
        cas_digest=cas_digest,
        id=_Key(builder_name, change, target))
    entities.append(entity)
  ndb.put_multi(entities)


class CASReference(ndb.Model):
  cas_instance = ndb.StringProperty(indexed=False, required=True)
  cas_digest = ndb.StringProperty(indexed=False, required=True)
  created = ndb.DateTimeProperty(auto_now_add=True)

  # We can afford to look directly in Datastore here since we don't expect to
  # make multiple calls to this at a high rate to benefit from being in
  # memcache. This lets us clear out the cache in Datastore and not have to
  # clear out memcache as well.
  _use_memcache = False
  _use_datastore = True
  _use_cache = False


def _Key(builder_name, change, target):
  # The key must be stable across machines, platforms,
  # Python versions, and Python invocations.
  return '\n'.join((builder_name, change.id_string, target))
