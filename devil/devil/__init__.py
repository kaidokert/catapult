# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import os
import sys

logging.getLogger('devil').addHandler(logging.NullHandler())


PY_UTILS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'common', 'py_utils'))
sys.path.append(PY_UTILS_DIR)
