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

  KNOWN_VERSION_NAMES = [
    'JELLY_BEAN',
    'JELLY_BEAN_MR1',
    'JELLY_BEAN_MR2',
    'KITKAT',
    'KITKAT_WATCH',
    'LOLLIPOP',
    'LOLLIPOP_MR1',
    'MARSHMALLOW',
    'NOUGAT',
    'NOUGAT_MR1',
    'OREO',
    'OREO_MR1'
  ]

  def testVersions(self):
    for name in self.KNOWN_VERSION_NAMES:
      self.assertTrue(hasattr(version_codes, name),
                      "Version code for %s is not defined" % (name))

  def testVersionNamesDict(self):
    for name in self.KNOWN_VERSION_NAMES:
      self.assertTrue(getattr(version_codes, name) in
                      version_codes.VERSION_NAMES_DICT,
                      "Didn't find name for version %s" % (name))
      code = getattr(version_codes, name)
      found_name = version_codes.VERSION_NAMES_DICT[code]
      self.assertEqual(name, found_name,
                       "Version name found for %s does not match: %s"
                       % (name, found_name))
    for code, name in version_codes.VERSION_NAMES_DICT.iteritems():
      self.assertTrue(name in self.KNOWN_VERSION_NAMES,
                      "Version name %s is not known" % (name))



if __name__ == '__main__':
  unittest.main()
