# Copyright 2023 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Common utils for issue tracker client."""

import json
import logging

import httplib2

import google.auth
import google_auth_httplib2


TOKEN_INFO_ENDPOINT = 'https://oauth2.googleapis.com/tokeninfo'
EMAIL_SCOPE = 'https://www.googleapis.com/auth/userinfo.email'

def AuthorizeBearerToken(request, allow_list=None):
  """
    Verifies that the request is authorized by checking the email info from
    the bearer token.
  """

  # Check that the request includes the `Authorization` header.
  if "Authorization" not in request.headers:
    return False, None

  access_token = request.headers["Authorization"].split("Bearer ")[1]
  token_info_url = '%s?bearer_token=%s' % (TOKEN_INFO_ENDPOINT, access_token)
  response, content = httplib2.Http(timeout=30).request(token_info_url)

  if response.status != 200:
    logging.warning(
      'Invalid response status from token info endpoint: %s. Url: %s',
      response, token_info_url)
    return False, None

  content_dict = json.loads(content)
  email = content_dict.get('email')
  logging.info('Client email: %s', email)
  if email and content_dict.get('email_verified'):
    if allow_list is None or email in allow_list:
      return True, email

  logging.warning('No valid email is found in request token.')
  return False, None


def ServiceAccountHttp(scope=EMAIL_SCOPE, timeout=None):
  """Returns the Credentials of the service account if available."""

  assert scope, "ServiceAccountHttp scope must not be None."
  credentials = _GetAppDefaultCredentials(scope)
  http = google_auth_httplib2.AuthorizedHttp(credentials)
  if timeout:
    http.timeout = timeout
  return http


def _GetAppDefaultCredentials(scope=None):
  try:
    credentials, _ = google.auth.default()
    if scope and credentials.requires_scopes:
      credentials = credentials.with_scopes([scope])
    return credentials
  except google.auth.exceptions.DefaultCredentialsError as e:
    logging.error('Error when getting the application default credentials: %s',
                  str(e))
    return None
