# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""URL endpoint for adding new histograms to the dashboard."""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import cloudstorage
import json
import logging
import uuid
import zlib
import six

from google.appengine.api import taskqueue

from dashboard.api import api_request_handler
from dashboard.common import datastore_hooks
from dashboard.common import request_handler
from dashboard.common import timing
from dashboard.common import utils
from dashboard.models import upload_completion_token

from dashboard.add_histograms_helper import DecompressFileWrapper
from dashboard.add_histograms_helper import ProcessHistogramSet
from dashboard.add_histograms_helper import CreateUploadCompletionToken
from dashboard.add_histograms_helper import LoadHistogramList
from dashboard.add_histograms_helper import RETRY_PARAMS
from dashboard.add_histograms_helper import TASK_RETRY_LIMIT

from flask import make_response, request


def AddHistogramsProcessPost():
  datastore_hooks.SetPrivilegedRequest()
  token = None

  try:
    params = json.loads(request.body)
    gcs_file_path = params['gcs_file_path']

    token_id = params.get('upload_completion_token')
    if token_id is not None:
      token = upload_completion_token.Token.get_by_id(token_id)
      upload_completion_token.Token.UpdateObjectState(
          token, upload_completion_token.State.PROCESSING)

    try:
      logging.debug('Loading %s', gcs_file_path)
      gcs_file = cloudstorage.open(
          gcs_file_path, 'r', retry_params=RETRY_PARAMS)
      with DecompressFileWrapper(gcs_file) as decompressing_file:
        histogram_dicts = LoadHistogramList(decompressing_file)

      gcs_file.close()
      ProcessHistogramSet(histogram_dicts, token)
    finally:
      cloudstorage.delete(gcs_file_path, retry_params=RETRY_PARAMS)

    upload_completion_token.Token.UpdateObjectState(
        token, upload_completion_token.State.COMPLETED)
    return make_response('{}')

  except Exception as e:  # pylint: disable=broad-except
    logging.error('Error processing histograms: %s', str(e))
    upload_completion_token.Token.UpdateObjectState(
        token, upload_completion_token.State.FAILED, str(e))
    return make_response(json.dumps({'error': str(e)}))


def AddHistogramsPost():
  if utils.IsDevAppserver():
    # Don't require developers to zip the body.
    # In prod, the data will be written to cloud storage and processed on the
    # taskqueue, so the caller will not see any errors. In dev_appserver,
    # process the data immediately so the caller will see errors.
    # Also always create upload completion token for such requests.
    token, token_info = CreateUploadCompletionToken()
    ProcessHistogramSet(
        LoadHistogramList(six.StringIO(request.body)), token)
    token.UpdateState(upload_completion_token.State.COMPLETED)
    return token_info

  with timing.WallTimeLogger('decompress'):
    try:
      data_str = request.body

      # Try to decompress at most 100 bytes from the data, only to determine
      # if we've been given compressed payload.
      zlib.decompressobj().decompress(data_str, 100)
      logging.info('Received compressed data.')
    except zlib.error as e:
      data_str = request.values.get('data')
      if not data_str:
        six.raise_from(
            api_request_handler.BadRequestError(
                'Missing or uncompressed data.'), e)
      data_str = zlib.compress(data_str)
      logging.info('Received uncompressed data.')

  if not data_str:
    raise api_request_handler.BadRequestError('Missing "data" parameter')

  filename = uuid.uuid4()
  params = {'gcs_file_path': '/add-histograms-cache/%s' % filename}

  gcs_file = cloudstorage.open(
      params['gcs_file_path'],
      'w',
      content_type='application/octet-stream',
      retry_params=RETRY_PARAMS)
  gcs_file.write(data_str)
  gcs_file.close()

  _, token_info = CreateUploadCompletionToken(params['gcs_file_path'])
  params['upload_completion_token'] = token_info['token']

  retry_options = taskqueue.TaskRetryOptions(
      task_retry_limit=TASK_RETRY_LIMIT)
  queue = taskqueue.Queue('default')
  queue.add(
      taskqueue.Task(
          url='/add_histograms/process',
          payload=json.dumps(params),
          retry_options=retry_options))
  return token_info


if six.PY2:
  class AddHistogramsProcessHandler(request_handler.RequestHandler):

    def post(self):
      datastore_hooks.SetPrivilegedRequest()
      token = None

      try:
        params = json.loads(self.request.body)
        gcs_file_path = params['gcs_file_path']

        token_id = params.get('upload_completion_token')
        if token_id is not None:
          token = upload_completion_token.Token.get_by_id(token_id)
          upload_completion_token.Token.UpdateObjectState(
              token, upload_completion_token.State.PROCESSING)

        try:
          logging.debug('Loading %s', gcs_file_path)
          gcs_file = cloudstorage.open(
              gcs_file_path, 'r', retry_params=RETRY_PARAMS)
          with DecompressFileWrapper(gcs_file) as decompressing_file:
            histogram_dicts = LoadHistogramList(decompressing_file)

          gcs_file.close()

          ProcessHistogramSet(histogram_dicts, token)
        finally:
          cloudstorage.delete(gcs_file_path, retry_params=RETRY_PARAMS)

        upload_completion_token.Token.UpdateObjectState(
            token, upload_completion_token.State.COMPLETED)

      except Exception as e:  # pylint: disable=broad-except
        logging.error('Error processing histograms: %s', str(e))
        self.response.out.write(json.dumps({'error': str(e)}))

        upload_completion_token.Token.UpdateObjectState(
            token, upload_completion_token.State.FAILED, str(e))


  # pylint: disable=abstract-method
  class AddHistogramsHandler(api_request_handler.ApiRequestHandler):

    def Post(self, *args, **kwargs):
      del args, kwargs  # Unused.
      if utils.IsDevAppserver():
        # Don't require developers to zip the body.
        # In prod, the data will be written to cloud storage and processed on
        # the taskqueue, so the caller will not see any errors.
        # In dev_appserver, process the data immediately so the caller will
        # see errors. Also, always create upload completion token for such
        # requests.
        token, token_info = CreateUploadCompletionToken()
        ProcessHistogramSet(
            LoadHistogramList(six.StringIO(self.request.body)), token)
        token.UpdateState(upload_completion_token.State.COMPLETED)
        return token_info

      with timing.WallTimeLogger('decompress'):
        try:
          data_str = self.request.body

          # Try to decompress at most 100 bytes from the data, only to determine
          # if we've been given compressed payload.
          zlib.decompressobj().decompress(data_str, 100)
          logging.info('Received compressed data.')
        except zlib.error as e:
          data_str = self.request.get('data')
          if not data_str:
            six.raise_from(
                api_request_handler.BadRequestError(
                    'Missing or uncompressed data.'), e)
          data_str = zlib.compress(data_str)
          logging.info('Received uncompressed data.')

      if not data_str:
        raise api_request_handler.BadRequestError('Missing "data" parameter')

      filename = uuid.uuid4()
      params = {'gcs_file_path': '/add-histograms-cache/%s' % filename}

      gcs_file = cloudstorage.open(
          params['gcs_file_path'],
          'w',
          content_type='application/octet-stream',
          retry_params=RETRY_PARAMS)
      gcs_file.write(data_str)
      gcs_file.close()

      _, token_info = CreateUploadCompletionToken(params['gcs_file_path'])
      params['upload_completion_token'] = token_info['token']

      retry_options = taskqueue.TaskRetryOptions(
          task_retry_limit=TASK_RETRY_LIMIT)
      queue = taskqueue.Queue('default')
      queue.add(
          taskqueue.Task(
              url='/add_histograms/process',
              payload=json.dumps(params),
              retry_options=retry_options))
      return token_info
