# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Adds pre hook to data store queries to hide internal-only data.

Checks if the user has a google.com address, and hides data with the
internal_only property set if not.
"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from google.appengine.api import apiproxy_stub_map
from google.appengine.api import users
from google.appengine.datastore import datastore_pb

from dashboard.common import utils
import six

from flask import g as flask_global
from flask import request as flask_request

if not utils.IsRunningFlask():
  import webapp2

# The list below contains all kinds that have an internal_only property.
# IMPORTANT: any new data types with internal_only properties must be added
# here in order to be restricted to internal users.
_INTERNAL_ONLY_KINDS = [
    'Bot',
    'TestMetadata',
    'Sheriff',
    'Anomaly',
    'TryJob',
    'TableConfig',
    'Histogram',
    'SparseDiagnostic',
    'ReportTemplate',
]

# Permissions namespaces.
EXTERNAL = 'externally_visible'
INTERNAL = 'internal_only'


def InstallHooks():
  """Installs datastore pre hook to add access checks to queries.

  This only needs to be called once, when doing config (currently in
  appengine_config.py).
  """
  apiproxy_stub_map.apiproxy.GetPreCallHooks().Push('_DatastorePreHook',
                                                    _DatastorePreHook,
                                                    'datastore_v3')


def SetPrivilegedRequest(flask_flag=False):
  """Allows the current request to act as a privileged user.

  This should ONLY be called for handlers that are restricted from end users
  by some other mechanism (IP allowlist, admin-only pages).

  This should be set once per request, before accessing the data store.

  Args:
    flask_flag - Determines if running on flask handlers when routing from URL.
        Default False.
  """
  if utils.IsRunningFlask() or flask_flag:
    flask_global.privileged = True
  else:
    request = webapp2.get_request()
    request.registry['privileged'] = True


def SetSinglePrivilegedRequest(flask_flag=False):
  """Allows the current request to act as a privileged user only ONCE.

  This should be called ONLY by handlers that have checked privilege immediately
  before making a query. It will be automatically unset when the next query is
  made.

  Args:
    flask_flag - Determines if running on flask handlers when routing from URL.
        Default False.
  """
  if utils.IsRunningFlask() or flask_flag:
    flask_global.single_privileged = True
  else:
    request = webapp2.get_request()
    request.registry['single_privileged'] = True


def CancelSinglePrivilegedRequest(flask_flag=False):
  """Disallows the current request to act as a privileged user only.

  Args:
    flask_flag - Determines if running on flask handlers when routing from URL.
        Default False.
  """
  if utils.IsRunningFlask() or flask_flag:
    flask_global.single_privileged = False
  else:
    request = webapp2.get_request()
    request.registry['single_privileged'] = False


def _IsServicingPrivilegedRequest(flask_flag=False):
  """Checks whether the request is considered privileged.

  Args:
    flask_flag - Determines if running on flask handlers when routing from URL.
        Default False.
  """
  if utils.IsRunningFlask() or flask_flag:
    try:
      path = flask_request.path
    except RuntimeError:
      # This happens in unit tests, when code gets called outside of a request.
      return False
    if path.startswith('/mapreduce'):
      return True
    if path.startswith('/_ah/queue/deferred'):
      return True
    if path.startswith('/_ah/pipeline/'):
      return True
    if 'privileged' in flask_global and flask_global.privileged:
      return True
    if 'single_privileged' in flask_global and flask_global.single_privileged:
      flask_global.pop('single_privileged')
      return True
    # We have been checking on utils.GetIpAllowlist() here. Though, the list
    # has been empty and we are infinite recursive calls in crbug/1402197.
    # Thus, we remove the check here.
  else:
    try:
      request = webapp2.get_request()
    except AssertionError:
      # This happens in unit tests, when code gets called outside of a request.
      return False
    path = getattr(request, 'path', '')
    if path.startswith('/mapreduce'):
      return True
    if path.startswith('/_ah/queue/deferred'):
      return True
    if path.startswith('/_ah/pipeline/'):
      return True
    if request.registry.get('privileged', False):
      return True
    if request.registry.get('single_privileged', False):
      request.registry['single_privileged'] = False
      return True
  return False


def IsUnalteredQueryPermitted(flask_flag=False):
  """Checks if the current user is internal, or the request is privileged.

  "Internal users" are users whose email address belongs to a certain
  privileged domain; but some privileged requests, such as task queue tasks,
  are also considered privileged.

  Args:
    flask_flag - Determines if running on flask handlers when routing from URL.
        Default False.

  Returns:
    True for users with google.com emails and privileged requests.
  """
  if _IsServicingPrivilegedRequest(flask_flag):
    return True
  if utils.IsInternalUser():
    return True
  # It's possible to be an admin with a non-internal account; For example,
  # the default login for dev appserver instances is test@example.com.
  return users.is_current_user_admin()


def GetNamespace():
  """Returns a namespace prefix string indicating internal or external user."""
  return INTERNAL if IsUnalteredQueryPermitted() else EXTERNAL


def _DatastorePreHook(service, call, request, _):
  """Adds a filter which checks whether to return internal data for queries.

  If the user is not privileged, we don't want to return any entities that
  have internal_only set to True. That is done here in a datastore hook.
  See: https://developers.google.com/appengine/articles/hooks

  Args:
    service: Service name, must be 'datastore_v3'.
    call: String representing function to call. One of 'Put', Get', 'Delete',
        or 'RunQuery'.
    request: Request protobuf.
    _: Response protobuf (not used).
  """
  assert service == 'datastore_v3'
  if call != 'RunQuery':
    return
  if IsUnalteredQueryPermitted():
    return

  # Add a filter for internal_only == False, because the user is external.
  if six.PY2:
    if request.kind() not in _INTERNAL_ONLY_KINDS:
      return
    try:
      external_filter = request.filter_list().add()
    except AttributeError:
      external_filter = request.add_filter()
    external_filter.set_op(datastore_pb.Query_Filter.EQUAL)
    new_property = external_filter.add_property()
    new_property.set_name('internal_only')
    new_property.mutable_value().set_booleanvalue(False)
    new_property.set_multiple(False)
  else:
    if request.kind not in _INTERNAL_ONLY_KINDS:
      return
    query_filter = request.filter.add()
    query_filter.op = datastore_pb.Query.Filter.EQUAL
    filter_property = query_filter.property.add()
    filter_property.name = 'internal_only'
    filter_property.value.booleanValue = False
    filter_property.multiple = False
