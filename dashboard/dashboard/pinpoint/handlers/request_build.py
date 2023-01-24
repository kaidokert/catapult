from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import logging

from dashboard.api import api_request_handler
from dashboard.api import api_auth
from dashboard.common import utils
from dashboard.pinpoint.models import change as change_module
from dashboard.pinpoint.models import isolate
from dashboard.pinpoint.models.quest import find_isolate
from dashboard.services import buildbucket_service

if utils.IsRunningFlask():
  from flask import request

  def _CheckUser():
    if utils.IsDevAppserver():
      return
    api_auth.Authorize()
    if not utils.IsTryjobUser():
      raise api_request_handler.ForbiddenError()

  @api_request_handler.RequestHandlerDecoratorFactory(_CheckUser)
  def RequestBuildHandlerPost():
    args = utils.RequestParamsMixed(request)
    builder_name = args.get('builder_name')
    git_hash = args.get('git_hash')
    repository = args.get('repository', 'chromium')
    bucket = args.get('bucket')
    patch = args.get('patch', '')
    target = args.get('target')

    buildbucket_id = _RequestBuild(builder_name=builder_name,
                                     git_hash=git_hash,
                                     repository=repository,
                                     bucket=bucket,
                                     patch=patch,
                                     target=target)

    return {
        'buildbucket_id': buildbucket_id
    }

else:
  class RequestBuild(api_request_handler.ApiRequestHandler):
    """Handler that requests a new Pinpoint build"""

    def _CheckUser(self):
      self._CheckIsLoggedIn()
      if not utils.IsTryjobUser():
        raise api_request_handler.ForbiddenError()

    def Post(self, *args, **kwargs):
      del args, kwargs
      builder_name = self.request.get('builder_name')
      git_hash = self.request.get('git_hash')
      repository = self.request.get('repository', 'chromium')
      bucket = self.request.get('bucket')
      patch = self.request.get('patch', '')
      target = self.request.get('target')

      buildbucket_id = _RequestBuild(builder_name=builder_name,
                                      git_hash=git_hash,
                                      repository=repository,
                                      bucket=bucket,
                                      patch=patch,
                                      target=target)

      return {
          'buildbucket_id': buildbucket_id
      }


def _RequestBuild(builder_name, git_hash, target, bucket, repository='chromium', patch=''):
    commit = change_module.Commit.FromDict({
        'repository': repository,
        'git_hash': git_hash,
    })

    if patch:
      patch = change_module.GerritPatch.FromUrl(patch)

    change = change_module.Change(
        commits=(commit,),
        patch=patch or None,
    )
    if _CheckIsolateCache(builder_name, change, target):
      raise KeyError('Isolate with builder %s, change %s, and target %s already exists.' %
                   (builder_name, change, target))

    build_tags = {}

    buildbucket_info = find_isolate.RequestBuild(builder_name, change, bucket, build_tags)
    logging.info('buildbucket_info:', buildbucket_info)
    return buildbucket_info['id']


def _CheckIsolateCache(builder_name, change, target):
  try:
    isolate_server, isolate_hash = isolate.Get(builder_name,
                                               change,
                                               target)
    return True
  except KeyError as e:
    return False
