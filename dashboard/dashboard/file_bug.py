# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Provides the web interface for filing a bug on the issue tracker."""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from httplib2 import http
import json

from google.appengine.api import users
from google.appengine.ext import ndb

from dashboard.common import file_bug
from dashboard.common import request_handler
from dashboard.common import utils

from flask import request, make_response


def FileBugHandlerGet():
  """Uses oauth2 to file a new bug with a set of alerts.
  Either shows the form to file a bug, or if filled in, files the bug.

  The form to file a bug is popped up from the triage-dialog polymer element.
  The default summary, description and label strings are constructed there.

  Request parameters:
    summary: Bug summary string.
    description: Bug full description string.
    keys: Comma-separated Alert keys in urlsafe format.
    finish: Boolean set to true when creating a bug, false otherwise.
    project_id: The Monorail project ID (used to create  a bug).
    labels: Bug labels (used to create  a bug).
    components: Bug components (used to create  a bug).
    owner: Bug owner email address (used to create  a bug).
    cc: Bug emails to CC (used to create  a bug).

  Outputs:
    HTML, using the template 'bug_result.html'.
  """
  if not utils.IsValidSheriffUser():
    return request_handler.RequestHandlerRenderHtml(
        'bug_result.html', {
            'error': 'You must be logged in with a chromium.org account '
                     'to file bugs.'
        })

  summary = request.values.get('summary')
  description = request.values.get('description')
  keys = request.values.get('keys')

  if not keys:
    return request_handler.RequestHandlerRenderHtml(
        'bug_result.html', {'error': 'No alerts specified to add bugs to.'})

  if request.values.get('finish'):
    project_id = request.values.get('project_id', 'chromium')
    labels = request.values.getlist('label')
    components = request.values.getlist('component')
    owner = request.values.get('owner', '')
    cc = request.values.get('cc', '')
    create_bug_result = _CreateBug(owner, cc, summary, description, project_id,
                                   labels, components, keys)

    return request_handler.RequestHandlerRenderHtml('bug_result.html',
                                                    create_bug_result)
  return _ShowBugDialog(summary, description, keys)


def SkiaFileBugHandlerPost():
  """Similar to FileBugHandlerGet(), with the following difference:
     - Expect POST requests in application/json, where we need to load data
     from request.data.
     - No longer needs the 'finish' field, and always create a bug directly.
     - Return json instead of html.
  """
  print("===== received: ", request.data)
  if not utils.IsValidSheriffUser():
    return make_response({
            'error': 'You must be logged in to file bugs.'
        }, 401)

  try:
    data = json.loads(request.data)
  except json.JSONDecodeError as e:
    return make_response(str(e), http.HTTPStatus.BAD_REQUEST.value)

  keys = data.get('keys')
  if not keys:
    return make_response(
        json.dumps({'error': 'No anomaly keys specified to add bugs to.'}))

  summary = data.get('summary')
  description = data.get('description')
  project_id = data.get('project_id', 'chromium')
  labels = data.get('label')
  components = data.get('component')
  owner = data.get('owner', '')
  cc = data.get('cc', '')
  create_bug_result = _CreateBug(owner, cc, summary, description, project_id,
                                 labels, components, keys)

  return make_response(json.dumps(create_bug_result))


def _ShowBugDialog(summary, description, urlsafe_keys):
  """Sends a HTML page with a form for filing the bug.

  Args:
    summary: The default bug summary string.
    description: The default bug description string.
    urlsafe_keys: Comma-separated Alert keys in urlsafe format.
  """
  alert_keys = [ndb.Key(urlsafe=k) for k in urlsafe_keys.split(',')]
  labels, components = file_bug.FetchLabelsAndComponents(alert_keys)
  owner_components = file_bug.FetchBugComponents(alert_keys)
  return request_handler.RequestHandlerRenderHtml(
      'bug_result.html', {
          'bug_create_form': True,
          'keys': urlsafe_keys,
          'summary': summary,
          'description': description,
          'projects': utils.MONORAIL_PROJECTS,
          'labels': labels,
          'components': components.union(owner_components),
          'owner': '',
          'cc': users.get_current_user(),
      })


def _CreateBug(owner, cc, summary, description, project_id, labels, components,
               urlsafe_keys):
  """Creates a bug, associates it with the alerts, sends a HTML response.

  Args:
    owner: The owner of the bug, must end with @{project_id}.org or
      @google.com if not empty.
    cc: CSV of email addresses to CC on the bug.
    summary: The new bug summary string.
    description: The new bug description string.
    project_id: The Monorail project ID used to create the bug.
    labels: List of label strings for the new bug.
    components: List of component strings for the new bug.
    urlsafe_keys: Comma-separated alert keys in urlsafe format.
  """
  # Only project members (@{project_id}.org or @google.com accounts)
  # can be owners of bugs.
  project_domain = '@%s.org' % project_id
  if owner and not owner.endswith(project_domain) and not owner.endswith(
      '@google.com'):
    return {
        'error':
            'Owner email address must end with %s or @google.com.' %
            project_domain
    }

  template_params = file_bug.FileBug(owner, cc, summary, description,
                                     project_id, labels, components,
                                     urlsafe_keys.split(','))
  return template_params
