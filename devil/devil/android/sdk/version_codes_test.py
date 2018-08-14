#!/usr/bin/env python
# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""
Unit tests for sdk version_codes.py
"""

import unittest

from devil.android.sdk import version_codes


class VersionCodesTest(unittest.TestCase):

  def testVersionNamesAreComplete(self):
    for version_name in [v for v in dir(version_codes) if
                         not v.startswith("__") and v != "VERSION_NAMES"]:
      self.assertTrue(version_name in version_codes.VERSION_NAMES,
                      "Version name %s not in VERSION_CODES" % (version_name))

  def testVersionNamesExist(self):
    for version_name in version_codes.VERSION_NAMES:
      self.assertTrue(hasattr(version_codes, version_name),
                      "Version code for %s is not defined" % (version_name))


if __name__ == '__main__':
  unittest.main()
