# Copyright (c) 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""TODO(abennetts): DO NOT SUBMIT without one-line documentation for split_by_timestamp.

TODO(abennetts): DO NOT SUBMIT without a detailed description of split_by_timestamp.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import google_type_annotations
from __future__ import print_function

import datetime

import apache_beam as beam
from google.cloud.datastore import client as ds_client
from google.cloud.datastore import query as ds_query


class ReadTimestampRangeFromDatastore(beam.PTransform):
  """A ReadFromDatastore alternative for fetching all entities in a timestamp range."""

  def __init__(self,
               query_params,
               min_timestamp,
               max_timestamp=None,
               step=datetime.timedelta(days=1)):
    super(ReadTimestampRangeFromDatastore, self).__init__()
    self._query_params = query_params
    self._min_timestamp = min_timestamp
    if max_timestamp is None:
      max_timestamp = datetime.datetime.now()
    self._max_timestamp = max_timestamp
    self._step = step

  def expand(self, pcoll):  # pylint: disable=invalid-name
    return (pcoll.pipeline
            | 'UserSplits' >> beam.Create(list(self._Splits()))
            | 'ReadRows' >> ParDo(
                ReadTimestampRangeFromDatastore._QueryFn(self._query_params))
           )

  class _QueryFn(beam.DoFn):
    def __init__(self, query_params):
      super(ReadTimestampRangeFromDatastore._QueryFn, self).__init__()
      self._query_params = query_params

    def process(self, start_end, *unused_args,  # pylint: disable=invalid-name
                **unused_kwargs):
      start, end = start_end
      client = ds_client.Client(project=self._query_params['project'])
      query = ds_query.Query(client=client, **self._query_params)
      query.add_filter('timestamp', '>=', start)
      query.add_filter('timestamp', '<', end)
      for entity in query.fetch(client=client):
        yield entity

  def _Splits(self):
    start = self._min_timestamp
    while True:
      end = start + self._step
      yield (start, end)

      if end >= self._max_timestamp:
        break
      start = end

