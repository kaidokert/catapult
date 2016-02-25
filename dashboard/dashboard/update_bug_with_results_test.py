# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import copy
import datetime
import json
import unittest

import mock
import webapp2
import webtest

from dashboard import bisect_fyi
from dashboard import bisect_fyi_test
from dashboard import layered_cache
from dashboard import rietveld_service
from dashboard import stored_object
from dashboard import testing_common
from dashboard import update_bug_with_results
from dashboard import utils
from dashboard.models import anomaly
from dashboard.models import bug_data
from dashboard.models import try_job

_SAMPLE_BISECT_RESULTS_JSON = {
    'try_job_id': 6789,
    'bug_id': 4567,
    'status': 'completed',
    'bisect_bot': 'linux',
    'buildbot_log_url': '',
    'command': ('tools/perf/run_benchmark -v '
                '--browser=release page_cycler.intl_ar_fa_he'),
    'metric': 'warm_times/page_load_time',
    'change': '',
    'score': 99.9,
    'good_revision': '306475',
    'bad_revision': '306478',
    'warnings': None,
    'abort_reason': None,
    'issue_url': 'https://issue_url/123456',
    'culprit_data': {
        'subject': 'subject',
        'author': 'author',
        'email': 'author@email.com',
        'cl_date': '1/2/2015',
        'commit_info': 'commit_info',
        'revisions_links': ['http://src.chromium.org/viewvc/chrome?view='
                            'revision&revision=20798'],
        'cl': '2a1781d64d'  # Should match config in bisect_fyi_test.py.
    },
    'revision_data': [
        {
            'depot_name': 'chromium',
            'deps_revision': 1234,
            'commit_pos': 1234,
            'mean_value': 70,
            'std_dev': 0,
            'values': [70, 70, 70],
            'result': 'good'
        }, {
            'depot_name': 'chromium',
            'deps_revision': 1235,
            'commit_pos': 1235,
            'mean_value': 80,
            'std_dev': 0,
            'values': [80, 80, 80],
            'result': 'bad'
        }
    ]
}

_REVISION_RESPONSE = """
<html xmlns=....>
<head><title>[chrome] Revision 207985</title></head><body><table>....
<tr align="left">
<th>Log Message:</th>
<td> Message....</td>
&gt; &gt; Review URL: <a href="https://codereview.chromium.org/81533002">\
https://codereview.chromium.org/81533002</a>
&gt;
&gt; Review URL: <a href="https://codereview.chromium.org/96073002">\
https://codereview.chromium.org/96073002</a>

Review URL: <a href="https://codereview.chromium.org/17504006">\
https://codereview.chromium.org/96363002</a></pre></td></tr></table>....</body>
</html>
"""

_PERF_TEST_CONFIG = """config = {
  'command': 'tools/perf/run_benchmark -v --browser=release\
dromaeo.jslibstylejquery --profiler=trace',
  'good_revision': '215806',
  'bad_revision': '215828',
  'repeat_count': '1',
  'max_time_minutes': '120'
}"""

_ISSUE_RESPONSE = """
    {
      "description": "Issue Description.",
      "cc": [
              "chromium-reviews@chromium.org",
              "cc-bugs@chromium.org",
              "sullivan@google.com"
            ],
      "reviewers": [
                      "prasadv@google.com"
                   ],
      "owner_email": "sullivan@google.com",
      "private": false,
      "base_url": "svn://chrome-svn/chrome/trunk/src/",
      "owner":"sullivan",
      "subject":"Issue Subject",
      "created":"2013-06-20 22:23:27.227150",
      "patchsets":[1,21001,29001],
      "modified":"2013-06-22 00:59:38.530190",
      "closed":true,
      "commit":false,
      "issue":17504006
    }
"""


def _MockFetch(url=None):
  url_to_response_map = {
      'http://src.chromium.org/viewvc/chrome?view=revision&revision=20798': [
          200, _REVISION_RESPONSE
      ],
      'http://src.chromium.org/viewvc/chrome?view=revision&revision=20799': [
          200, 'REVISION REQUEST FAILED!'
      ],
      'https://codereview.chromium.org/api/17504006': [
          200, json.dumps(json.loads(_ISSUE_RESPONSE))
      ],
  }

  if url not in url_to_response_map:
    assert False, 'Bad url %s' % url

  response_code = url_to_response_map[url][0]
  response = url_to_response_map[url][1]
  return testing_common.FakeResponseObject(response_code, response)


# In this class, we patch apiclient.discovery.build so as to not make network
# requests, which are normally made when the IssueTrackerService is initialized.
@mock.patch('apiclient.discovery.build', mock.MagicMock())
@mock.patch.object(utils, 'TickMonitoringCustomMetric', mock.MagicMock())
class UpdateBugWithResultsTest(testing_common.TestCase):

  def setUp(self):
    super(UpdateBugWithResultsTest, self).setUp()
    app = webapp2.WSGIApplication([(
        '/update_bug_with_results',
        update_bug_with_results.UpdateBugWithResultsHandler)])
    self.testapp = webtest.TestApp(app)
    self._AddRietveldConfig()

  def _AddRietveldConfig(self):
    """Adds a RietveldConfig entity to the datastore.

    This is used in order to get the Rietveld URL when requests are made to the
    handler in te tests below. In the real datastore, the RietveldConfig entity
    would contain credentials.
    """
    rietveld_service.RietveldConfig(
        id='default_rietveld_config',
        client_email='sullivan@google.com',
        service_account_key='Fake Account Key',
        server_url='https://test-rietveld.appspot.com',
        internal_server_url='https://test-rietveld.appspot.com').put()

  def _AddTryJob(self, bug_id, status, bot, **kwargs):
    job = try_job.TryJob(bug_id=bug_id, status=status, bot=bot, **kwargs)
    job.put()
    bug_data.Bug(id=bug_id).put()
    return job

  @mock.patch(
      'google.appengine.api.urlfetch.fetch',
      mock.MagicMock(side_effect=_MockFetch))
  @mock.patch.object(
      update_bug_with_results.issue_tracker_service, 'IssueTrackerService',
      mock.MagicMock())
  def testGet(self):
    # Put succeeded, failed, staled, and not yet finished jobs in the
    # datastore.
    self._AddTryJob(11111, 'started', 'win_perf',
                    results_data=_SAMPLE_BISECT_RESULTS_JSON)
    staled_timestamp = (datetime.datetime.now() -
                        update_bug_with_results._STALE_TRYJOB_DELTA)
    self._AddTryJob(22222, 'started', 'win_perf',
                    last_ran_timestamp=staled_timestamp)
    self._AddTryJob(33333, 'failed', 'win_perf')
    self._AddTryJob(44444, 'started', 'win_perf')

    self.testapp.get('/update_bug_with_results')
    pending_jobs = try_job.TryJob.query().fetch()
    # Expects no jobs to be deleted.
    self.assertEqual(4, len(pending_jobs))
    self.assertEqual(11111, pending_jobs[0].bug_id)
    self.assertEqual('completed', pending_jobs[0].status)
    self.assertEqual(22222, pending_jobs[1].bug_id)
    self.assertEqual('staled', pending_jobs[1].status)
    self.assertEqual(33333, pending_jobs[2].bug_id)
    self.assertEqual('failed', pending_jobs[2].status)
    self.assertEqual(44444, pending_jobs[3].bug_id)
    self.assertEqual('started', pending_jobs[3].status)

  @mock.patch(
      'google.appengine.api.urlfetch.fetch',
      mock.MagicMock(side_effect=_MockFetch))
  @mock.patch.object(
      update_bug_with_results.issue_tracker_service, 'IssueTrackerService',
      mock.MagicMock())
  def testCreateTryJob_WithoutExistingBug(self):
    # Put succeeded job in the datastore.
    try_job.TryJob(
        bug_id=12345, status='started', bot='win_perf',
        results_data=_SAMPLE_BISECT_RESULTS_JSON).put()

    self.testapp.get('/update_bug_with_results')
    pending_jobs = try_job.TryJob.query().fetch()

    # Expects job to finish.
    self.assertEqual(1, len(pending_jobs))
    self.assertEqual(12345, pending_jobs[0].bug_id)
    self.assertEqual('completed', pending_jobs[0].status)

  @mock.patch.object(utils, 'ServiceAccountCredentials', mock.MagicMock())
  @mock.patch(
      'google.appengine.api.urlfetch.fetch',
      mock.MagicMock(side_effect=_MockFetch))
  @mock.patch.object(
      update_bug_with_results.issue_tracker_service.IssueTrackerService,
      'AddBugComment', mock.MagicMock(return_value=False))
  @mock.patch('logging.error')
  def testGet_FailsToUpdateBug_LogsErrorAndMovesOn(self, mock_logging_error):
    # Put a successful job and a failed job with partial results.
    # Note that AddBugComment is mocked to always returns false, which
    # simulates failing to post results to the issue tracker for all bugs.
    self._AddTryJob(12345, 'started', 'win_perf',
                    results_data=_SAMPLE_BISECT_RESULTS_JSON)
    self._AddTryJob(54321, 'started', 'win_perf',
                    results_data=_SAMPLE_BISECT_RESULTS_JSON)
    self.testapp.get('/update_bug_with_results')

    # Two errors should be logged.
    self.assertEqual(2, mock_logging_error.call_count)

    # The pending jobs should still be there.
    pending_jobs = try_job.TryJob.query().fetch()
    self.assertEqual(2, len(pending_jobs))
    self.assertEqual('started', pending_jobs[0].status)
    self.assertEqual('started', pending_jobs[1].status)

  @mock.patch(
      'google.appengine.api.urlfetch.fetch',
      mock.MagicMock(side_effect=_MockFetch))
  @mock.patch.object(
      update_bug_with_results.issue_tracker_service.IssueTrackerService,
      'AddBugComment')
  def testGet_BisectCulpritHasAuthor_AssignsAuthor(self, mock_update_bug):
    # When a bisect has a culprit for a perf regression,
    # author and reviewer of the CL should be cc'ed on issue update.
    self._AddTryJob(12345, 'started', 'win_perf',
                    results_data=_SAMPLE_BISECT_RESULTS_JSON)

    self.testapp.get('/update_bug_with_results')
    mock_update_bug.assert_called_once_with(
        mock.ANY, mock.ANY,
        cc_list=['author@email.com', 'prasadv@google.com'],
        merge_issue=None, labels=None, owner='author@email.com')

  @mock.patch(
      'google.appengine.api.urlfetch.fetch',
      mock.MagicMock(side_effect=_MockFetch))
  @mock.patch.object(
      update_bug_with_results.issue_tracker_service.IssueTrackerService,
      'AddBugComment')
  def testGet_FailedRevisionResponse(self, mock_add_bug):
    # When a Rietveld CL link fails to respond, only update CL owner in CC
    # list.
    sample_bisect_results = copy.deepcopy(_SAMPLE_BISECT_RESULTS_JSON)
    sample_bisect_results['revisions_links'] = [
        'http://src.chromium.org/viewvc/chrome?view=revision&revision=20799']
    self._AddTryJob(12345, 'started', 'win_perf',
                    results_data=sample_bisect_results)

    self.testapp.get('/update_bug_with_results')
    mock_add_bug.assert_called_once_with(mock.ANY,
                                         mock.ANY,
                                         cc_list=['author@email.com',
                                                  'prasadv@google.com'],
                                         merge_issue=None,
                                         labels=None,
                                         owner='author@email.com')

  @mock.patch(
      'google.appengine.api.urlfetch.fetch',
      mock.MagicMock(side_effect=_MockFetch))
  @mock.patch.object(
      update_bug_with_results.issue_tracker_service.IssueTrackerService,
      'AddBugComment', mock.MagicMock())
  def testGet_PositiveResult_StoresCommitHash(self):
    self._AddTryJob(12345, 'started', 'win_perf',
                    results_data=_SAMPLE_BISECT_RESULTS_JSON)

    self.testapp.get('/update_bug_with_results')
    self.assertEqual('12345',
                     layered_cache.GetExternal('commit_hash_2a1781d64d'))

  @mock.patch(
      'google.appengine.api.urlfetch.fetch',
      mock.MagicMock(side_effect=_MockFetch))
  @mock.patch.object(
      update_bug_with_results.issue_tracker_service.IssueTrackerService,
      'AddBugComment', mock.MagicMock())
  def testGet_NegativeResult_DoesNotStoreCommitHash(self):
    sample_bisect_results = copy.deepcopy(_SAMPLE_BISECT_RESULTS_JSON)
    sample_bisect_results['culprit_data'] = None
    self._AddTryJob(12345, 'started', 'win_perf',
                    results_data=sample_bisect_results)
    self.testapp.get('/update_bug_with_results')

    caches = layered_cache.CachedPickledString.query().fetch()
    # Only 1 cache for bisect stats.
    self.assertEqual(1, len(caches))

  def testMapAnomaliesToMergeIntoBug(self):
    # Add anomalies.
    test_keys = map(utils.TestKey, [
        'ChromiumGPU/linux-release/scrolling-benchmark/first_paint',
        'ChromiumGPU/linux-release/scrolling-benchmark/mean_frame_time'])
    anomaly.Anomaly(
        start_revision=9990, end_revision=9997, test=test_keys[0],
        median_before_anomaly=100, median_after_anomaly=200,
        sheriff=None, bug_id=12345).put()
    anomaly.Anomaly(
        start_revision=9990, end_revision=9996, test=test_keys[0],
        median_before_anomaly=100, median_after_anomaly=200,
        sheriff=None, bug_id=54321).put()
    # Map anomalies to base(dest_bug_id) bug.
    update_bug_with_results._MapAnomaliesToMergeIntoBug(
        dest_bug_id=12345, source_bug_id=54321)
    anomalies = anomaly.Anomaly.query(
        anomaly.Anomaly.bug_id == int(54321)).fetch()
    self.assertEqual(0, len(anomalies))

  @mock.patch(
      'google.appengine.api.urlfetch.fetch',
      mock.MagicMock(side_effect=_MockFetch))
  @mock.patch.object(
      update_bug_with_results.email_template,
      'GetPerfTryJobEmailReport', mock.MagicMock(return_value=None))
  def testSendPerfTryJobEmail_EmptyEmailReport_DontSendEmail(self):
    self._AddTryJob(12345, 'started', 'win_perf', job_type='perf-try',
                    results_data=_SAMPLE_BISECT_RESULTS_JSON)
    self.testapp.get('/update_bug_with_results')
    messages = self.mail_stub.get_sent_messages()
    self.assertEqual(0, len(messages))

  @mock.patch(
      'google.appengine.api.urlfetch.fetch',
      mock.MagicMock(side_effect=_MockFetch))
  @mock.patch.object(
      update_bug_with_results.issue_tracker_service.IssueTrackerService,
      'AddBugComment')
  def testGet_InternalOnlyTryJob_AddsInternalOnlyBugLabel(
      self, mock_update_bug):
    self._AddTryJob(12345, 'started', 'win_perf',
                    results_data=_SAMPLE_BISECT_RESULTS_JSON,
                    internal_only=True)

    self.testapp.get('/update_bug_with_results')
    mock_update_bug.assert_called_once_with(
        mock.ANY, mock.ANY,
        cc_list=mock.ANY,
        merge_issue=None, labels=['Restrict-View-Google'], owner=mock.ANY)

  @mock.patch(
      'google.appengine.api.urlfetch.fetch',
      mock.MagicMock(side_effect=_MockFetch))
  @mock.patch.object(
      update_bug_with_results.issue_tracker_service, 'IssueTrackerService',
      mock.MagicMock())
  def testFYI_Send_No_Email_On_Success(self):
    stored_object.Set(
        bisect_fyi._BISECT_FYI_CONFIGS_KEY,
        bisect_fyi_test.TEST_FYI_CONFIGS)
    test_config = bisect_fyi_test.TEST_FYI_CONFIGS['positive_culprit']
    bisect_config = test_config.get('bisect_config')
    self._AddTryJob(12345, 'started', 'win_perf',
                    results_data=_SAMPLE_BISECT_RESULTS_JSON,
                    internal_only=True,
                    config=utils.BisectConfigPythonString(bisect_config),
                    job_type='bisect-fyi',
                    job_name='positive_culprit',
                    email='chris@email.com')

    self.testapp.get('/update_bug_with_results')
    messages = self.mail_stub.get_sent_messages()
    self.assertEqual(0, len(messages))

  @mock.patch(
      'google.appengine.api.urlfetch.fetch',
      mock.MagicMock(side_effect=_MockFetch))
  @mock.patch.object(
      update_bug_with_results.bisect_fyi, 'IsBugUpdated',
      mock.MagicMock(return_value=True))
  @mock.patch.object(
      update_bug_with_results.issue_tracker_service, 'IssueTrackerService',
      mock.MagicMock())
  def testFYI_Failed_Job_SendEmail(self):
    stored_object.Set(
        bisect_fyi._BISECT_FYI_CONFIGS_KEY,
        bisect_fyi_test.TEST_FYI_CONFIGS)
    test_config = bisect_fyi_test.TEST_FYI_CONFIGS['positive_culprit']
    bisect_config = test_config.get('bisect_config')
    sample_bisect_results = copy.deepcopy(_SAMPLE_BISECT_RESULTS_JSON)
    sample_bisect_results['status'] = 'failed'
    self._AddTryJob(12345, 'started', 'win_perf',
                    results_data=sample_bisect_results,
                    internal_only=True,
                    config=utils.BisectConfigPythonString(bisect_config),
                    job_type='bisect-fyi',
                    job_name='positive_culprit',
                    email='chris@email.com')

    self.testapp.get('/update_bug_with_results')
    messages = self.mail_stub.get_sent_messages()
    self.assertEqual(1, len(messages))

  @mock.patch('update_bug_with_results.quick_logger.QuickLogger.Log')
  def testUpdateQuickLog_WithJobResults_AddsQuickLog(self, mock_log):
    job = self._AddTryJob(111, 'started', 'win_perf',
                          results_data=_SAMPLE_BISECT_RESULTS_JSON)
    update_bug_with_results.UpdateQuickLog(job)
    self.assertEqual(1, mock_log.call_count)

  @mock.patch('logging.error')
  @mock.patch('update_bug_with_results.quick_logger.QuickLogger.Log')
  def testUpdateQuickLog_NoResultsData_ReportsError(
      self, mock_log, mock_logging_error):
    job = self._AddTryJob(111, 'started', 'win_perf')
    update_bug_with_results.UpdateQuickLog(job)
    self.assertEqual(0, mock_log.call_count)
    mock_logging_error.assert_called_once_with(
        'Bisect report returns empty for job id %s, bug_id %s.', 1, 111)

if __name__ == '__main__':
  unittest.main()
