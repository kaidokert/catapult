# Copyright 2020 Google Inc. All rights reserved.
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

import json
import os
import tempfile

import mock
from pyfakefs import fake_filesystem_unittest

from typ import json_results
from typ import result_sink


DEFAULT_LUCI_CONTEXT = {
    'result_sink': {
        'address': 'address',
        'auth_token': 'auth_token',
    },
}
ARTIFACT_DIR = os.path.abspath(os.path.join('artifact', 'dir'))


def CreateResults(inputs):
    """Creates a ResultSet with Results.

    Args:
        inputs: A list of dicts describing the results to create.

    Returns:
        A ResultSet with its results field filled with Results.
    """
    rs = json_results.ResultSet()
    for i in inputs:
        r = json_results.Result(
            name=i['name'],
            actual=i['actual'],
            started=True,
            took=1,
            worker=None,
            expected=i.get('expected'),
            artifacts=i.get('artifacts'))
        rs.add(r)
    return rs


class ResultSinkReporterTest(fake_filesystem_unittest.TestCase):
    def setUp(self):
        self.setUpPyfakefs()
        self._luci_context_file = tempfile.NamedTemporaryFile(delete=False).name
        self._patcher = mock.patch.dict(os.environ, {}, clear=True)
        self._patcher.start()
        self.addCleanup(self._patcher.stop)

    def setLuciContextWithContent(self, content):
        os.environ['LUCI_CONTEXT'] = self._luci_context_file
        with open(self._luci_context_file, 'w') as outfile:
            json.dump(content, outfile)

    def testNoLuciContext(self):
        rsr = result_sink.ResultSinkReporter()
        self.assertFalse(rsr.resultdb_supported)

    def testNoSinkKey(self):
        self.setLuciContextWithContent({})
        rsr = result_sink.ResultSinkReporter()
        self.assertFalse(rsr.resultdb_supported)

    def testValidSinkKey(self):
        self.setLuciContextWithContent(DEFAULT_LUCI_CONTEXT)
        rsr = result_sink.ResultSinkReporter()
        self.assertTrue(rsr.resultdb_supported)

    @mock.patch.object(result_sink.ResultSinkReporter, 'report_result')
    def testReportFullResultsEarlyReturnIfNotSupported(self, report_mock):
        self.setLuciContextWithContent({})
        rsr = result_sink.ResultSinkReporter()
        self.assertEqual(rsr.report_full_results(None, None, None, None), 0)
        report_mock.assert_not_called()

    @mock.patch.object(result_sink.ResultSinkReporter, 'report_result')
    def testReportFullResultsBasicCase(self, report_mock):
        self.setLuciContextWithContent(DEFAULT_LUCI_CONTEXT)
        rsr = result_sink.ResultSinkReporter()
        results = CreateResults([{
            'name': 'test_name',
            'actual': 'PASS',
        }])
        report_mock.return_value = 2
        retval = rsr.report_full_results(
                'test_name_prefix.', results, ARTIFACT_DIR,
                ['foo_tag', 'bar_tag'])
        test_id = 'test_name_prefix.test_name'
        report_mock.assert_called_once_with(
            test_id, 'PASS', True, {},
            {'typ_tags': 'foo_tag bar_tag', 'test_name': test_id})
        self.assertEqual(retval, 2)

    @mock.patch.object(result_sink.ResultSinkReporter, 'report_result')
    def testReportFullResultsMultipleResults(self, report_mock):
        self.setLuciContextWithContent(DEFAULT_LUCI_CONTEXT)
        rsr = result_sink.ResultSinkReporter()
        results = CreateResults([{
            'name': 'test_name',
            'actual': 'PASS',
        }, {
            'name': 'second_name',
            'actual': 'FAIL',
        }])
        report_mock.return_value = 2
        retval = rsr.report_full_results(
                'test_name_prefix.', results, ARTIFACT_DIR,
                ['foo_tag', 'bar_tag'])
        self.assertEqual(report_mock.call_count, 2)
        test_id = 'test_name_prefix.test_name'
        report_mock.assert_any_call(
                test_id, 'PASS', True, {},
                {'typ_tags': 'foo_tag bar_tag', 'test_name': test_id})
        test_id = 'test_name_prefix.second_name'
        report_mock.assert_any_call(
                test_id, 'FAIL', False, {},
                {'typ_tags': 'foo_tag bar_tag', 'test_name': test_id})
        self.assertEqual(retval, 2)
    

    @mock.patch.object(result_sink.ResultSinkReporter, 'report_result')
    def testReportFullResultsSingleArtifact(self, report_mock):
        self.setLuciContextWithContent(DEFAULT_LUCI_CONTEXT)
        rsr = result_sink.ResultSinkReporter()
        results = CreateResults([{
            'name': 'test_name',
            'actual': 'PASS',
            'artifacts': {
                'artifact_name': ['some_artifact'],
            },
        }])
        retval = rsr.report_full_results(
                'test_name_prefix.', results, ARTIFACT_DIR,
                ['foo_tag', 'bar_tag'])
        test_id = 'test_name_prefix.test_name'
        report_mock.assert_called_once_with(
            test_id, 'PASS', True, {
                'artifact_name': {
                    'filePath': os.path.join(ARTIFACT_DIR, 'some_artifact')
                },
            }, {'typ_tags': 'foo_tag bar_tag', 'test_name': test_id})

    @mock.patch.object(result_sink.ResultSinkReporter, 'report_result')
    def testReportFullResultsMultipleArtifacts(self, report_mock):
        self.setLuciContextWithContent(DEFAULT_LUCI_CONTEXT)
        rsr = result_sink.ResultSinkReporter()
        results = CreateResults([{
            'name': 'test_name',
            'actual': 'PASS',
            'artifacts': {
                'artifact_name': ['some_artifact', 'another_artifact'],
            },
        }])
        retval = rsr.report_full_results(
                'test_name_prefix.', results, ARTIFACT_DIR,
                ['foo_tag', 'bar_tag'])
        test_id = 'test_name_prefix.test_name'
        report_mock.assert_called_once_with(
            test_id, 'PASS', True, {
                'artifact_name-file0': {
                    'filePath': os.path.join(ARTIFACT_DIR, 'some_artifact')
                },
                'artifact_name-file1': {
                    'filePath': os.path.join(ARTIFACT_DIR, 'another_artifact')
                },
            }, {'typ_tags': 'foo_tag bar_tag', 'test_name': test_id})

    @mock.patch('result_sink._create_json_test_result')
    def testReportResultEarlyReturnIfNotSupported(self, json_mock):
        self.setLuciContextWithContent({})
        rsr = result_sink.ResultSinkReporter()
        self.assertEqual(rsr.report_result(None, None, None, None, None), 0)
        json_mock.assert_not_called()

    @mock.patch('requests.post')
    @mock.patch('typ.result_sink._create_json_test_result')
    def testReportResultBasic(self, json_mock, post_mock):
        self.setLuciContextWithContent(DEFAULT_LUCI_CONTEXT)
        rsr = result_sink.ResultSinkReporter()
        mock_response = mock.Mock()
        mock_response.status_code = 200
        post_mock.return_value = mock_response
        json_mock.return_value = {'some': 'fancy_json'}
        retval = rsr.report_result(
            'test_id', 'PASS', True, {'artifact': {'filePath': 'somefile'}},
            {'tag_key': 'tag_value'})
        json_mock.assert_called_once_with(
            'test_id', 'PASS', True, {'artifact': {'filePath': 'somefile'}},
            {'tag_key': 'tag_value'})
        post_mock.assert_called_once_with(
            url='http://address/prpc/luci.resultsink.v1.Sink/ReportTestResults',
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': 'ResultSink auth_token',
            },
            data='{"testResults": [{"some": "fancy_json"}]}')
        self.assertEqual(retval, 0)

    @mock.patch('requests.post')
    @mock.patch('typ.result_sink._create_json_test_result')
    def testReportResultNonZeroOnNotOkay(self, json_mock, post_mock):
        self.setLuciContextWithContent(DEFAULT_LUCI_CONTEXT)
        rsr = result_sink.ResultSinkReporter()
        mock_response = mock.Mock()
        mock_response.status_code = 201
        post_mock.return_value = mock_response
        json_mock.return_value = {'some': 'fancy_json'}
        retval = rsr.report_result(
            'test_id', 'PASS', True, {'artifact': {'filePath': 'somefile'}},
            {'tag_key': 'tag_value'})
        self.assertEqual(retval, 1)

    def testCreateJsonTestResultInvalidStatus(self):
        with self.assertRaises(AssertionError):
            result_sink._create_json_test_result(
                None, 'InvalidStatus', None, None, None)

    def testCreateJsonTestResultBasic(self):
        retval = result_sink._create_json_test_result(
            'test_id', 'PASS', True, {'artifact': {'filePath': 'somepath'}},
            {'tag_key': 'tag_value'})
        self.assertEqual(retval, {
            'testId': 'test_id',
            'status': 'PASS',
            'expected': True,
            'summaryHtml': '',
            'artifacts': {
                'artifact': {
                    'filePath': 'somepath',
                },
            },
            'tags': [
                {
                    'key': 'tag_key',
                    'value': 'tag_value',
                },
            ],
        })
