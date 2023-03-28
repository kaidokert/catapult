# Copyright 2023 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import grpc

import cabe_grpc

cabe_server_address = 'cabe.skia.org'
plaintext = True

def GetAnalysis(job_id):
  "Return a TryJob CABE Analysis as a list."
    if plaintext:
        channel = grpc.insecure_channel(cabe_server_address)
    else:
        channel = grpc.secure_channel(cabe_server_address, grpc.ssl_channel_credentials())
    try:
        stub = cabe_grpc.AnalysisStub(channel)
        request = cabe_grpc.GetanalysisRequest(
            pinpoint_job_id=job_id
        )
        return stub.GetAnalysis(request).result
    finally:
        channel.close()
