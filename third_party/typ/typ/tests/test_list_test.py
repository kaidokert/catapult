# Copyright 2018 Dirk Pranke. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest

from typ.test_list import Parser


class TestSimpleTestList(unittest.TestCase):
    def test_run_one_test(self):
        res, _, _ = Parser('foo.bar\n', '-').parse()
        self.assertEqual(
            [['rule', '', [], 'foo.bar', ['Pass'], ''],
             ['blank']],
            res)

    def test_skip_one_test(self):
        res, _, _ = Parser('-foo.bar\n', '-').parse()
        self.assertEqual(
            [['rule', '', [], 'foo.bar', ['Skip'], ''],
             ['blank']],
            res)

    def test_multiple_lines(self):
        res, _, _ = Parser('foo.bar\n# comment\n-baz.quux\n', '-').parse()
        self.assertEqual(
            [['rule', '', [], 'foo.bar', ['Pass'], ''],
             ['comment', '# comment'],
             ['rule', '', [], 'baz.quux', ['Skip'], ''],
             ['blank']],
            res)

class TestTaggedTestList(unittest.TestCase):
    maxDiff = None

    def test_simple(self):
        res, err, pos = Parser('''\
# sample file
# tags: [ Debug Release ]
# tags: [ Linux Mac Win ]

Bug(me) [ Mac Release ] foo/bar.html [ Skip ]
Bug(me) [ Win ] baz/* [ Pass Timeout ]
''', '-').parse()
        self.assertEqual(
            [['comment', '# sample file'],
             ['t_tag', [ 'Debug', 'Release' ]],
             ['t_tag', [ 'Linux', 'Mac', 'Win' ]],
             ['blank'],
             ['rule', 'Bug(me)', ['Mac', 'Release'], 'foo/bar.html', ['Skip'], ''],
             ['rule', 'Bug(me)', ['Win'], 'baz/*', ['Pass', 'Timeout'], ''],
             ['blank']], res)

