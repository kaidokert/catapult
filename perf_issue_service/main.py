# Copyright 2023 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Dispatches requests to request handler classes."""

from flask import Flask, request, make_response
import logging

import google.cloud.logging
try:
  import googleclouddebugger
  googleclouddebugger.enable(breakpoint_enable_canary=True)
except ImportError:
  pass

import issue_tracker_client

google.cloud.logging.Client().setup_logging(log_level=logging.DEBUG)

APP = Flask(__name__)


@APP.route('/')
def DummyHandler():
  return make_response('welcome')


@APP.route('/issues', methods=['GET'])
def IssuesGetHandler():
  limit = request.args.get('limit', '2000')
  age = request.args.get('age', '3')
  status = request.args.get('status', 'open')
  labels = request.args.get('labels', '')

  issue_tracker = issue_tracker_client.IssueTrackerService()
  response = issue_tracker.GetIssuesList(
      q='opened>today-%s' % age,
      can=status,
      label=labels,
      maxResults=limit,
      sort='-id')
  return make_response(response.get('items', []) if response else [])


@APP.route('/issues/<issue_id>/project/<project_name>', methods=['GET'])
def IssuesGetByIdHandler(issue_id, project_name):
  issue_tracker = issue_tracker_client.IssueTrackerService()
  response = issue_tracker.GetIssue(
      issue_id=issue_id,
      project=project_name)
  return make_response(response)


@APP.route('/issues/<issue_id>/project/<project_name>/comments', methods=['GET'])
def CommentsHandler(issue_id, project_name):
  issue_tracker = issue_tracker_client.IssueTrackerService()
  response = issue_tracker.GetIssueComments(
      issue_id=bug_id,
      project=project_name)
  return make_response(response)


if __name__ == '__main__':
  # This is used when running locally only.
  app.run(host='127.0.0.1', port=8080, debug=True)
