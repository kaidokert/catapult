# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import re

def sanitizeTypExpectationsTags(tags):
  return [re.sub('[ _]', '-', tag) for tag in tags if tag]
