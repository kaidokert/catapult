# Copyright 2023 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import
import grpc
import cabe_grpc

CABE_SERVER_ADDRESS = 'cabe.skia.org'
CABE_USE_PLAINTEXT = True


def GetAnalysis(job_id):
  "Return a TryJob CABE Analysis as a list."
  if CABE_USE_PLAINTEXT:
    channel = grpc.insecure_channel(CABE_SERVER_ADDRESS)
  else:
    channel = grpc.secure_channel(CABE_SERVER_ADDRESS,
                                  grpc.ssl_channel_credentials())

  try:
    stub = cabe_grpc.AnalysisStub(channel)
    request = cabe_grpc.GetanalysisRequest(pinpoint_job_id=job_id)
    return stub.GetAnalysis(request).result
  finally:
    channel.close()
