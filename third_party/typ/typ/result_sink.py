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

"""Functionality for interacting with ResultDB's ResultSink.

ResultSink is a process that accepts test results via HTTP requests for
ingesting into ResultDB.

See go/resultdb and go/resultsink for more details.
"""

import json
import os
import posixpath
import requests

# Valid status taken from the "TestStatus" enum in
# https://source.chromium.org/chromium/infra/infra/+/master:go/src/go.chromium.org/luci/resultdb/proto/v1/test_result.proto
VALID_STATUSES = {
    'PASS',
    'FAIL',
    'CRASH',
    'ABORT',
    'SKIP',
}


class ResultSinkReporter(object):
    def __init__(self):
        self._sink = None

        luci_context_file = os.environ.get('LUCI_CONTEXT')
        if not luci_context_file:
            # Would be nice to keep this, but currently messes with the output
            # checks in main_test.py.
            #print('LUCI_CONTEXT not found, ResultDB integration not supported.')
            return
        with open(luci_context_file) as f:
            self._sink = json.load(f).get('result_sink')
            if not self._sink:
                # Ditto.
                #print('ResultDB "result_sink" key not found in LUCI context, ResultDB '
                #            'integration not supported.')
                return

        self._url = (
                'http://%s/prpc/luci.resultsink.v1.Sink/ReportTestResults' %
                self._sink['address'])
        self._headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': 'ResultSink %s' % self._sink['auth_token']
        }

    @property
    def resultdb_supported(self):
        return self._sink is not None

    def report_full_results(
            self, test_name_prefix, results, artifact_output_dir,
            expectation_tags):
        """Reports full typ results to ResultSink.

        Inputs are typically similar to what is passed to
        json_results.make_full_results().

        Ideally, test results would be reported immediately after a test
        finishes, but currently requires some information that isn't available
        to a child.

        Args:
            test_name_prefix: A string containing the prefix that will be added
                    to each test name.
            results: A json_results.ResultsSet instance containing the results
                    to report.
            artifact_output_dir: The path to the directory where artifacts test
                    artifacts are saved on disk.
            expectation_tags: A list of typ expectation tags that apply to the
                    run tests.

        Returns:
            0 if all results were reported successfully or ResultDB is not
            supported, otherwise 1.
        """
        retcode = 0
        if not self.resultdb_supported:
            return retcode

        base_tags_dict = {}
        if expectation_tags:
            base_tags_dict['typ_tags'] = ' '.join(expectation_tags)

        if not os.path.isabs(artifact_output_dir):
            artifact_output_dir = os.path.join(os.getcwd(), artifact_output_dir)
        for r in results.results:
            test_id = test_name_prefix + r.name
            tags_dict = base_tags_dict.copy()
            tags_dict['test_name'] = test_id
            result_is_expected = r.actual in r.expected
            artifacts = {}
            original_artifacts = r.artifacts or {}
            for artifact_name, artifact_filepaths in original_artifacts.items():
                # The typ artifact implementation supports multiple artifacts
                # for a single artifact name, but ResultDB does not.
                if len(artifact_filepaths) > 1:
                    for index, filepath in enumerate(artifact_filepaths):
                        artifacts[artifact_name + '-file%d' % index] = {
                            'filePath': os.path.join(
                                    artifact_output_dir, filepath),
                        }
                else:
                    artifacts[artifact_name] = {
                        'filePath': os.path.join(
                                artifact_output_dir, artifact_filepaths[0]),
                    }
            retcode |= self.report_result(
                    test_id, r.actual, result_is_expected, artifacts, tags_dict)
        return retcode


    def report_result(self, test_id, status, expected, artifacts, tags_dict):
        """Reports a single test result to ResultSink.

        Args:
            test_id: A string containing the unique identifier of the test.
            status: A string containing the status of the test. Must be in
                    |VALID_STATUSES|.
            expected: A boolean denoting whether |status| is expected or not.
            artifacts: A dict of artifact names (strings) to dicts, specifying
                    either a filepath or base64-encoded artifact content.
            tags_dict: A dict of tag names (strings) to tag values (strings).

        Returns:
            0 if the result was reported successfully or ResultDB is not
            supported, otherwise 1.
        """
        if not self.resultdb_supported:
            return 0

        # TODO: Handle testLocation key
        test_result = _create_json_test_result(
                test_id, status, expected, artifacts, tags_dict)

        res = requests.post(
                url=self._url,
                headers=self._headers,
                data=json.dumps({'testResults': [test_result]})
        )
        return 0 if res.status_code == 200 else 1


def _create_json_test_result(test_id, status, expected, artifacts, tags_dict):
    """Formats data to be suitable for sending to ResultSink.

    Args:
        test_id: A string containing the unique identifier of the test.
        status: A string containing the status of the test. Must be in
                |VALID_STATUSES|.
        expected: A boolean denoting whether |status| is expected or not.
        artifacts: A dict of artifact names (strings) to dicts, specifying
                either a filepath or base64-encoded artifact content.
        tags_dict: A dict of tag names (strings) to tag values (strings).

    Returns:
        A dict containing the provided data in a format that is ingestable by
        ResultSink.
    """
    assert status in VALID_STATUSES
    test_result = {
            'testId': test_id,
            'status': status,
            'expected': expected,
            'summaryHtml': '',
            'artifacts': artifacts,
            'tags': [],
    }
    for k, v in tags_dict.items():
        test_result['tags'].append({'key': k, 'value': v})
    return test_result
