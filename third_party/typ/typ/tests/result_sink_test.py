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

import base64
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


def CreateResult(input_dict):
    """Creates a ResultSet with Results.

    Args:
        input_dict: A dict describing the result to create.

    Returns:
        A Result filled with the information from |input_dict|
    """
    return json_results.Result(name=input_dict['name'],
                               actual=input_dict['actual'],
                               started=True,
                               took=1,
                               worker=None,
                               expected=input_dict.get('expected'),
                               out=input_dict.get('out', 'stdout'),
                               err=input_dict.get('err', 'stderr'),
                               artifacts=input_dict.get('artifacts'))


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

    @mock.patch.object(result_sink.ResultSinkReporter, '_report_result')
    def testReportIndividualTestResultEarlyReturnIfNotSupported(
            self, report_mock):
        self.setLuciContextWithContent({})
        rsr = result_sink.ResultSinkReporter()
        self.assertEqual(
                rsr.report_individual_test_result(None, None, None, None), 0)
        report_mock.assert_not_called()

    @mock.patch.object(result_sink.ResultSinkReporter, '_report_result')
    def testReportIndividualTestResultBasicCase(self, report_mock):
        self.setLuciContextWithContent(DEFAULT_LUCI_CONTEXT)
        rsr = result_sink.ResultSinkReporter()
        result = CreateResult({
            'name': 'test_name',
            'actual': 'PASS',
        })
        report_mock.return_value = 2
        retval = rsr.report_individual_test_result(
                'test_name_prefix.', result, ARTIFACT_DIR,
                ['foo_tag', 'bar_tag'])
        test_id = 'test_name_prefix.test_name'
        report_mock.assert_called_once_with(
            test_id, 'PASS', True, {},
            {'typ_tags': 'foo_tag bar_tag', 'test_name': test_id},
            '<pre>stdout: stdout\nstderr: stderr</pre>', 1)
        self.assertEqual(retval, 2)

    @mock.patch.object(result_sink.ResultSinkReporter, '_report_result')
    def testReportIndividualTestResultLongSummary(self, report_mock):
        self.setLuciContextWithContent(DEFAULT_LUCI_CONTEXT)
        rsr = result_sink.ResultSinkReporter()
        result = CreateResult({
            'name': 'test_name',
            'actual': 'PASS',
            'out': 'a' * 4097,
            'err': '',
        })
        report_mock.return_value = 0
        rsr.report_individual_test_result(
                'test_name_prefix.', result, ARTIFACT_DIR,
                ['foo_tag', 'bar_tag'])
        test_id = 'test_name_prefix.test_name'
        truncated_summary = '<pre>stdout: %s%s' % (
            'a' * (result_sink.MAX_HTML_SUMMARY_LENGTH
                   - len(result_sink.TRUNCATED_SUMMARY_MESSAGE)
                   - 13),
            result_sink.TRUNCATED_SUMMARY_MESSAGE
        )
        artifact_contents = 'stdout: %s\nstderr: ' % ('a' * 4097)
        report_mock.assert_called_once_with(
            test_id, 'PASS', True, {
                'Test Log': {
                    'contents': base64.b64encode(artifact_contents)
                }
            },
            {'typ_tags': 'foo_tag bar_tag', 'test_name': test_id},
            truncated_summary, 1)

    @mock.patch.object(result_sink.ResultSinkReporter, '_report_result')
    def testReportIndividualTestResultConflictingKeyLongSummary(
            self, report_mock):
        self.setLuciContextWithContent(DEFAULT_LUCI_CONTEXT)
        rsr = result_sink.ResultSinkReporter()
        result = CreateResult({
            'name': 'test_name',
            'actual': 'PASS',
            'artifacts': {
                'Test Log': [''],
            },
            'out': 'a' * 4097,
        })
        with self.assertRaises(AssertionError):
            rsr.report_individual_test_result(
                    'test_name_prefix', result, ARTIFACT_DIR,
                    ['foo_tag', 'bar_tag'])

    @mock.patch.object(result_sink.ResultSinkReporter, '_report_result')
    def testReportIndividualTestResultSingleArtifact(self, report_mock):
        self.setLuciContextWithContent(DEFAULT_LUCI_CONTEXT)
        rsr = result_sink.ResultSinkReporter()
        results = CreateResult({
            'name': 'test_name',
            'actual': 'PASS',
            'artifacts': {
                'artifact_name': ['some_artifact'],
            },
        })
        retval = rsr.report_individual_test_result(
                'test_name_prefix.', results, ARTIFACT_DIR,
                ['foo_tag', 'bar_tag'])
        test_id = 'test_name_prefix.test_name'
        report_mock.assert_called_once_with(
            test_id, 'PASS', True, {
                'artifact_name': {
                    'filePath': os.path.join(ARTIFACT_DIR, 'some_artifact')
                },
            }, {'typ_tags': 'foo_tag bar_tag', 'test_name': test_id},
            '<pre>stdout: stdout\nstderr: stderr</pre>', 1)

    @mock.patch.object(result_sink.ResultSinkReporter, '_report_result')
    def testReportIndividualTestResultMultipleArtifacts(self, report_mock):
        self.setLuciContextWithContent(DEFAULT_LUCI_CONTEXT)
        rsr = result_sink.ResultSinkReporter()
        results = CreateResult({
            'name': 'test_name',
            'actual': 'PASS',
            'artifacts': {
                'artifact_name': ['some_artifact', 'another_artifact'],
            },
        })
        retval = rsr.report_individual_test_result(
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
            }, {'typ_tags': 'foo_tag bar_tag', 'test_name': test_id},
            '<pre>stdout: stdout\nstderr: stderr</pre>', 1)

    @mock.patch('result_sink._create_json_test_result')
    def testReportResultEarlyReturnIfNotSupported(self, json_mock):
        self.setLuciContextWithContent({})
        rsr = result_sink.ResultSinkReporter()
        self.assertEqual(rsr._report_result(
                'test_id', 'PASS', True, {}, {}, '<pre>summary</pre>', 1), 0)
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
        retval = rsr._report_result(
            'test_id', 'PASS', True, {'artifact': {'filePath': 'somefile'}},
            {'tag_key': 'tag_value'}, '<pre>summary</pre>', 1)
        json_mock.assert_called_once_with(
            'test_id', 'PASS', True, {'artifact': {'filePath': 'somefile'}},
            {'tag_key': 'tag_value'}, '<pre>summary</pre>', 1)
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
        retval = rsr._report_result(
            'test_id', 'PASS', True, {'artifact': {'filePath': 'somefile'}},
            {'tag_key': 'tag_value'}, '<pre>summary</pre>', 1)
        self.assertEqual(retval, 1)

    def testCreateJsonTestResultInvalidStatus(self):
        with self.assertRaises(AssertionError):
            result_sink._create_json_test_result(
                'test_id', 'InvalidStatus', False, {}, {}, '', 1)

    def testCreateJsonTestResultInvalidSummary(self):
        with self.assertRaises(AssertionError):
            result_sink._create_json_test_result(
                'test_id', 'PASS', True, {}, {}, 'a' * 4097, 1)

    def testCreateJsonTestResultBasic(self):
        retval = result_sink._create_json_test_result(
            'test_id', 'PASS', True, {'artifact': {'filePath': 'somepath'}},
            {'tag_key': 'tag_value'}, '<pre>summary</pre>', 1)
        self.assertEqual(retval, {
            'testId': 'test_id',
            'status': 'PASS',
            'expected': True,
            'duration': '1s',
            'summaryHtml': '<pre>summary</pre>',
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
