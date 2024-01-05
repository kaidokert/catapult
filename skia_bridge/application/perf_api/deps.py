# Copyright 2024 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging

from application.perf_api.clients import gitiles_client
from flask import Blueprint, request, make_response

blueprint = Blueprint('deps', __name__)

DEPS_MALFORMATTED_ERROR = 'DEPS is malformatted.'

@blueprint.route('', methods=['GET'])
def GetDepsHandler():
  repository_url = request.args.get('repository_url')
  if not repository_url:
    return 'Repository url is required in the request', 400

  git_hash = request.args.get('git_hash')
  if not git_hash:
    return 'Git hash is required in the request', 400

  try:
    client = gitiles_client.GitilesClient()
    content = client.GetGitDepsJSON(repository_url, git_hash)
    return content
  except NotImplementedError as e:
    # This means that the format of the requested DEPS is invalid.
    logging.exception(e)
    return DEPS_MALFORMATTED_ERROR, 400
  except Exception as e:
    logging.exception(e)
    raise e

