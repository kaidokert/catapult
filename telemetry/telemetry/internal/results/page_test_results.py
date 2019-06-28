# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import collections
import copy
import datetime
import json
import logging
import os
import random
import shutil
import sys
import tempfile
import time
import traceback
import uuid

import multiprocessing
from multiprocessing.dummy import Pool as ThreadPool

from py_utils import cloud_storage  # pylint: disable=import-error

from telemetry import value as value_module
from telemetry.internal.results import chart_json_output_formatter
from telemetry.internal.results import html_output_formatter
from telemetry.internal.results import progress_reporter as reporter_module
from telemetry.internal.results import story_run
from telemetry.value import common_value_helpers
from telemetry.value import trace

from tracing.metrics import metric_runner
from tracing.trace_data import trace_data
from tracing.value import convert_chart_json
from tracing.value import histogram_set
from tracing.value.diagnostics import all_diagnostics
from tracing.value.diagnostics import reserved_infos

_TEN_MINUTES = 60*10


def _TraceCanonicalName(run, label):
  if label is None:
    return '%s_%s_%s.html' % (
        run.story.file_safe_name,
        run.start_datetime.strftime('%Y-%m-%d_%H-%M-%S'),
        random.randint(1, 1e5))
  else:
    return '%s_%s_%s_%s.html' % (
        run.story.file_safe_name,
        label,
        run.start_datetime.strftime('%Y-%m-%d_%H-%M-%S'),
        random.randint(1, 1e5))


def _SerializeAndUploadHtmlTrace(run, html_trace_name, label, bucket):
  html_trace = run.GetArtifact(html_trace_name)
  if html_trace is None:
    trace_files = [art.local_path for art in run.IterArtifacts('trace')]
    with run.CaptureArtifact(html_trace_name) as html_path:
      trace_data.SerializeAsHtml(trace_files, html_path)

  html_trace = run.GetArtifact(html_trace_name)
  if bucket is not None and html_trace.url is None:
    remote_name = _TraceCanonicalName(run, label)
    cloud_url = cloud_storage.Insert(bucket, remote_name, html_trace.local_path)
    sys.stderr.write(
        'View generated trace files online at %s for story %s\n' % (
            cloud_url, run.story.name))
    html_trace.SetUrl(cloud_url)

  return html_trace


def _ComputeMetricsInPool(run, html_trace_name, label=None, bucket=None):
  story_name = run.story.name
  try:
    retvalue = {
        'run': run,
        'fail': [],
        'histogram_dicts': None,
        'scalars': []
    }
    extra_import_options = {
        'trackDetailedModelStats': True
    }

    html_trace = _SerializeAndUploadHtmlTrace(
        run, html_trace_name, label, bucket)
    trace_size_in_mib = os.path.getsize(html_trace.local_path) / (2 ** 20)
    # Bails out on trace that are too big. See crbug.com/812631 for more
    # details.
    if trace_size_in_mib > 400:
      retvalue['fail'].append(
          '%s: Trace size is too big: %s MiB' % (story_name, trace_size_in_mib))
      return retvalue

    logging.info('%s: Starting to compute metrics on trace.', story_name)
    start = time.time()
    # This timeout needs to be coordinated with the Swarming IO timeout for the
    # task that runs this code. If this timeout is longer or close in length
    # to the swarming IO timeout then we risk being forcibly killed for not
    # producing any output. Note that this could be fixed by periodically
    # outputing logs while waiting for metrics to be calculated.
    timeout = _TEN_MINUTES
    mre_result = metric_runner.RunMetricOnSingleTrace(
        html_trace.local_path, run.tbm_metrics,
        extra_import_options, canonical_url=html_trace.url,
        timeout=timeout)
    logging.info('%s: Computing metrics took %.3f seconds.' % (
        story_name, time.time() - start))

    if mre_result.failures:
      for f in mre_result.failures:
        retvalue['fail'].append('%s: %s' % (story_name, str(f)))

    histogram_dicts = mre_result.pairs.get('histograms', [])
    retvalue['histogram_dicts'] = histogram_dicts

    scalars = []
    for d in mre_result.pairs.get('scalars', []):
      scalars.append(common_value_helpers.TranslateScalarValue(
          d, run.story))
    retvalue['scalars'] = scalars
    return retvalue
  except Exception as e:  # pylint: disable=broad-except
    # logging exception here is the only way to get a stack trace since
    # multiprocessing's pool implementation does not save that data. See
    # crbug.com/953365.
    logging.error('%s: Exception while calculating metric', story_name)
    logging.exception(e)
    raise


class TelemetryInfo(object):
  def __init__(self, benchmark_name, benchmark_description, results_label=None,
               upload_bucket=None, output_dir=None):
    self._benchmark_name = benchmark_name
    self._benchmark_start_us = time.time() * 1e6
    self._benchmark_interrupted = False
    self._benchmark_descriptions = benchmark_description
    self._label = results_label
    self._story_name = None
    self._story_tags = set()
    self._story_grouping_keys = {}
    self._storyset_repeat_counter = 0
    self._trace_start_us = None
    self._upload_bucket = upload_bucket
    self._trace_remote_path = None
    self._output_dir = output_dir
    self._trace_local_path = None
    self._had_failures = None

  @property
  def upload_bucket(self):
    return self._upload_bucket

  @property
  def benchmark_name(self):
    return self._benchmark_name

  @property
  def benchmark_start_us(self):
    return self._benchmark_start_us

  @property
  def benchmark_descriptions(self):
    return self._benchmark_descriptions

  @property
  def trace_start_us(self):
    return self._trace_start_us

  @property
  def benchmark_interrupted(self):
    return self._benchmark_interrupted

  @property
  def label(self):
    return self._label

  @property
  def story_display_name(self):
    return self._story_name

  @property
  def story_grouping_keys(self):
    return self._story_grouping_keys

  @property
  def story_tags(self):
    return self._story_tags

  @property
  def storyset_repeat_counter(self):
    return self._storyset_repeat_counter

  @property
  def had_failures(self):
    return self._had_failures

  def GetStoryTagsList(self):
    return list(self._story_tags) + [
        '%s:%s' % kv for kv in self._story_grouping_keys.iteritems()]

  def InterruptBenchmark(self):
    self._benchmark_interrupted = True

  def WillRunStory(self, story, storyset_repeat_counter):
    self._trace_start_us = time.time() * 1e6
    self._story_name = story.name
    self._story_grouping_keys = story.grouping_keys
    self._story_tags = story.tags
    self._storyset_repeat_counter = storyset_repeat_counter

    trace_name_suffix = '%s_%s.html' % (
        datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),
        random.randint(1, 1e5))
    if self.label:
      trace_name = '%s_%s_%s' % (
          story.file_safe_name, self.label, trace_name_suffix)
    else:
      trace_name = '%s_%s' % (
          story.file_safe_name, trace_name_suffix)

    if self._upload_bucket:
      self._trace_remote_path = trace_name

    if self._output_dir:
      self._trace_local_path = os.path.abspath(os.path.join(
          self._output_dir, trace_name))

  @property
  def trace_local_path(self):
    return self._trace_local_path

  @property
  def trace_local_url(self):
    if self._trace_local_path:
      return 'file://' + self._trace_local_path
    return None

  @property
  def trace_remote_path(self):
    return self._trace_remote_path

  @property
  def trace_remote_url(self):
    if self._trace_remote_path:
      return 'https://console.developers.google.com/m/cloudstorage/b/%s/o/%s' % (
          self._upload_bucket, self._trace_remote_path)
    return None

  @property
  def trace_url(self):
    # This is MRE's canonicalUrl.
    if self._upload_bucket is None:
      return self.trace_local_url
    return self.trace_remote_url


class PageTestResults(object):
  HTML_TRACE_NAME = 'trace.html'

  def __init__(self, output_formatters=None, progress_reporter=None,
               output_dir=None, should_add_value=None, benchmark_name=None,
               benchmark_description=None, benchmark_enabled=True,
               upload_bucket=None, results_label=None):
    """
    Args:
      output_formatters: A list of output formatters. The output
          formatters are typically used to format the test results, such
          as CsvOutputFormatter, which output the test results as CSV.
      progress_reporter: An instance of progress_reporter.ProgressReporter,
          to be used to output test status/results progressively.
      output_dir: A string specifying the directory where to store the test
          artifacts, e.g: trace, videos, etc.
      should_add_value: A function that takes two arguments: a value name and
          a boolean (True when the value belongs to the first run of the
          corresponding story). It returns True if the value should be added
          to the test results and False otherwise.
      benchmark_name: A string with the name of the currently running benchmark.
      benchmark_description: A string with a description of the currently
          running benchmark.
      benchmark_enabled: A boolean indicating whether the benchmark to run
          is enabled. (Some output formats need to produce special output for
          disabled benchmarks).
      upload_bucket: A string identifting a cloud storage bucket where to
          upload artifacts.
      results_label: A string that serves as an identifier for the current
          benchmark run.
    """
    super(PageTestResults, self).__init__()
    self._progress_reporter = (
        progress_reporter if progress_reporter is not None
        else reporter_module.ProgressReporter())
    self._output_formatters = (
        output_formatters if output_formatters is not None else [])
    self._output_dir = output_dir
    if should_add_value is not None:
      self._should_add_value = should_add_value
    else:
      self._should_add_value = lambda v, is_first: True

    self._current_page_run = None
    self._all_page_runs = []
    self._all_stories = set()
    self._representative_value_for_each_value_name = {}
    self._all_summary_values = []

    self._histograms = histogram_set.HistogramSet()

    self._benchmark_name = benchmark_name or '(unknown benchmark)'
    self._benchmark_description = benchmark_description or ''
    self._telemetry_info = TelemetryInfo(
        benchmark_name=self._benchmark_name,
        benchmark_description=self._benchmark_description,
        results_label=results_label,
        upload_bucket=upload_bucket, output_dir=output_dir)

    # State of the benchmark this set of results represents.
    self._benchmark_enabled = benchmark_enabled

    self._histogram_dicts_to_add = []

    # Mapping of the stories that have run to the number of times they have run
    # This is necessary on interrupt if some of the stories did not run.
    self._story_run_count = {}

  @property
  def telemetry_info(self):
    return self._telemetry_info

  @property
  def benchmark_name(self):
    return self._benchmark_name

  @property
  def benchmark_description(self):
    return self._benchmark_description

  @property
  def output_dir(self):
    return self._output_dir

  def AsHistogramDicts(self):
    return self._histograms.AsDicts()

  def PopulateHistogramSet(self):
    if len(self._histograms):
      return

    # We ensure that html traces are serialized and uploaded if necessary
    for run in self.IterRunsWithTraces():
      _SerializeAndUploadHtmlTrace(
          run,
          self.HTML_TRACE_NAME,
          self.telemetry_info.label,
          self.telemetry_info.upload_bucket)

    chart_json = chart_json_output_formatter.ResultsAsChartDict(self)
    info = self.telemetry_info
    chart_json['label'] = info.label
    chart_json['benchmarkStartMs'] = info.benchmark_start_us / 1000.0

    file_descriptor, chart_json_path = tempfile.mkstemp()
    os.close(file_descriptor)
    json.dump(chart_json, file(chart_json_path, 'w'))

    vinn_result = convert_chart_json.ConvertChartJson(chart_json_path)

    os.remove(chart_json_path)

    if vinn_result.returncode != 0:
      logging.error('Error converting chart json to Histograms:\n' +
                    vinn_result.stdout)
      return []
    self._histograms.ImportDicts(json.loads(vinn_result.stdout))
    self._histograms.ImportDicts(self._histogram_dicts_to_add)

  def __copy__(self):
    cls = self.__class__
    result = cls.__new__(cls)
    for k, v in self.__dict__.items():
      if isinstance(v, collections.Container):
        v = copy.copy(v)
      setattr(result, k, v)
    return result

  @property
  def all_page_specific_values(self):
    values = []
    for run in self._IterAllStoryRuns():
      values += run.values
    return values

  @property
  def all_summary_values(self):
    return self._all_summary_values

  @property
  def current_page(self):
    assert self._current_page_run, 'Not currently running test.'
    return self._current_page_run.story

  @property
  def current_page_run(self):
    assert self._current_page_run, 'Not currently running test.'
    return self._current_page_run

  @property
  def all_page_runs(self):
    return self._all_page_runs

  @property
  def pages_that_succeeded(self):
    """Returns the set of pages that succeeded.

    Note: This also includes skipped pages.
    """
    pages = set(run.story for run in self.all_page_runs)
    pages.difference_update(self.pages_that_failed)
    return pages

  @property
  def pages_that_succeeded_and_not_skipped(self):
    """Returns the set of pages that succeeded and werent skipped."""
    skipped_story_names = set(
        run.story.name for run in self._IterAllStoryRuns() if run.skipped)
    pages = self.pages_that_succeeded
    for page in self.pages_that_succeeded:
      if page.name in skipped_story_names:
        pages.remove(page)
    return pages

  @property
  def pages_that_failed(self):
    """Returns the set of failed pages."""
    failed_pages = set()
    for run in self.all_page_runs:
      if run.failed:
        failed_pages.add(run.story)
    return failed_pages

  @property
  def had_successes_not_skipped(self):
    return bool(self.pages_that_succeeded_and_not_skipped)

  @property
  def had_failures(self):
    return any(run.failed for run in self.all_page_runs)

  @property
  def num_failed(self):
    return sum(1 for run in self.all_page_runs if run.failed)

  @property
  def had_skips(self):
    return any(run.skipped for run in self._IterAllStoryRuns())

  def _IterAllStoryRuns(self):
    for run in self._all_page_runs:
      yield run
    if self._current_page_run:
      yield self._current_page_run

  def CleanUp(self):
    """Clean up any TraceValues contained within this results object."""
    for run in self._all_page_runs:
      for v in run.values:
        if isinstance(v, trace.TraceValue):
          v.CleanUp()
          run.values.remove(v)

  def CloseOutputFormatters(self):
    """
    Clean up any open output formatters contained within this results object
    """
    for output_formatter in self._output_formatters:
      output_formatter.output_stream.close()

  def __enter__(self):
    return self

  def __exit__(self, _, __, ___):
    self.CleanUp()
    self.CloseOutputFormatters()

  def WillRunPage(self, page, storyset_repeat_counter=0):
    assert not self._current_page_run, 'Did not call DidRunPage.'
    self._current_page_run = story_run.StoryRun(page, self._output_dir)
    self._progress_reporter.WillRunPage(self)
    self.telemetry_info.WillRunStory(
        page, storyset_repeat_counter)

  def DidRunPage(self, page):  # pylint: disable=unused-argument
    """
    Args:
      page: The current page under test.
    """
    assert self._current_page_run, 'Did not call WillRunPage.'
    self._current_page_run.Finish()
    self._progress_reporter.DidRunPage(self)
    self._all_page_runs.append(self._current_page_run)
    story = self._current_page_run.story
    self._all_stories.add(story)
    if bool(self._story_run_count.get(story)):
      self._story_run_count[story] += 1
    else:
      self._story_run_count[story] = 1
    self._current_page_run = None

  def _AddPageResults(self, result):
    self._current_page_run = result['run']
    try:
      for fail in result['fail']:
        self.Fail(fail)
      if result['histogram_dicts']:
        self.ImportHistogramDicts(result['histogram_dicts'])
      for scalar in result['scalars']:
        self.AddValue(scalar)
    finally:
      self._current_page_run = None

  def ComputeTimelineBasedMetrics(self):
    assert not self._current_page_run, 'Cannot compute metrics while running.'
    def _GetCpuCount():
      try:
        return multiprocessing.cpu_count()
      except NotImplementedError:
        # Some platforms can raise a NotImplementedError from cpu_count()
        logging.warn('cpu_count() not implemented.')
        return 8

    # Note that this is speculatively halved as an attempt to fix
    # crbug.com/953365.
    threads_count = min(_GetCpuCount()/2 or 1, len(self._all_page_runs))
    pool = ThreadPool(threads_count)
    metrics_runner = lambda run: _ComputeMetricsInPool(
        run,
        self.HTML_TRACE_NAME,
        self.telemetry_info.label,
        self.telemetry_info.upload_bucket)

    try:
      for result in pool.imap_unordered(metrics_runner,
                                        self.IterRunsWithTraces()):
        self._AddPageResults(result)
    finally:
      pool.terminate()
      pool.join()

  def InterruptBenchmark(self, stories, repeat_count):
    self.telemetry_info.InterruptBenchmark()
    # If we are in the middle of running a page it didn't finish
    # so reset the current page run
    self._current_page_run = None
    for story in stories:
      num_runs = repeat_count - self._story_run_count.get(story, 0)
      for i in xrange(num_runs):
        self._GenerateSkippedStoryRun(story, i)

  def _GenerateSkippedStoryRun(self, story, storyset_repeat_counter):
    self.WillRunPage(story, storyset_repeat_counter)
    self.Skip('Telemetry interrupted', is_expected=False)
    self.DidRunPage(story)

  def AddHistogram(self, hist):
    if self._ShouldAddHistogram(hist):
      diags = self._GetDiagnostics()
      for diag in diags.itervalues():
        self._histograms.AddSharedDiagnostic(diag)
      self._histograms.AddHistogram(hist, diags)

  def _GetDiagnostics(self):
    """Get benchmark metadata as histogram diagnostics."""
    info = self._telemetry_info
    diag_values = [
        (reserved_infos.BENCHMARKS, info.benchmark_name),
        (reserved_infos.BENCHMARK_START, info.benchmark_start_us),
        (reserved_infos.BENCHMARK_DESCRIPTIONS, info.benchmark_descriptions),
        (reserved_infos.LABELS, info.label),
        (reserved_infos.HAD_FAILURES, info.had_failures),
        (reserved_infos.STORIES, info._story_name),
        (reserved_infos.STORY_TAGS, info.GetStoryTagsList()),
        (reserved_infos.STORYSET_REPEATS, info.storyset_repeat_counter),
        (reserved_infos.TRACE_START, info.trace_start_us),
        (reserved_infos.TRACE_URLS, info.trace_url)
    ]

    diags = {}
    for diag, value in diag_values:
      if value is None or value == []:
        continue
      if diag.type == 'GenericSet' and not isinstance(value, list):
        value = [value]
      elif diag.type == 'DateRange':
        # We store timestamps in microseconds, DateRange expects milliseconds.
        value = value / 1e3  # pylint: disable=redefined-variable-type
      diag_class = all_diagnostics.GetDiagnosticClassForName(diag.type)
      diags[diag.name] = diag_class(value)
    return diags

  def ImportHistogramDicts(self, histogram_dicts, import_immediately=True):
    histograms = histogram_set.HistogramSet()
    histograms.ImportDicts(histogram_dicts)
    histograms.FilterHistograms(lambda hist: not self._ShouldAddHistogram(hist))
    dicts_to_add = histograms.AsDicts()

    # For measurements that add both TBMv2 and legacy metrics to results, we
    # want TBMv2 histograms be imported at the end, when PopulateHistogramSet is
    # called so that legacy histograms can be built, too, from scalar value
    # data.
    #
    # Measurements that add only TBMv2 metrics and also add scalar value data
    # should set import_immediately to True (i.e. the default behaviour) to
    # prevent PopulateHistogramSet from trying to build more histograms from the
    # scalar value data.
    if import_immediately:
      self._histograms.ImportDicts(dicts_to_add)
    else:
      self._histogram_dicts_to_add.extend(dicts_to_add)

  def _ShouldAddHistogram(self, hist):
    assert self._current_page_run, 'Not currently running test.'
    is_first_result = (
        self._current_page_run.story not in self._all_stories)
    # TODO(eakuefner): Stop doing this once AddValue doesn't exist
    stat_names = [
        '%s_%s' % (hist.name, s) for  s in hist.statistics_scalars.iterkeys()]
    return any(self._should_add_value(s, is_first_result) for s in stat_names)

  def AddValue(self, value):
    assert self._current_page_run, 'Not currently running test.'
    assert self._benchmark_enabled, 'Cannot add value to disabled results'

    self._ValidateValue(value)
    is_first_result = (
        self._current_page_run.story not in self._all_stories)

    if not (isinstance(value, trace.TraceValue) or
            self._should_add_value(value.name, is_first_result)):
      return
    self._current_page_run.AddValue(value)

  def AddSharedDiagnosticToAllHistograms(self, name, diagnostic):
    self._histograms.AddSharedDiagnosticToAllHistograms(name, diagnostic)

  def Fail(self, failure):
    """Mark the current story run as failed.

    This method will print a GTest-style failure annotation and mark the
    current story run as failed.

    Args:
      failure: A string or exc_info describing the reason for failure.
    """
    # TODO(#4258): Relax this assertion.
    assert self._current_page_run, 'Not currently running test.'
    if isinstance(failure, basestring):
      failure_str = 'Failure recorded for page %s: %s' % (
          self._current_page_run.story.name, failure)
    else:
      failure_str = ''.join(traceback.format_exception(*failure))
    logging.error(failure_str)
    self._current_page_run.SetFailed(failure_str)

  def Skip(self, reason, is_expected=True):
    assert self._current_page_run, 'Not currently running test.'
    self._current_page_run.Skip(reason, is_expected)

  def CreateArtifact(self, name):
    assert self._current_page_run, 'Not currently running test.'
    return self._current_page_run.CreateArtifact(name)

  def CaptureArtifact(self, name):
    assert self._current_page_run, 'Not currently running test.'
    return self._current_page_run.CaptureArtifact(name)

  def AddTraces(self, traces, tbm_metrics=None):
    """Associate some recorded traces with the current story run.

    Args:
      traces: A TraceDataBuilder object with traces recorded from all
        tracing agents.
      tbm_metrics: Optional list of TBMv2 metrics to be computed from the
        input traces.
    """
    assert self._current_page_run, 'Not currently running test.'
    for part, filename in traces.IterTraceParts():
      with self.CaptureArtifact('trace/' + part) as artifact_path:
        shutil.copy(filename, artifact_path)
    if tbm_metrics:
      self._current_page_run.SetTbmMetrics(tbm_metrics)

  def AddSummaryValue(self, value):
    assert value.page is None
    self._ValidateValue(value)
    self._all_summary_values.append(value)

  def _ValidateValue(self, value):
    assert isinstance(value, value_module.Value)
    if value.name not in self._representative_value_for_each_value_name:
      self._representative_value_for_each_value_name[value.name] = value
    representative_value = self._representative_value_for_each_value_name[
        value.name]
    assert value.IsMergableWith(representative_value)

  def PrintSummary(self):
    if self._benchmark_enabled:
      self._progress_reporter.DidFinishAllTests(self)

      # Only serialize the trace if output_format is json or html.
      if (self._output_dir and
          any(isinstance(o, html_output_formatter.HtmlOutputFormatter)
              for o in self._output_formatters)):
        for run in self.IterRunsWithTraces():
          # Just to make sure that html trace is there in artifacts dir
          _SerializeAndUploadHtmlTrace(
              run,
              self.HTML_TRACE_NAME,
              self.telemetry_info.label,
              self.telemetry_info.upload_bucket)

      for output_formatter in self._output_formatters:
        output_formatter.Format(self)
        output_formatter.PrintViewResults()
    else:
      for output_formatter in self._output_formatters:
        output_formatter.FormatDisabled(self)

  def FindValues(self, predicate):
    """Finds all values matching the specified predicate.

    Args:
      predicate: A function that takes a Value and returns a bool.
    Returns:
      A list of values matching |predicate|.
    """
    values = []
    for value in self.all_page_specific_values:
      if predicate(value):
        values.append(value)
    return values

  def FindPageSpecificValuesForPage(self, page, value_name):
    return self.FindValues(lambda v: v.page == page and v.name == value_name)

  def FindAllPageSpecificValuesNamed(self, value_name):
    return self.FindValues(lambda v: v.name == value_name)

  def FindAllTraceValues(self):
    return self.FindValues(lambda v: isinstance(v, trace.TraceValue))

  def IterRunsWithTraces(self):
    for run in self._IterAllStoryRuns():
      for _ in run.IterArtifacts('trace'):
        yield run
        break

  #TODO(crbug.com/772216): Remove this once the uploading is done by Chromium
  # test recipe.
  def UploadArtifactsToCloud(self):
    """Upload all artifacts of the test to cloud storage.

    Sets 'url' attribute of each artifact to its cloud URL.
    """
    bucket = self.telemetry_info.upload_bucket
    for run in self._all_page_runs:
      for artifact in run.IterArtifacts():
        if artifact.url is None:
          remote_name = str(uuid.uuid1())
          cloud_url = cloud_storage.Insert(
              bucket, remote_name, artifact.local_path)
          logging.info('Uploading %s of page %s to %s\n' % (
              artifact.name, run.story.name, cloud_url))
          artifact.SetUrl(cloud_url)
