# Copyright 2023 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from flask import make_response, Blueprint, request
from application import issue_tracker_client

issues = Blueprint('issues', __name__)

@issues.route('/', methods=['GET'])
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


@issues.route('/<issue_id>/project/<project_name>', methods=['GET'])
def IssuesGetByIdHandler(issue_id, project_name):
  issue_tracker = issue_tracker_client.IssueTrackerService()
  response = issue_tracker.GetIssue(
      issue_id=issue_id,
      project=project_name)
  return make_response(response)


@issues.route('/<issue_id>/project/<project_name>/comments', methods=['GET'])
def CommentsHandler(issue_id, project_name):
  issue_tracker = issue_tracker_client.IssueTrackerService()
  response = issue_tracker.GetIssueComments(
      issue_id=issue_id,
      project=project_name)
  return make_response(response)