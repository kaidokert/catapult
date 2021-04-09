# Copyright 2021 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from apiclient import discovery
from oauth2client.client import GoogleCredentials


class RBECASService(object):

  def __init__(self, http):
    """Initializes an object for retrieving files and directories from RBE-CAS.

    This class makes requests to RBE-CAS

    Args:
      http: A Http object that requests will be made through
    """
    self._service = discovery.build(
        'remotebuildexecution',
        'v2',
        http=http,
        credentials=GoogleCredentials.get_application_default(),
    )

  def GetTree(self, cas_ref, page_size=None, page_token=None):
    return self._service.blobs().getTree(
        instanceName=cas_ref['cas_instance'],
        hash=cas_ref['digest']['hash'],
        sizeBytes=cas_ref['digest']['sizeBytes'],
        pageSize=page_size,
        pageToken=page_token
    ).execute()

  def BatchRead(self, cas_instance, digests):
    return self._service.blobs().batchRead(
        instanceName=cas_instance,
        body={
            'digests': digests,
        },
    ).execute()
