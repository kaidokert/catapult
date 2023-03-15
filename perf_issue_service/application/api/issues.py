# Copyright 2023 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from flask import make_response, Blueprint, request
from httplib2 import http
import json
import logging

from application import issue_tracker_client

issues = Blueprint('issues', __name__)


@issues.route('/', methods=['GET'])
def IssuesGetHandler():
  limit = request.args.get('limit', '2000')
  age = request.args.get('age', '3')
  status = request.args.get('status', 'open')
  labels = request.args.get('labels', '')

  client = issue_tracker_client.IssueTrackerClient()
  response = client.GetIssuesList(
      q='opened>today-%s' % age,
      can=status,
      label=labels,
      maxResults=limit,
      sort='-id')
  return make_response(response)

@issues.route('/<issue_id>/project/<project_name>', methods=['GET'])
def IssuesGetByIdHandler(issue_id, project_name):
  client = issue_tracker_client.IssueTrackerClient()
  response = client.GetIssue(
      issue_id=issue_id,
      project=project_name)
  return make_response(response)

@issues.route('/<issue_id>/project/<project_name>/comments', methods=['GET'])
def CommentsHandler(issue_id, project_name):
  client = issue_tracker_client.IssueTrackerClient()
  response = client.GetIssueComments(
      issue_id=issue_id,
      project=project_name)
  return make_response(response)

@issues.route('/', methods=['POST'])
def IssuesPostHandler():
  try:
    data = json.loads(request.data.decode())
  except json.JSONDecodeError as e:
    return make_response(str(e), http.HTTPStatus.BAD_REQUEST.value)

  try:
    title = data.get('title')
    description = data.get('description')
    project = data.get('project', 'chromium')
    labels = data.get('labels', None)
    components = data.get('components', None)
    owner = data.get('owner', None)
    cc = data.get('cc', None)
    status = data.get('status', None)
  except (AttributeError, KeyError) as e:
    return make_response(str(e), http.HTTPStatus.BAD_REQUEST.value)

  client = issue_tracker_client.IssueTrackerClient()
  response = client.NewIssue(
    title=title,
    description=description,
    project=project,
    labels=labels,
    components=components,
    owner=owner,
    cc=cc,
    status=status)
  return make_response(response)

@issues.route('/<issue_id>/project/<project_name>/comments', methods=['POST'])
def CommentsPostHandler(issue_id, project_name):
  try:
    data = json.loads(request.data.decode())
  except json.JSONDecodeError as e:
    return make_response(str(e), http.HTTPStatus.BAD_REQUEST.value)

  try:
    comment = data.get('comment')
    title = data.get('title', None)
    status = data.get('status', None)
    merge_issue = data.get('merge_issue', None)
    owner = data.get('owner', None)
    cc = data.get('cc', None)
    components = data.get('components', None)
    labels = data.get('labels', None)
    send_email = data.get('send_email', 'True')
  except (AttributeError, KeyError) as e:
    return make_response(str(e), http.HTTPStatus.BAD_REQUEST.value)

  client = issue_tracker_client.IssueTrackerClient()
  response = client.NewComment(
    issue_id=int(issue_id),
    project=project_name,
    comment=comment,
    title=title,
    status=status,
    merge_issue=merge_issue,
    owner=owner,
    cc=cc,
    components=components,
    labels=labels,
    send_email=(send_email.lower()=='true'))
  return make_response(response)