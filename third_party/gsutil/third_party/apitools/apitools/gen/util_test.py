#
# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for util."""
import unittest2

from apitools.gen import util


class NormalizeVersionTest(unittest2.TestCase):

    def testVersions(self):
        already_valid = 'v1'
        self.assertEqual(already_valid, util.NormalizeVersion(already_valid))
        to_clean = 'v0.1'
        self.assertEqual('v0_1', util.NormalizeVersion(to_clean))


class NamesTest(unittest2.TestCase):

    def testKeywords(self):
        names = util.Names([''])
        self.assertEqual('in_', names.CleanName('in'))

    def testNormalizeEnumName(self):
        names = util.Names([''])
        self.assertEqual('_0', names.NormalizeEnumName('0'))
