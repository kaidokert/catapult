# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import collections
import itertools
import logging
import mock
import unittest

from google.appengine.api import taskqueue

from dashboard.common import testing_common
from dashboard.pinpoint.models import job_state
from dashboard.pinpoint.models import results2
from dashboard.pinpoint.models.change import change
from dashboard.pinpoint.models.change import commit
from dashboard.pinpoint.models.change import patch
from dashboard.pinpoint.models.quest import read_value
from dashboard.pinpoint.models.quest import run_test
from dashboard.services import swarming
from tracing.value import histogram_set
from tracing.value import histogram as histogram_module

_ATTEMPT_DATA = {
    "executions": [{
        "result_arguments": {
            "isolate_server": "https://isolateserver.appspot.com",
            "isolate_hash": "e26a40a0d4",
        }
    }]
}

_JOB_NO_DIFFERENCES = {
    "state": [
        {
            "attempts": [_ATTEMPT_DATA],
            "change": {},
            "comparisons": {
                'next': 'same'
            },
        },
        {
            "attempts": [_ATTEMPT_DATA],
            "change": {},
            "comparisons": {
                'next': 'same',
                'prev': 'same'
            },
        },
        {
            "attempts": [_ATTEMPT_DATA],
            "change": {},
            "comparisons": {
                'next': 'same',
                'prev': 'same'
            },
        },
        {
            "attempts": [_ATTEMPT_DATA],
            "change": {},
            "comparisons": {
                'prev': 'same'
            },
        },
    ],
    "quests": ["Test"],
}

_JOB_WITH_DIFFERENCES = {
    "state": [
        {
            "attempts": [_ATTEMPT_DATA],
            "change": {},
            "comparisons": {
                'next': 'same'
            },
        },
        {
            "attempts": [_ATTEMPT_DATA],
            "change": {},
            "comparisons": {
                'prev': 'same',
                'next': 'different'
            },
        },
        {
            "attempts": [_ATTEMPT_DATA],
            "change": {},
            "comparisons": {
                'prev': 'different',
                'next': 'different'
            },
        },
        {
            "attempts": [_ATTEMPT_DATA],
            "change": {},
            "comparisons": {
                'prev': 'different'
            },
        },
    ],
    "quests": ["Test"],
}

_JOB_MISSING_EXECUTIONS = {
    "state": [
        {
            "attempts": [_ATTEMPT_DATA, {
                "executions": []
            }],
            "change": {},
            "comparisons": {
                'next': 'same'
            },
        },
        {
            "attempts": [{
                "executions": []
            }, _ATTEMPT_DATA],
            "change": {},
            "comparisons": {
                'prev': 'same'
            },
        },
    ],
    "quests": ["Test"],
}


@mock.patch.object(results2.cloudstorage, 'listbucket')
class GetCachedResults2Test(unittest.TestCase):

  def testGetCachedResults2_Cached_ReturnsResult(self, mock_cloudstorage):
    mock_cloudstorage.return_value = ['foo']

    job = _JobStub(_JOB_WITH_DIFFERENCES, '123', job_state.PERFORMANCE)
    url = results2.GetCachedResults2(job)

    self.assertEqual(
        'https://storage.cloud.google.com/results2-public/'
        '%s.html' % job.job_id, url)

  @mock.patch.object(results2, 'ScheduleResults2Generation', mock.MagicMock())
  def testGetCachedResults2_Uncached_Fails(self, mock_cloudstorage):
    mock_cloudstorage.return_value = []

    job = _JobStub(_JOB_WITH_DIFFERENCES, '123', job_state.PERFORMANCE)
    url = results2.GetCachedResults2(job)

    self.assertIsNone(url)


class ScheduleResults2Generation2Test(unittest.TestCase):

  @mock.patch.object(results2.taskqueue, 'add')
  def testScheduleResults2Generation2_FailedPreviously(self, mock_add):
    mock_add.side_effect = taskqueue.TombstonedTaskError

    job = _JobStub(_JOB_WITH_DIFFERENCES, '123', job_state.PERFORMANCE)
    result = results2.ScheduleResults2Generation(job)
    self.assertFalse(result)

  @mock.patch.object(results2.taskqueue, 'add')
  def testScheduleResults2Generation2_AlreadyRunning(self, mock_add):
    mock_add.side_effect = taskqueue.TaskAlreadyExistsError

    job = _JobStub(_JOB_WITH_DIFFERENCES, '123', job_state.PERFORMANCE)
    result = results2.ScheduleResults2Generation(job)
    self.assertTrue(result)


@mock.patch.object(
    results2, 'open', mock.mock_open(read_data='fake_viewer'), create=True)
class GenerateResults2Test(testing_common.TestCase):

  @mock.patch.object(results2, '_FetchHistograms',
                     mock.MagicMock(return_value=['a', 'b']))
  @mock.patch.object(results2, '_GcsFileStream', mock.MagicMock())
  @mock.patch.object(results2.render_histograms_viewer,
                     'RenderHistogramsViewer')
  def testPost_Renders(self, mock_render):
    job = _JobStub(None, '123', job_state.PERFORMANCE)
    results2.GenerateResults2(job)

    mock_render.assert_called_with(['a', 'b'],
                                   mock.ANY,
                                   reset_results=True,
                                   vulcanized_html='fake_viewer')

    results = results2.CachedResults2.query().fetch()
    self.assertEqual(1, len(results))

  @mock.patch.object(results2, '_GcsFileStream', mock.MagicMock())
  @mock.patch.object(results2.render_histograms_viewer,
                     'RenderHistogramsViewer')
  @mock.patch.object(results2, '_JsonFromExecution')
  def testTypeDispatch_LegacyHistogramExecution(self, mock_json, mock_render):
    job = _JobStub(
        None, '123', job_state.PERFORMANCE,
        _JobStateFake({
            'f00c0de': [{
                'executions': [
                    read_value._ReadHistogramsJsonValueExecution(
                        'fake_filename', 'fake_metric', 'fake_grouping',
                        'fake_trace_or_story', 'avg', 'https://isolate_server',
                        'deadc0decafef00d')
                ]
            }]
        }))
    histograms = []

    def TraverseHistograms(hists, *unused_args, **unused_kw_args):
      for histogram in hists:
        histograms.append(histogram.histogram)

    mock_render.side_effect = TraverseHistograms
    histogram = histogram_module.Histogram('histogram', 'count')
    histogram.AddSample(0)
    histogram.AddSample(1)
    histogram.AddSample(2)
    expected_histogram_set = histogram_set.HistogramSet([histogram])
    mock_json.return_value = expected_histogram_set.AsDicts()
    results2.GenerateResults2(job)
    mock_render.assert_called_with(
        mock.ANY, mock.ANY, reset_results=True, vulcanized_html='fake_viewer')
    results = results2.CachedResults2.query().fetch()
    self.assertEqual(1, len(results))
    self.assertEqual(expected_histogram_set.AsDicts(), histograms)

  @mock.patch.object(results2, '_GcsFileStream', mock.MagicMock())
  @mock.patch.object(results2.render_histograms_viewer,
                     'RenderHistogramsViewer')
  @mock.patch.object(results2, '_JsonFromExecution')
  def testTypeDispatch_LegacyGraphJsonExecution(self, mock_json, mock_render):
    job = _JobStub(
        None, '123', job_state.PERFORMANCE,
        _JobStateFake({
            'f00c0de': [{
                'executions': [
                    read_value._ReadGraphJsonValueExecution(
                        'fake_filename', 'fake_chart', 'fake_trace',
                        'https://isolate_server', 'deadc0decafef00d')
                ]
            }]
        }))
    histograms = []

    def TraverseHistograms(hists, *unused_args, **unused_kw_args):
      for histogram in hists:
        histograms.append(histogram.histogram)

    mock_render.side_effect = TraverseHistograms
    mock_json.return_value = {
        'fake_chart': {
            'traces': {
                'fake_trace': ['12345.6789', '0.0']
            }
        }
    }

    results2.GenerateResults2(job)
    mock_render.assert_called_with(
        mock.ANY, mock.ANY, reset_results=True, vulcanized_html='fake_viewer')
    results = results2.CachedResults2.query().fetch()
    self.assertEqual(1, len(results))
    # TODO(dberris): check more precisely the contents of the histograms.
    self.assertEqual([mock.ANY, mock.ANY], histograms)

  @mock.patch.object(results2, '_GcsFileStream', mock.MagicMock())
  @mock.patch.object(results2.render_histograms_viewer,
                     'RenderHistogramsViewer')
  @mock.patch.object(results2, '_JsonFromExecution')
  def testTypeDispatch_ReadValueExecution(self, mock_json, mock_render):
    job = _JobStub(
        None, '123', job_state.PERFORMANCE,
        _JobStateFake({
            'f00c0de': [{
                'executions': [
                    read_value.ReadValueExecution(
                        'fake_filename', ['fake_filename'], 'fake_metric',
                        'fake_grouping_label', 'fake_trace_or_story', 'avg',
                        'fake_chart', 'https://isolate_server',
                        'deadc0decafef00d')
                ]
            }]
        }))
    histograms = []

    def TraverseHistograms(hists, *args, **kw_args):
      del args
      del kw_args
      for histogram in hists:
        histograms.append(histogram.histogram)

    mock_render.side_effect = TraverseHistograms
    histogram = histogram_module.Histogram('histogram', 'count')
    histogram.AddSample(0)
    histogram.AddSample(1)
    histogram.AddSample(2)
    expected_histogram_set = histogram_set.HistogramSet([histogram])
    mock_json.return_value = expected_histogram_set.AsDicts()
    results2.GenerateResults2(job)
    mock_render.assert_called_with(
        mock.ANY, mock.ANY, reset_results=True, vulcanized_html='fake_viewer')
    results = results2.CachedResults2.query().fetch()
    self.assertEqual(1, len(results))
    self.assertEqual(expected_histogram_set.AsDicts(), histograms)

  @mock.patch.object(results2, '_GcsFileStream', mock.MagicMock())
  @mock.patch.object(results2.render_histograms_viewer,
                     'RenderHistogramsViewer')
  @mock.patch.object(results2, '_JsonFromExecution')
  def testTypeDispatch_ReadValueExecution_MultipleChanges(
      self, mock_json, mock_render):
    job = _JobStub(
        None, '123', job_state.PERFORMANCE,
        _JobStateFake({
            'f00c0de': [{
                'executions': [
                    read_value.ReadValueExecution(
                        'fake_filename', ['fake_filename'], 'fake_metric',
                        'fake_grouping_label', 'fake_trace_or_story', 'avg',
                        'fake_chart', 'https://isolate_server',
                        'deadc0decafef00d')
                ]
            }],
            'badc0de': [{
                'executions': [
                    read_value.ReadValueExecution(
                        'fake_filename', ['fake_filename'], 'fake_metric',
                        'fake_grouping_label', 'fake_trace_or_story', 'avg',
                        'fake_chart', 'https://isolate_server',
                        'deadc0decafef00d')
                ]
            }]
        }))
    histograms = []

    def TraverseHistograms(hists, *args, **kw_args):
      del args
      del kw_args
      for histogram in hists:
        histograms.append(histogram.histogram)

    mock_render.side_effect = TraverseHistograms
    histogram_a = histogram_module.Histogram('histogram', 'count')
    histogram_a.AddSample(0)
    histogram_a.AddSample(1)
    histogram_a.AddSample(2)
    expected_histogram_set_a = histogram_set.HistogramSet([histogram_a])
    histogram_b = histogram_module.Histogram('histogram', 'count')
    histogram_b.AddSample(0)
    histogram_b.AddSample(1)
    histogram_b.AddSample(2)
    expected_histogram_set_b = histogram_set.HistogramSet([histogram_b])

    mock_json.side_effect = (expected_histogram_set_a.AsDicts(),
                             expected_histogram_set_b.AsDicts())
    results2.GenerateResults2(job)
    mock_render.assert_called_with(
        mock.ANY, mock.ANY, reset_results=True, vulcanized_html='fake_viewer')
    results = results2.CachedResults2.query().fetch()
    self.assertEqual(1, len(results))
    self.assertEqual(
        expected_histogram_set_a.AsDicts() + expected_histogram_set_b.AsDicts(),
        histograms)


  @mock.patch.object(results2, '_GcsFileStream', mock.MagicMock())
  @mock.patch.object(results2, '_InsertBQRows')
  @mock.patch.object(results2.render_histograms_viewer,
                     'RenderHistogramsViewer')
  @mock.patch.object(results2, '_JsonFromExecution')
  @mock.patch.object(swarming, 'Swarming')
  def testTypeDispatch_PushBQ(self, mock_swarming, mock_json, mock_render,
                              mock_bqinsert):

    test_execution = run_test._RunTestExecution("fake_server", None, None, None,
                                                None, None)
    test_execution._task_id = "fake_task"

    commit_a = commit.Commit("fakerepo", "fakehashA")
    change_a = change.Change([commit_a])
    commit_b = commit.Commit("fakeRepo", "fakehashB")
    patch_b = FakePatch("fakePatchServer", "fakePatchNo", "fakePatchRev")
    change_b = change.Change([commit_b], patch_b)

    job = _JobStub(
        None, 'fake_job_id', None,
        _JobStateFake({
            change_a: [{
                'executions': [
                    test_execution,
                    read_value.ReadValueExecution(
                        'fake_filename', ['fake_filename'], 'fake_metric',
                        'fake_grouping_label', 'fake_trace_or_story', 'avg',
                        'fake_chart', 'https://isolate_server',
                        'deadc0decafef00d')
                ]
            }],
            change_b: [{
                'executions': [
                    test_execution,
                    read_value.ReadValueExecution(
                        'fake_filename', ['fake_filename'], 'fake_metric',
                        'fake_grouping_label', 'fake_trace_or_story', 'avg',
                        'fake_chart', 'https://isolate_server',
                        'deadc0decafef00d')
                ]
            }],
        }))
    job.batch_id = "fake_batch_id"
    job.benchmark_arguments = {
        "benchmark": "fake_benchmark",
        "story": "fake_story"
    }
    job.configuration = "fake_configuration"
    histograms = []

    def TraverseHistograms(hists, *args, **kw_args):
      del args
      del kw_args
      for histogram in hists:
        histograms.append(histogram.histogram)

    task_mock = mock.Mock()
    task_mock.Result.return_value = {
        "bot_dimensions": {
            "device_type": "type",
            "device_os": "os"
        }
    }
    mock_swarming.return_value.Task.return_value = task_mock
    mock_render.side_effect = TraverseHistograms
    histogram = histogram_module.Histogram('histogram', 'count')
    histogram.AddSample(42)
    expected_histogram_set = histogram_set.HistogramSet([histogram])
    mock_json.return_value = expected_histogram_set.AsDicts()
    results2.GenerateResults2(job)

    # TODO: Validate args for _InsertBQRows.
    expected_rows = [{
        'change_hash': 'fakehashB',
        'story': 'fake_story',
        'deviceOS': 'os',
        'deviceModel': 'type',
        'cfg': 'fake_configuration',
        'patch_number': 'fake_patch_issue',
        'benchmark': 'fake_benchmark',
        'iteration': 0,
        'jobID': 'fake_job_id',
        'batchID': 'fake_batch_id',
        'patch_repo': 'fake_project',
        'change_repo': 'fakeRepo',
        'value': 42,
        'passing': True,
        'patch_server': 'fake_gerrit_url',
        'patch_rev': 'fake_patch_rev',
        'metric': 'histogram'
    }, {
        'change_hash': 'fakehashA',
        'story': 'fake_story',
        'deviceOS': 'os',
        'deviceModel': 'type',
        'cfg': 'fake_configuration',
        'patch_number': None,
        'benchmark': 'fake_benchmark',
        'iteration': 0,
        'jobID': 'fake_job_id',
        'batchID': 'fake_batch_id',
        'patch_repo': None,
        'change_repo': 'fakerepo',
        'value': 42,
        'passing': True,
        'patch_server': None,
        'patch_rev': None,
        'metric': 'histogram'
    }]

    mock_bqinsert.assert_called_with(
        "todo",
        "todo",
        "todo",
        expected_rows
    )


class FakePatch(
    collections.namedtuple('GerritPatch', ('server', 'change', 'revision'))):

  def BuildParameters(self):
    return {
        "patch_gerrit_url": "fake_gerrit_url",
        "project": "fake_project",
        "patch_issue": "fake_patch_issue",
        "patch_rev": "fake_patch_rev"
    }


class _AttemptFake(object):

  def __init__(self, attempt):
    self._attempt = attempt

  @property
  def executions(self):
    logging.debug('Attempt.executions = %s', self._attempt['executions'])
    return self._attempt['executions']

  def __str__(self):
    return '%s' % (self._attempt,)


class _JobStateFake(object):

  def __init__(self, attempts):
    self._attempts = {
        change: [_AttemptFake(attempt)]
        for change, attempt_list in attempts.items() for attempt in attempt_list
    }
    logging.debug('JobStateFake = %s', self._attempts)

  @property
  def _changes(self):
    changes = list(self._attempts.keys())
    logging.debug('JobStateFake._changes = %s', changes)
    return changes

  def Differences(self):

    def Pairwise(iterable):
      a, b = itertools.tee(iterable)
      next(b, None)
      return itertools.izip(a, b)

    return [(a, b) for a, b in Pairwise(self._attempts.keys())]


class _JobStub(object):

  def __init__(self, job_dict, job_id, comparison_mode, state=None):
    self._job_dict = job_dict
    self.comparison_mode = comparison_mode
    self.job_id = job_id
    self.state = state

  def AsDict(self, options=None):
    del options
    return self._job_dict
