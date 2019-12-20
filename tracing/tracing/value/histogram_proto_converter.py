# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json
import logging


UNIT_MAP = {
    'MS': 'ms',
    'MS_BEST_FIT_FORMAT': 'msBestFitFormat',
    'TS_MS': 'tsMs',
    'N_PERCENT': 'n%',
    'SIZE_IN_BYTES': 'sizeInBytes',
    'BYTES_PER_SECOND': 'bytesPerSecond',
    'J': 'J',
    'W': 'W',
    'A': 'A',
    'V': 'V',
    'HERTZ': 'Hz',
    'UNITLESS': 'unitless',
    'COUNT': 'count',
    'SIGMA': 'sigma',
}

IMPROVEMENT_DIRECTION_MAP = {
    'BIGGER_IS_BETTER': 'biggerIsBetter',
    'SMALLER_IS_BETTER': 'smallerIsBetter',
}

BOUNDARY_TYPE_MAP = {
    'LINEAR': 0,
    'EXPONENTIAL': 1,
}


def ConvertHistogram(proto_dict):
  hist = {
      'name': proto_dict['name'],
  }

  improvement_direction = proto_dict['unit'].get('improvement_direction')
  unit = UNIT_MAP[proto_dict['unit']['unit']]
  hist['unit'] = unit
  if improvement_direction and improvement_direction != 'NOT_SPECIFIED':
    hist['unit'] += '_' + IMPROVEMENT_DIRECTION_MAP[improvement_direction]

  description = proto_dict.get('description')
  if description:
    hist['description'] = description

  bin_bounds = proto_dict.get('binBoundaries')
  if bin_bounds:
    first = bin_bounds['firstBinBoundary']
    hist['binBoundaries'] = [first]
    bin_specs = bin_bounds.get('binSpecs')
    if bin_specs:
      for spec in bin_specs:
        if 'binBoundary' in spec:
          value = int(spec['binBoundary'])
          hist['binBoundaries'].append(value)
        elif 'binSpec' in spec:
          detailed_spec = spec['binSpec']
          boundary_type = BOUNDARY_TYPE_MAP[detailed_spec['boundaryType']]
          maximum = int(detailed_spec['maximumBinBoundary'])
          num_boundaries = int(detailed_spec['numBinBoundaries'])
          hist['binBoundaries'].append([boundary_type, maximum, num_boundaries])

  diagnostics = proto_dict.get('diagnostics')
  if diagnostics:
    hist['diagnostics'] = {}
    for name, diag_json in diagnostics['diagnosticMap'].items():
      diagnostic = _ConvertDiagnostic(diag_json)
      hist['diagnostics'][name] = diagnostic

  sample_values = proto_dict.get('sampleValues')
  if sample_values:
    hist['sampleValues'] = proto_dict['sampleValues']

  max_num_sample_values = proto_dict.get('maxNumSampleValues')
  if max_num_sample_values:
    hist['maxNumSampleValues'] = max_num_sample_values

  num_nans = proto_dict.get('numNans')
  if num_nans:
    hist['numNans'] = num_nans

  nan_diagnostics = proto_dict.get('nanDiagnostics')
  if nan_diagnostics:
    raise TypeError('NaN diagnostics: Not implemented yet')

  running = proto_dict.get('running')
  if running:
    hist['running'] = [running['count'], running['max'], running['meanlogs'],
                       running['mean'], running['min'], running['sum'],
                       running['variance']]

  all_bins = proto_dict.get('allBins')
  if all_bins:
    hist['allBins'] = {}
    for index_str, bin_spec in all_bins.items():
      bin_count = bin_spec['binCount']
      hist['allBins'][index_str] = [bin_count]
      bin_diagnostics = bin_spec.get('diagnosticMaps')
      if bin_diagnostics:
        dest_diagnostics = []
        for diag_map in bin_diagnostics:
          bin_diag_map = {}
          for name, diag_json in diag_map['diagnosticMap'].items():
            diagnostic = _ConvertDiagnostic(diag_json)
            bin_diag_map[name] = diagnostic
          dest_diagnostics.append(bin_diag_map)
        hist['allBins'][index_str].append(dest_diagnostics)

  summary_options = proto_dict.get('summaryOptions')
  if summary_options:
    hist['summaryOptions'] = summary_options

  return hist


def ConvertSharedDiagnostics(shared_diagnostics):
  for guid, body in shared_diagnostics.items():
    diagnostic = _ConvertDiagnostic(body)
    diagnostic['guid'] = guid
    yield diagnostic


def _ConvertDiagnostic(proto_dict):
  def _GetType(d):
    # The dict should be one key mapped to another dict, and the key is the
    # the type of the diagnostic. E.g. "genericSet": {...}.
    assert len(d) == 1, ('Expected diagnostic to be dict with just one key. '
                         'Was: %s' % proto_dict)
    return next(iter(d))

  diag_type = _GetType(proto_dict)
  if diag_type == 'genericSet':
    return _ConvertGenericSet(proto_dict)
  elif diag_type == 'sharedDiagnosticGuid':
    return proto_dict['sharedDiagnosticGuid']
  else:
    raise ValueError('%s not yet supported by proto-JSON' % diag_type)


def _ConvertGenericSet(proto_dict):
  # Values can be of any JSON type. Therefore, GenericSet values are kind of
  # double encoded - they're JSON-encoded data in a string inside of the
  # proto JSON format. Note that proto_dict is already JSON decoded, so we
  # just need to decode the values string here.
  values = []
  for value_json in proto_dict['genericSet']['values']:
    try:
      values.append(json.loads(value_json))
    except (TypeError, ValueError) as e:
      logging.exception(e)
      raise TypeError('The value %s is not valid JSON. You cannot pass naked '
                      'strings as a GenericSet value, for instance; they '
                      'have to be quoted. Therefore, 1234 is a valid value '
                      '(int), "abcd" is a valid value (string), but abcd is '
                      'not valid.' % (value_json))

  return {
      'type': 'GenericSet',
      'values': values,
  }
