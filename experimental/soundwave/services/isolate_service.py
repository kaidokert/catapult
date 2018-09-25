# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json
import os
import subprocess


ISOLATE_SERVER_SCRIPT = '/usr/local/google/code/clankium/src/tools/swarming_client/isolateserver.py'
ISOLATE_SERVER_URL = 'https://chrome-isolated.appspot.com'
OUTPUT_DIR = '/usr/local/google/code/clankium/src/third_party/catapult/experimental/soundwave/isolate_output'
CACHE_DIR = '/usr/local/google/code/clankium/src/third_party/catapult/experimental/soundwave/isolate_cache'


def RetrieveJson(isolate_hash, filepath):
  return json.loads(Retrieve(isolate_hash, filepath))


def Retrieve(isolate_hash, filepath):
  subprocess.check_call([
      ISOLATE_SERVER_SCRIPT, 'download',
      '--isolate-server', ISOLATE_SERVER_URL,
      '--file', isolate_hash, filepath,
      '--target', OUTPUT_DIR,
      '--cache', CACHE_DIR])
  with open(os.path.join(OUTPUT_DIR, filepath)) as f:
    return f.read()

