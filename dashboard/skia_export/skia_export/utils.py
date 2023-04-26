# Copyright (c) 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import math

import apache_beam as beam


def FloatHack(f):
  """Workaround BQ streaming inserts not supporting inf and NaN values.

  Somewhere between Beam and the BigQuery streaming inserts API infinities and
  NaNs break if passed as is, apparently because JSON cannot represent these
  values natively.  Fortunately BigQuery appears happy to cast string values
  into floats, so we just have to intercept these values and substitute strings.

  Nones, and floats other than inf and NaN, are returned unchanged.
  """
  if f is None:
    return None
  if math.isinf(f):
    return 'inf' if f > 0 else '-inf'
  if math.isnan(f):
    return 'NaN'
  return f


def PrintCounters(pipeline_result):
  """Print pipeline counters to stdout.

  Useful for seeing metrics when running pipelines directly rather than in
  Dataflow.
  """
  try:
    metrics = pipeline_result.metrics().query()
  except ValueError:
    # Don't crash if there are no metrics, e.g. if we were run with
    # --template_location, which stages a job template but does not run the job.
    return
  for counter in metrics['counters']:
    print('Counter: ' + repr(counter))
    print('  = ' + str(counter.result))
