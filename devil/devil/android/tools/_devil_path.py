# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import sys


DEVIL_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..'))


if not DEVIL_PATH in sys.path:
  sys.path.append(DEVIL_PATH)
