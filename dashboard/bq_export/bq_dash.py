from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import datetime
import logging
import json
import math
import sys
import time

import apache_beam as beam
from apache_beam.io.gcp.bigquery import BigQueryWriteFn
from apache_beam.io.gcp.datastore.v1new.datastoreio import ReadFromDatastore
from apache_beam.io.gcp.datastore.v1new.datastoreio import types as beam_ds_types
from apache_beam.options.pipeline_options import GoogleCloudOptions
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.metrics import Metrics, MetricsFilter
from apache_beam.transforms.core import FlatMap, Map, ParDo
from apache_beam.transforms.util import ReshufflePerKey
from google.cloud.datastore import client as ds_client
from google.cloud.datastore import query as ds_query
from google.cloud.datastore import key as ds_key


## Copy of dashboard.common.utils.TestPath for google.cloud.datastore.key.Key
## rather than ndb.Key.
def TestPath(key):
  if key.kind == 'Test':
    # The Test key looks like ('Master', 'name', 'Bot', 'name', 'Test' 'name'..)
    # Pull out every other entry and join with '/' to form the path.
    return '/'.join(key.flat_path[1::2])
  assert key.kind == 'TestMetadata' or key.kind == 'TestContainer'
  return key.name


def DaysAgoTimestamp(days_ago):
  """Return a datetime for a day the given number of days in the past."""
  now = datetime.datetime.now()
  result_datetime = now - datetime.timedelta(days=days_ago)
  return result_datetime


def FloatHack(f):
  """Workaround BQ streaming inserts not supporting inf and NaN values.

  Somewhere between Beam and the BigQuery streaming inserts API infinities and
  NaNs break if passed as is, apparently because JSON cannot represent these
  values natively.  Fortunately BigQuery appears happy to cast string values
  into floats, so we just have to intercept these values and substitute strings.

  Nones, and floats other than inf and NaN, are returned unchanged.
  """
  if f is None: return None
  if math.isinf(f): return 'inf' if f > 0 else '-inf'
  if math.isnan(f): return 'NaN'
  return f


class ReadRowsForAnomalies(beam.PTransform):
  # TODO: take 'project' as a param in this transform
  # TODO: possibly replace this with simple last N days fetch like Anomaly.

  def expand(self, pcoll):
    return (pcoll
            | 'BuildRowQuery' >> Map(self._FilterForQueryRowsForAnomaly)
            # We cannot use ReadFromDatastore with query derived from dynamic
            # results, so use our code to query datastore directly.
            | 'ReadRows' >> ParDo(ReadRowsForAnomalies._QueryFn())
    )

  class _QueryFn(beam.DoFn):
    def process(self, filters, *unused_args, **unused_kwargs):
      client = ds_client.Client(project='chromeperf')
      query = ds_query.Query(client=client, kind='Row', filters=filters)
      for entity in query.fetch(client=client):
        yield entity # types.Entity.from_client_entity(entity)

  @staticmethod
  def _FilterForQueryRowsForAnomaly(k_anomaly):
    k, anomaly = k_anomaly
    # `anomaly` is a client entity for Anomaly
    test_key = anomaly['test']
    if test_key.kind == 'Test':
      row_parent_test = test_key.to_client_key()
    elif test_key.kind == 'TestMetadata':
      path_parts = test_key.name.split('/')
      key_parts = ['Master', path_parts[0], 'Bot', path_parts[1]]
      for part in path_parts[2:]:
        key_parts += ['Test', part]
      row_parent_test = ds_key.Key(*key_parts, project=test_key.project)

    # Return the query params.
    return [('parent_test', '=', row_parent_test),
            ('revision', '>=', anomaly['start_revision']),
            ('revision', '>=', anomaly['end_revision']),
           ]


def main():
  project = 'chromeperf'
  options = PipelineOptions()
  options.view_as(GoogleCloudOptions).project = project

  p = beam.Pipeline(options=options)
  entities_read = Metrics.counter('main', 'entities_read')
  failed_entity_transforms = Metrics.counter('main', 'failed_entity_transforms')
  failed_bq_rows = Metrics.counter('main', 'failed_bq_rows')

  # Query for Anomalies with timestamp >= 180 days ago.
  query = beam_ds_types.Query(
      project=project,
      kind='Anomaly',
      filters=[('timestamp', '>=', DaysAgoTimestamp(180))],
  )

  def ToClientEntity(entity):
    entities_read.inc()
    return entity.to_client_entity()

  # Read 'Anomaly' entities from datastore.
  entities = (p
              | 'ReadFromDatastore' >> ReadFromDatastore(query)
              | 'ToClientEntity(Anomaly)' >> Map(ToClientEntity)
              | beam.WithKeys(lambda v: v.key.id))

  def AnomalyEntityToRowDict(k_entity):
    k, entity = k_entity
    try:
      d = {
          'id': entity.key.id,
          # TODO: 'sheriff'
          # 'subscriptions' omitted; subscription_names is sufficient
          'subscription_names': entity.get('subscription_names', []),
          'test': TestPath(entity['test']),
          'start_revision': entity['start_revision'],
          'end_revision': entity['end_revision'],
          'display_start': entity.get('display_start'),
          'display_end': entity.get('display_end'),
          # TODO: 'ownership'
          'statistic': entity['statistic'],
          'bug_id': entity['bug_id'],
          'internal_only': entity['internal_only'],
          'timestamp': entity['timestamp'].isoformat(),
          'segment_size_before': entity.get('segment_size_before'),
          'segment_size_after': entity.get('segment_size_after'),
          'median_before_anomaly': entity.get('median_before_anomaly'),
          'median_after_anomaly': entity.get('median_after_anomaly'),
          'std_dev_before_anomaly': entity.get('std_dev_before_anomaly'),
          'window_end_revision': entity.get('window_end_revision'),
          't_statistic': FloatHack(entity.get('t_statistic')),
          'degrees_of_freedom': entity.get('degrees_of_freedom'),
          'p_value': entity.get('p_value'),
          'is_improvement': entity.get('is_improvement', False),
          'recovered': entity.get('recovered', False),
          # TODO: 'ref_test'
          'units': entity.get('units'),
          # TODO: 'recipe_bisects'
          'pinpoint_bisects': entity.get('pinpoint_bisects', []),
      }
      return [d]
    except KeyError:
      failed_entity_transforms.inc()
      return []
  anomaly_dicts = (
      entities
      | 'ConvertEntityToRow(Anomaly)' >> FlatMap(AnomalyEntityToRowDict))

  bq_anomaly_schema = {'fields': [
      {'name': 'id', 'type': 'INT64', 'mode': 'REQUIRED'},
      {'name': 'subscription_names', 'type': 'STRING', 'mode': 'REPEATED'},
      {'name': 'test', 'type': 'STRING', 'mode': 'REQUIRED'},
      {'name': 'start_revision', 'type': 'INT64', 'mode': 'REQUIRED'},
      {'name': 'end_revision', 'type': 'INT64', 'mode': 'REQUIRED'},
      {'name': 'display_start', 'type': 'INT64', 'mode': 'NULLABLE'},
      {'name': 'display_end', 'type': 'INT64', 'mode': 'NULLABLE'},
      {'name': 'statistic', 'type': 'STRING', 'mode': 'REQUIRED'},
      {'name': 'bug_id', 'type': 'INT64', 'mode': 'NULLABLE'},
      {'name': 'internal_only', 'type': 'BOOLEAN', 'mode': 'REQUIRED'},
      {'name': 'timestamp', 'type': 'TIMESTAMP', 'mode': 'REQUIRED'},
      {'name': 'segment_size_before', 'type': 'INT64', 'mode': 'NULLABLE'},
      {'name': 'segment_size_after', 'type': 'INT64', 'mode': 'NULLABLE'},
      {'name': 'median_before_anomaly', 'type': 'FLOAT', 'mode': 'NULLABLE'},
      {'name': 'median_after_anomaly', 'type': 'FLOAT', 'mode': 'NULLABLE'},
      {'name': 'std_dev_before_anomaly', 'type': 'FLOAT', 'mode': 'NULLABLE'},
      {'name': 'window_end_revision', 'type': 'INT64', 'mode': 'NULLABLE'},
      {'name': 't_statistic', 'type': 'FLOAT', 'mode': 'NULLABLE'},
      {'name': 'degrees_of_freedom', 'type': 'FLOAT', 'mode': 'NULLABLE'},
      {'name': 'p_value', 'type': 'FLOAT', 'mode': 'NULLABLE'},
      {'name': 'is_improvement', 'type': 'BOOLEAN', 'mode': 'REQUIRED'},
      {'name': 'recovered', 'type': 'BOOLEAN', 'mode': 'REQUIRED'},
      {'name': 'units', 'type': 'STRING', 'mode': 'NULLABLE'},
      {'name': 'pinpoint_bisects', 'type': 'STRING', 'mode': 'REPEATED'},
  ]}

  bq_anomalies = anomaly_dicts | 'WriteToBigQuery(anomalies)' >> beam.io.WriteToBigQuery(
      '{}:chromeperf_dashboard_data.anomalies_test'.format(project),
      schema=bq_anomaly_schema,
      method=beam.io.WriteToBigQuery.Method.STREAMING_INSERTS,
      write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE,
      create_disposition=beam.io.BigQueryDisposition.CREATE_NEVER)

  def CountFailed(element):
    failed_bq_rows.inc()
  failed_rows = bq_anomalies[BigQueryWriteFn.FAILED_ROWS]
  failed_rows | beam.Map(CountFailed)
  #failed_rows | beam.ToString.Iterables() | beam.Map(print)

  bq_row_schema = {'fields': [
      {'name': 'revision', 'type': 'INT64', 'mode': 'REQUIRED'},
      {'name': 'value', 'type': 'FLOAT', 'mode': 'REQUIRED'},
      {'name': 'error', 'type': 'FLOAT', 'mode': 'NULLABLE'},
      {'name': 'timestamp', 'type': 'TIMESTAMP', 'mode': 'REQUIRED'},
      {'name': 'parent_test', 'type': 'STRING', 'mode': 'REQUIRED'},
      {'name': 'properties', 'type': 'STRING', 'mode': 'NULLABLE'},
  ]}
  def RowEntityToRowDict(entity):
    entities_read.inc()
    try:
      d = {
          'revision': entity.key.id,
          'value': FloatHack(entity['value']),
          'error': FloatHack(entity.get('error')),
          'timestamp': entity['timestamp'].isoformat(),
          'parent_test': entity.key.parent.name,
      }
      # Add the expando properties as a JSON-encoded dict.
      properties = {}
      for key, value in entity.items():
        if key in d: continue  # skip properties with dedicated columns.
        if isinstance(value, float): value = FloatHack(value)
        properties[key] = value
      d['properties'] = json.dumps(properties) if properties else None
      return [d]
    except KeyError:
      logging.getLogger().exception('Failed to convert Row')
      failed_entity_transforms.inc()
      return []
  row_dicts = (
      entities
      | ReshufflePerKey()
      | 'ReadRows' >> ReadRowsForAnomalies()
      | 'ConvertEntityToRow(Row)' >> FlatMap(RowEntityToRowDict))

  bq_rows = row_dicts | 'WriteToBigQuery(rows)' >> beam.io.WriteToBigQuery(
      '{}:chromeperf_dashboard_data.rows_test'.format(project),
      schema=bq_row_schema,
      method=beam.io.WriteToBigQuery.Method.STREAMING_INSERTS,
      write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE,
      create_disposition=beam.io.BigQueryDisposition.CREATE_NEVER)

  print(p)
  result = p.run()
  result.wait_until_finish()
  import pprint
  #for counter in result.monitoring_metrics().query(
  #    filter=MetricsFilter().with_step('WriteToBigQuery'))['counters']:
  for counter in result.metrics().query()['counters']:
    print('Counter: ' + repr(counter))
    print('  = ' + str(counter.result))
  print(result)


if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  main()
