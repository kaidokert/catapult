#!/usr/bin/env vpython

import os
import sys
import zlib
import json
import logging
import re
import uuid

from collections import namedtuple

_CATAPULT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..'))
_DASHBOARD_PATH = os.path.join(_CATAPULT_PATH, 'dashboard')

TRACING_PATHS = [
    'tracing/tracing',
    'tracing/tracing_build',
    'tracing/third_party/gl-matrix/dist/gl-matrix-min.js',
    'tracing/third_party/mannwhitneyu',
]

def _AddToPathIfNeeded(path):
  if path not in sys.path:
    sys.path.insert(0, path)


def _LogDebugInfo(histograms):
  hist = histograms.GetFirstHistogram()
  if not hist:
    logging.info('No histograms in data.')
    return

  log_urls = hist.diagnostics.get(reserved_infos.LOG_URLS.name)
  if log_urls:
    log_urls = list(log_urls)
    msg = 'Buildbot URL: %s' % str(log_urls)
    print(msg)
  else:
    logging.info('No LOG_URLS in data.')

  build_urls = hist.diagnostics.get(reserved_infos.BUILD_URLS.name)
  if build_urls:
    build_urls = list(build_urls)
    msg = 'Build URL: %s' % str(build_urls)
    print(msg)
  else:
    print('No BUILD_URLS in data.')

#def InlineDenseSharedDiagnostics(histograms):
#  # TODO(896856): Delete inlined diagnostics from the set
#  for hist in histograms:
#    diagnostics = hist.diagnostics
#    for name, diag in diagnostics.items():
#      if name not in histogram_helpers.SPARSE_DIAGNOSTIC_NAMES:
#        diag.Inline()

def _CheckRequest(condition, msg):
  if not condition:
    raise ValueError(msg)

def _GetDiagnosticValue(name, hist, optional=False):
  if optional:
    if name not in hist.diagnostics:
      return None

  _CheckRequest(name in hist.diagnostics,
                'Histogram [%s] missing "%s" diagnostic' % (hist.name, name))
  value = hist.diagnostics[name]
  _CheckRequest(len(value) == 1, 'Histograms must have exactly 1 "%s"' % name)
  return value.GetOnlyElement()

def ComputeRevision(histograms):
  _CheckRequest(len(histograms) > 0, 'Must upload at least one histogram')
  rev = _GetDiagnosticValue(
      reserved_infos.POINT_ID.name,
      histograms.GetFirstHistogram(),
      optional=True)

  if rev is None:
    rev = _GetDiagnosticValue(
        reserved_infos.CHROMIUM_COMMIT_POSITIONS.name,
        histograms.GetFirstHistogram(),
        optional=True)

  if rev is None:
    revision_timestamps = histograms.GetFirstHistogram().diagnostics.get(
        reserved_infos.REVISION_TIMESTAMPS.name)
    _CheckRequest(
        revision_timestamps is not None,
        'Must specify REVISION_TIMESTAMPS, CHROMIUM_COMMIT_POSITIONS,'
        ' or POINT_ID')
    rev = revision_timestamps.max_timestamp

  if not isinstance(rev, int):
    raise api_request_handler.BadRequestError('Point ID must be an integer.')

  return rev


def FindSuiteLevelSparseDiagnostics(histograms, suite_key, revision,
                                    internal_only):
  diagnostics = {}
  for hist in histograms:
    for name, diag in hist.diagnostics.items():
      if name in histogram_helpers.SUITE_LEVEL_SPARSE_DIAGNOSTIC_NAMES:
        existing_entity = diagnostics.get(name)
        if existing_entity is None:
          dictionary = dict(
              key=diag.guid,
              id=diag.guid,
              data=diag.AsDict(),
              test=suite_key,
              start_revision=revision,
              end_revision=sys.maxsize,
              name=name,
              internal_only=internal_only)

          sd = namedtuple("FakeSparseDiagnosticClass", dictionary.keys())(*dictionary.values())

          diagnostics[name] = sd
        elif existing_entity.key != diag.guid:
          raise ValueError(name +
                           ' diagnostics must be the same for all histograms')
  return list(diagnostics.values())

def FindHistogramLevelSparseDiagnostics(hist):
  diagnostics = {}
  for name, diag in hist.diagnostics.items():
    if name in histogram_helpers.HISTOGRAM_LEVEL_SPARSE_DIAGNOSTIC_NAMES:
      diagnostics[name] = diag
  return diagnostics

def _MakeTaskDict(hist,
                  test_path,
                  revision,
                  benchmark_description,
                  diagnostics,
                  completion_token=None):
  # TODO(simonhatch): "revision" is common to all tasks, as is the majority of
  # the test path
  params = {
      'test_path': test_path,
      'revision': revision,
      'benchmark_description': benchmark_description
  }

  # By changing the GUID just before serializing the task, we're making it
  # unique for each histogram. This avoids each histogram trying to write the
  # same diagnostic out (datastore contention), at the cost of copyin the
  # data. These are sparsely written to datastore anyway, so the extra
  # storage should be minimal.
  for d in diagnostics.values():
    d.ResetGuid()

  diagnostics = {k: d.AsDict() for k, d in diagnostics.items()}

  params['diagnostics'] = diagnostics
  params['data'] = hist.AsDict()

  if completion_token is not None:
    params['token'] = completion_token.key.id()

  return params

def _MakeTask(params):
  print('add_task', json.dumps(params))

def _CreateHistogramTasks(suite_path,
                          histograms,
                          revision,
                          benchmark_description,
                          completion_token=None):
  tasks = []
  duplicate_check = set()
  measurement_add_futures = []

  for hist in histograms:
    diagnostics = FindHistogramLevelSparseDiagnostics(hist)
    test_path = '%s/%s' % (suite_path, histogram_helpers.ComputeTestPath(hist))

    # Log the information here so we can see which histograms are being queued.
    logging.debug('Queueing: %s', test_path)

    if test_path in duplicate_check:
      raise api_request_handler.BadRequestError(
          'Duplicate histogram detected: %s' % test_path)

    duplicate_check.add(test_path)

    # We create one task per histogram, so that we can get as much time as we
    # need for processing each histogram per task.
    task_dict = _MakeTaskDict(hist, test_path, revision, benchmark_description,
                              diagnostics, completion_token)
    tasks.append([task_dict])

  #ndb.Future.wait_all(measurement_add_futures)

  return tasks

def ProcessHistogramSet(histograms):
  # InlineDenseSharedDiagnostics(histograms)
  master = _GetDiagnosticValue(reserved_infos.MASTERS.name,
                               histograms.GetFirstHistogram())
  bot = _GetDiagnosticValue(reserved_infos.BOTS.name,
                            histograms.GetFirstHistogram())
  benchmark = _GetDiagnosticValue(reserved_infos.BENCHMARKS.name,
                                  histograms.GetFirstHistogram())
  benchmark_description = _GetDiagnosticValue(
      reserved_infos.BENCHMARK_DESCRIPTIONS.name,
      histograms.GetFirstHistogram(),
      optional=True)

  revision = ComputeRevision(histograms)

  suite_key = ('%s/%s/%s' % (master, bot, benchmark))
  print('suite %s' % suite_key)

  internal_only = False

  # We'll skip the histogram-level sparse diagnostics because we need to
  # handle those with the histograms, below, so that we can properly assign
  # test paths.
  suite_level_sparse_diagnostic_entities = FindSuiteLevelSparseDiagnostics(
      histograms, suite_key, revision, internal_only)

  tasks = _CreateHistogramTasks(suite_key, histograms, revision,
                                  benchmark_description)

  return tasks

# Possible improvement directions for a change. An Anomaly will always have a
# direction of UP or DOWN, but a test's improvement direction can be UNKNOWN.
UP, DOWN, UNKNOWN = (0, 1, 4)

def GetUnitArgs(unit):
  unit_args = {'units': unit}
  histogram_improvement_direction = unit.split('_')[-1]
  if histogram_improvement_direction == 'biggerIsBetter':
    unit_args['improvement_direction'] = UP
  elif histogram_improvement_direction == 'smallerIsBetter':
    unit_args['improvement_direction'] = DOWN
  else:
    unit_args['improvement_direction'] = UNKNOWN
  return unit_args

def _GetStoryFromDiagnosticsDict(diagnostics):
  if not diagnostics:
    return None

  story_name = diagnostics.get(reserved_infos.STORIES.name)
  if not story_name:
    return None

  story_name = diagnostic.Diagnostic.FromDict(story_name)
  if story_name and len(story_name) == 1:
    return story_name.GetOnlyElement()
  return None

def GetOrCreateAncestors(master_name,
                         bot_name,
                         test_name,
                         internal_only=True,
                         benchmark_description='',
                         units=None,
                         improvement_direction=None,
                         unescaped_story_name=None):

  dictionary = dict(
      master_name= master_name,
      bot_name= bot_name,
      test_name= test_name,
      internal_only= internal_only,
      benchmark_description= benchmark_description,
      units= units,
      improvement_direction= improvement_direction,
      unescaped_story_name= unescaped_story_name
  )

  return namedtuple("FakeAncestorsClass", dictionary.keys())(*dictionary.values())

def _MakeRowDict(revision, test_path, tracing_histogram, stat_name=None):
  d = {}
  test_parts = test_path.split('/')
  d['master'] = test_parts[0]
  d['bot'] = test_parts[1]
  d['test'] = '/'.join(test_parts[2:])
  d['revision'] = revision
  d['supplemental_columns'] = {}

  # TODO(#3628): Remove this annotation when the frontend displays the full
  # histogram and all its diagnostics including the full set of trace urls.
  trace_url_set = tracing_histogram.diagnostics.get(
      reserved_infos.TRACE_URLS.name)
  # We don't show trace URLs for summary values in the legacy pipeline
  is_summary = reserved_infos.SUMMARY_KEYS.name in tracing_histogram.diagnostics
  #if trace_url_set and not is_summary:
  #  d['supplemental_columns']['a_tracing_uri'] = list(trace_url_set)[-1]

  # Note: annotation names should shorter than add_point._MAX_COLUMN_NAME_LENGTH.
  DIAGNOSTIC_NAMES_TO_ANNOTATION_NAMES = {
    reserved_infos.CHROMIUM_COMMIT_POSITIONS.name:
        'r_commit_pos',
    reserved_infos.V8_COMMIT_POSITIONS.name:
        'r_v8_commit_pos',
    reserved_infos.CHROMIUM_REVISIONS.name:
        'r_chromium',
    reserved_infos.V8_REVISIONS.name:
        'r_v8_rev',
    # TODO(#3545): Add r_catapult_git to Dashboard revision_info map.
    reserved_infos.CATAPULT_REVISIONS.name:
        'r_catapult_git',
    reserved_infos.ANGLE_REVISIONS.name:
        'r_angle_git',
    reserved_infos.WEBRTC_REVISIONS.name:
        'r_webrtc_git',
    reserved_infos.WEBRTC_INTERNAL_SIRIUS_REVISIONS.name:
        'r_webrtc_sirius_cl',
    reserved_infos.WEBRTC_INTERNAL_VEGA_REVISIONS.name:
        'r_webrtc_vega_cl',
    reserved_infos.WEBRTC_INTERNAL_CANOPUS_REVISIONS.name:
        'r_webrtc_canopus_cl',
    reserved_infos.WEBRTC_INTERNAL_ARCTURUS_REVISIONS.name:
        'r_webrtc_arcturus_cl',
    reserved_infos.WEBRTC_INTERNAL_RIGEL_REVISIONS.name:
        'r_webrtc_rigel_cl',
    reserved_infos.WEBRTC_INTERNAL_CAPELLA_REVISIONS.name:
        'r_webrtc_capella_cl',
    reserved_infos.FUCHSIA_GARNET_REVISIONS.name:
        'r_fuchsia_garnet_git',
    reserved_infos.FUCHSIA_PERIDOT_REVISIONS.name:
        'r_fuchsia_peridot_git',
    reserved_infos.FUCHSIA_TOPAZ_REVISIONS.name:
        'r_fuchsia_topaz_git',
    reserved_infos.FUCHSIA_ZIRCON_REVISIONS.name:
        'r_fuchsia_zircon_git',
    reserved_infos.REVISION_TIMESTAMPS.name:
        'r_revision_timestamp',
  }

  for diag_name, annotation in DIAGNOSTIC_NAMES_TO_ANNOTATION_NAMES.items():
    revision_info = tracing_histogram.diagnostics.get(diag_name)
    if not revision_info:
      continue
    if diag_name == reserved_infos.REVISION_TIMESTAMPS.name:
      value = [revision_info.min_timestamp]
    else:
      #TODO(sean) dereference these guids. Not sure where they are declared.
      value = list([revision_info])
    _CheckRequest(
        len(value) == 1,
        'RevisionInfo fields must contain at most one revision')

    d['supplemental_columns'][annotation] = value[0]

  _AddStdioUris(tracing_histogram, d)

  if stat_name is not None:
    d['value'] = tracing_histogram.statistics_scalars[stat_name].value
    d['error'] = 0.0
    if stat_name == 'avg':
      d['error'] = tracing_histogram.standard_deviation
  else:
    _PopulateNumericalFields(d, tracing_histogram)
  return d


def _AddStdioUris(tracing_histogram, row_dict):
  build_urls_diagnostic = tracing_histogram.diagnostics.get(
      reserved_infos.BUILD_URLS.name)
  if build_urls_diagnostic:

    build_tuple = ('foo', 'bar') #build_urls_diagnostic.GetOnlyElement()
    if isinstance(build_tuple, list):
      link = '[%s](%s)' % tuple(build_tuple)
      row_dict['supplemental_columns']['a_build_uri'] = link

  log_urls = tracing_histogram.diagnostics.get(reserved_infos.LOG_URLS.name)
  if not log_urls:
    return

  if len(log_urls) == 1:
    _AddStdioUri('a_stdio_uri', log_urls.GetOnlyElement(), row_dict)


def _AddStdioUri(name, link_list, row_dict):
  # TODO(#4397): Change this to an assert after infra-side fixes roll
  if isinstance(link_list, list):
    row_dict['supplemental_columns'][name] = '[%s](%s)' % tuple(link_list)
  # Support busted format until infra changes roll
  elif isinstance(link_list, basestring):
    row_dict['supplemental_columns'][name] = link_list


def _PopulateNumericalFields(row_dict, tracing_histogram):
  statistics_scalars = tracing_histogram.statistics_scalars
  for name, scalar in statistics_scalars.items():
    # We'll skip avg/std since these are already stored as value/error in rows.
    if name in ('avg', 'std'):
      continue

    row_dict['supplemental_columns']['d_%s' % name] = scalar.value

  row_dict['value'] = tracing_histogram.average
  row_dict['error'] = tracing_histogram.standard_deviation


def GetAndValidateRowProperties(row):
  """From the object received, make a dictionary of properties for a Row.

  This includes the default "value" and "error" columns as well as all
  supplemental columns, but it doesn't include "revision", and it doesn't
  include input fields that are properties of the parent TestMetadata, such as
  "units".

  This method is responsible for validating all properties that are to be
  properties of the new Row.

  Args:
    row: A dictionary obtained from the input JSON.

  Returns:
    A dictionary of the properties and property values to set when creating
    a Row. This will include "value" and "error" as well as all supplemental
    columns.

  Raises:
    BadRequestError: The properties weren't formatted correctly.
  """
  columns = {}

  # Value and error must be floating point numbers.
  if 'value' not in row:
    raise Error('No "value" given.')
  try:
    columns['value'] = float(row['value'])
  except (ValueError, TypeError):
    raise Error('Bad value for "value", should be numerical.')
  if 'error' in row:
    try:
      error = float(row['error'])
      columns['error'] = error
    except (ValueError, TypeError):
      print('Bad value for "error".')

  columns.update(_GetSupplementalColumns(row))
  return columns


# Max length for a Row property name.
_MAX_COLUMN_NAME_LENGTH = 25

# Maximum length of a value for a string property.
_STRING_COLUMN_MAX_LENGTH = 400

# Maximum number of properties for a Row.
_MAX_NUM_COLUMNS = 30

# Maximum length for a test path. This limit is required because the test path
# used as the string ID for TestContainer (the parent in the datastore for Row
# entities), and datastore imposes a maximum string ID length.
_MAX_TEST_PATH_LENGTH = 500

def _GetSupplementalColumns(row):
  """Gets a dict of supplemental columns.

  If any columns are invalid, a warning is logged and they just aren't included,
  but no exception is raised.

  Individual rows may specify up to _MAX_NUM_COLUMNS extra data, revision,
  and annotation columns. These columns must follow formatting rules for
  their type. Invalid columns are dropped with an error log, but the valid
  data will still be graphed.

  Args:
    row: A dict, possibly with the key "supplemental_columns", the value of
        which should be a dict.

  Returns:
    A dict of valid supplemental columns.
  """
  columns = {}
  for (name, value) in row.get('supplemental_columns', {}).items():
    # Don't allow too many columns
    if len(columns) == _MAX_NUM_COLUMNS:
      logging.warn('Too many columns, some being dropped.')
      break
    value = _CheckSupplementalColumn(name, value)
    if value:
      columns[name] = value
  return columns


def _CheckSupplementalColumn(name, value):
  """Returns a possibly modified value for a supplemental column, or None."""
  # Check length of column name.
  name = str(name)
  if len(name) > _MAX_COLUMN_NAME_LENGTH:
    logging.warn('Supplemental column name too long.')
    return None

  # The column name has a prefix which indicates type of value.
  if name[:2] not in ('d_', 'r_', 'a_'):
    logging.warn('Bad column name "%s", invalid prefix.', name)
    return None

  # The d_ prefix means "data column", intended to hold numbers.
  if name.startswith('d_'):
    try:
      value = float(value)
    except (ValueError, TypeError):
      logging.warn('Bad value for column "%s", should be numerical.', name)
      return None

  # The r_ prefix means "revision", and the value should look like a number,
  # a version number, or a git commit hash.
  if name.startswith('r_'):
    revision_patterns = [
        r'^\d+$',
        r'^\d+\.\d+\.\d+\.\d+$',
        r'^[A-Fa-f0-9]{40}$',
    ]
    if (not value or len(str(value)) > _STRING_COLUMN_MAX_LENGTH
        or not any(re.match(p, str(value)) for p in revision_patterns)):
      logging.warn('Bad value for revision column "%s". Value: %s', name, value)
      return None
    value = str(value)

  if name.startswith('a_'):
    # Annotation column, should be a short string.
    if len(str(value)) > _STRING_COLUMN_MAX_LENGTH:
      logging.warn('Value for "%s" too long, max length is %d.', name,
                   _STRING_COLUMN_MAX_LENGTH)
      return None

  return value


def CreateRowEntities(histogram_dict, test_metadata_key,
                      stat_names_to_test_keys, revision):
  h = histogram_module.Histogram.FromDict(histogram_dict)
  # TODO(#3564): Move this check into _PopulateNumericalFields once we
  # know that it's okay to put rows that don't have a value/error.
  if h.num_values == 0:
    return None

  rows = []

  row_dict = _MakeRowDict(revision, test_metadata_key, h)
  rows.append(GetAndValidateRowProperties(row_dict))

  #rows.append(
  #    graph_data.Row(
  #        id=revision,
  #        parent=utils.GetTestContainerKey(test_metadata_key),
  #        **add_point.GetAndValidateRowProperties(row_dict)))

  for stat_name, suffixed_key in stat_names_to_test_keys.items():
    row_dict = _MakeRowDict(revision, suffixed_key, h, stat_name=stat_name)
    rows.append(GetAndValidateRowProperties(row_dict))
    #rows.append(
    #    graph_data.Row(
    #        id=revision,
    #        parent=utils.GetTestContainerKey(suffixed_key),
    #        **add_point.GetAndValidateRowProperties(row_dict)))

  return rows

def _AddRowsFromData(params, revision, parent_test, legacy_parent_tests):
  data_dict = params['data']
  test_key = parent_test.key

  stat_names_to_test_keys = {k: v.key for k, v in legacy_parent_tests.items()}
  rows = CreateRowEntities(data_dict, test_key, stat_names_to_test_keys,
                           revision)

  return rows

def _GetOrCreateTest(name, parent_test_path, properties):
  """Either gets an entity if it already exists, or creates one.

  If the entity already exists but the properties are different than the ones
  specified, then the properties will be updated first. This implies that a
  new point is being added for an existing TestMetadata, so if the TestMetadata
  has been previously marked as deprecated then it can be updated and marked as
  non-deprecated.

  If the entity doesn't yet exist, a new one will be created with the given
  properties.

  Args:
    name: The string ID of the Test to get or create.
    parent_test_path: The test_path of the parent entity.
    properties: A dictionary of properties that should be set.

  Returns:
    An entity (which has already been put).

  Raises:
    datastore_errors.BadRequestError: Something went wrong getting the entity.
  """
  test_path = '%s/%s' % (parent_test_path, name)
  #existing = None # graph_data.TestMetadata.get_by_id(test_path)

    # Add improvement direction if this is a new test.
  if 'units' in properties and 'improvement_direction' not in properties:
    units = properties['units']
    direction = UNKNOWN #units_to_direction.GetImprovementDirection(units)
    properties['improvement_direction'] = direction
  elif 'units' not in properties or properties['units'] is None:
    properties['improvement_direction'] = anomaly.UNKNOWN

  dictionary = dict(id=test_path, test_path=test_path, **properties)
  return namedtuple("FakeTestClass", dictionary.keys())(*dictionary.values())


def GetOrCreateAncestors(master_name,
                         bot_name,
                         test_name,
                         internal_only=True,
                         benchmark_description='',
                         units=None,
                         improvement_direction=None,
                         unescaped_story_name=None):
  """Gets or creates all parent Master, Bot, TestMetadata entities for a Row."""


  master_entity = {'key': master_name}
  #            _GetOrCreateMaster(master_name)
  #_GetOrCreateBot(bot_name, master_entity.key, internal_only)

  # Add all ancestor tests to the datastore in order.
  ancestor_test_parts = test_name.split('/')

  test_path = '%s/%s' % (master_name, bot_name)
  suite = None
  for index, ancestor_test_name in enumerate(ancestor_test_parts):
    # Certain properties should only be updated if the TestMetadata is for a
    # leaf test.
    is_leaf_test = (index == len(ancestor_test_parts) - 1)
    test_properties = {
        'units': units if is_leaf_test else None,
        'internal_only': internal_only,
    }
    if is_leaf_test and improvement_direction is not None:
      test_properties['improvement_direction'] = improvement_direction
    if is_leaf_test and unescaped_story_name is not None:
      test_properties['unescaped_story_name'] = unescaped_story_name
    test_properties['description'] = benchmark_description
    test_properties['key'] = test_path
    ancestor_test = _GetOrCreateTest(ancestor_test_name, test_path,
                                     test_properties)
    if index == 0:
      suite = ancestor_test
    test_path = ancestor_test.test_path
  #if benchmark_description and suite.description != benchmark_description:
  #  suite.description = benchmark_description
  return ancestor_test

all_diagnostics = {}

def FindOrInsertDiagnostics(new_entities, test, rev, last_rev):
  ret = {}
  for new_entity in new_entities:
    if new_entity.guid in all_diagnostics:
      ret[new_entity_id] = all_diagnostics[new_entity.guid]
    else:
      all_diagnostics[new_entity.guid] = new_entity
      ret[new_entity.guid] = new_entity

  return ret

def ProcessDiagnostics(diagnostic_data, revision, test_key, internal_only):
  if not diagnostic_data:
    return

  diagnostic_entities = []
  for name, diagnostic_datum in diagnostic_data.items():
    guid = diagnostic_datum['guid']
    #dictionary = dict(
    #        id=guid,
    #        guid=guid,
    #        name=name,
    #        data=diagnostic_datum,
    #        test=test_key,
    #        start_revision=revision,
    #        end_revision=sys.maxsize,
    #        internal_only=internal_only)
    #new_diagnostic = namedtuple("FakeDiagnosticClass", dictionary.keys())(*dictionary.values())
    new_diagnostic = diagnostic.Diagnostic.FromDict(diagnostic_datum) #.keys())(*dictionary.values())
    diagnostic_entities.append(new_diagnostic)

  suite_key = '/'.join(test_key.split('/')[:3])

  #last_added = yield histogram.HistogramRevisionRecord.GetLatest(suite_key)
  #assert last_added

  new_guids_to_existing_diagnostics = FindOrInsertDiagnostics(
      diagnostic_entities, test_key, revision, None) #last_added.revision)

  return new_guids_to_existing_diagnostics

def _AddHistogramFromData(params, revision, test_key, internal_only):
  data_dict = params['data']
  diagnostics = params.get('diagnostics')

  new_guids_to_existing_diagnostics = ProcessDiagnostics(
      diagnostics, revision, test_key, internal_only)

  hs = histogram_set.HistogramSet()
  hs.ImportDicts([data_dict])

  replaced_diagnostics = []
  nonreplaced_diagnostics = []

  for new_guid, existing_diagnostic in new_guids_to_existing_diagnostics.items():
    for hist in hs:
      for name, diag in hist.diagnostics.items():
        if diag.has_guid and diag.guid == new_guid:
          hist.diagnostics[name] = existing_diagnostic
          replaced_diagnostics.append(name)
    #hs.ReplaceSharedDiagnostic(
    #    new_guid, diagnostic_ref.DiagnosticRef(existing_diagnostic.guid))
    #hs.ReplaceSharedDiagnostic(new_guid, existing_diagnostic)
    #d = hist.diagnostics
  for name, diag in diagnostics.items():
    if name not in replaced_diagnostics:
      nonreplaced_diagnostics.append(name)


  #for name in replaced_diagnostics:
  #  for hist in hs:

  # This is always 1. I think.

  hist = hs.GetFirstHistogram()
  #data = hist.AsDict()
  #for name in replaced_diagnostics:
  return hist

class SetEncoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, set) or isinstance(obj, generic_set.GenericSet):
      return list(obj)
    return json.JSONEncoder.default(self, obj)

def _ProcessRowAndHistogram(params):
  revision = int(params['revision'])
  test_path = params['test_path']
  benchmark_description = params['benchmark_description']
  data_dict = params['data']

  hist = histogram_module.Histogram.FromDict(data_dict)

  print('processing test_path: %s' % test_path)
  print('hist.num_values: %s' % hist.num_values)
  if hist.num_values == 0:
    return []
  test_path_parts = test_path.split('/')
  master = test_path_parts[0]
  bot = test_path_parts[1]
  benchmark_name = test_path_parts[2]
  histogram_name = test_path_parts[3]
  if len(test_path_parts) > 4:
    rest = '/'.join(test_path_parts[4:])
  else:
    rest = None
  full_test_name = '/'.join(test_path_parts[2:])
  internal_only = False #graph_data.Bot.GetInternalOnlySync(master, bot)
  extra_args = GetUnitArgs(hist.unit)

  unescaped_story_name = _GetStoryFromDiagnosticsDict(params.get('diagnostics'))

  # parent_test and all this stuff should be dimensions, not keys.
  parent_test = GetOrCreateAncestors(
      master,
      bot,
      full_test_name,
      internal_only=internal_only,
      unescaped_story_name=unescaped_story_name,
      benchmark_description=benchmark_description,
      **extra_args)
  test_key = parent_test.key

  statistics_scalars = hist.statistics_scalars
  legacy_parent_tests = {}

  print("processing %d statistics" % len(statistics_scalars))
  dims = {
      'benchmark': benchmark_name,
      'master': master,
      'bot': bot,
      'revision': revision
  }
  metrics = {}

  for stat_name, scalar in statistics_scalars.items():
    if histogram_helpers.ShouldFilterStatistic(histogram_name, benchmark_name,
                                               stat_name):
      print('skipping aggregate function: %s' % stat_name)
      continue
    extra_args = GetUnitArgs(scalar.unit)
    suffixed_name = '%s/%s_%s' % (benchmark_name, histogram_name, stat_name)
    if rest is not None:
      suffixed_name += '/' + rest
    metrics[histogram_name] = {
                               'value': scalar.value,
                               'aggregate_function': stat_name,
                               }

    legacy_parent_tests[stat_name] = GetOrCreateAncestors(
        master,
        bot,
        suffixed_name,
        internal_only=internal_only,
        unescaped_story_name=unescaped_story_name,
        **extra_args)

    h = _AddHistogramFromData(params, revision, test_key, internal_only)
    for name, diag in h.diagnostics.items():
      if not isinstance(diag, diagnostic_ref.DiagnosticRef):
        dims[name] = diag

    # Output isn't quite right yet. There are multiple storyies for a single
    # metric, which doesn't make sense.
    print("dims:\n%s" % json.dumps(dims, indent=2, cls=SetEncoder))
    print("metrics:\n%s" % json.dumps(metrics, indent=2, cls=SetEncoder))


def ProcessHistogram(params):
  for p in params:
    _ProcessRowAndHistogram(p)

if __name__ == '__main__':
  _AddToPathIfNeeded(_CATAPULT_PATH)
  _AddToPathIfNeeded(_DASHBOARD_PATH)

  for path in TRACING_PATHS:
    sys.path.append(os.path.join(_CATAPULT_PATH, os.path.normpath(path)))

  sys.path.append(os.path.join(_CATAPULT_PATH, os.path.normpath('third_party/ijson')))

  from hooks import install
  if '--no-install-hooks' in sys.argv:
    sys.argv.remove('--no-install-hooks')
  else:
    install.InstallHooks()

  from catapult_build import run_with_typ
  import ijson

  from tracing.value import histogram_set
  from tracing.value import histogram as histogram_module
  from tracing.value.diagnostics import reserved_infos
  from tracing.value.diagnostics import diagnostic
  from tracing.value.diagnostics import diagnostic_ref
  from tracing.value.diagnostics import generic_set

  from dashboard.common import histogram_helpers

  histograms = histogram_set.HistogramSet()

  infile = open('histdata', 'rb').read()
  decompressed_file = zlib.decompress(infile)
  histogram_dicts = json.loads(decompressed_file)
  histograms.ImportDicts(histogram_dicts)
  histograms.DeduplicateDiagnostics()
  _LogDebugInfo(histograms)

  tasks = ProcessHistogramSet(histograms)

  print("Processing %d histograms" % len(tasks))
  for params in tasks:
    ProcessHistogram(params)

  # Now, do the add_histograms_queue logic for each element of tasks list
  # by just iterating over it rather than queueing.


    #import dashboard
  #return_code = run_with_typ.Run(
  #    os.path.join(_DASHBOARD_PATH, 'dashboard'),
  #    path=dashboard.PathsForTesting())
  #sys.exit(return_code)
