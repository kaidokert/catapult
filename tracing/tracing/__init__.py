# Copyright (c) 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import sys
import tracing_project
tracing_project.UpdateSysPathIfNeeded()

if 'google' in sys.modules:
  sys.modules.pop('google')
from google.protobuf.internal import enum_type_wrapper

