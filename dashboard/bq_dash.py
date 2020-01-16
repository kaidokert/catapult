from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import datetime
import logging
import sys
import time

import apache_beam as beam
from apache_beam.io.gcp.bigquery import BigQueryWriteFn
from apache_beam.io.gcp.datastore.v1new.datastoreio import ReadFromDatastore
from apache_beam.io.gcp.datastore.v1new.datastoreio import types as ds_types
from apache_beam.options.pipeline_options import GoogleCloudOptions
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.metrics import Metrics, MetricsFilter
from apache_beam.transforms.core import FlatMap, Map


## Copy of dashboard.common.utils.TestPath for google.cloud.datastore.key.Key
## rather than ndb.Key.
def TestPath(key):
  #print('key: ' + repr(key))
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


def main():
  project = 'chromeperf'
  options = PipelineOptions()
  options.view_as(GoogleCloudOptions).project = project

  p = beam.Pipeline(options=options)
  rows_read = Metrics.counter('main', 'rows_read')
  failed_anomaly_transforms = Metrics.counter('main', 'failed_anomaly_transforms')
  failed_bq_rows = Metrics.counter('main', 'failed_bq_rows')

  # Query for Anomalies with timestamp >= 180 days ago.
  query = ds_types.Query(
      project=project,
      kind='Anomaly',
      filters=[('timestamp', '>=', DaysAgoTimestamp(180))],
  )

  # Transform entities to rows (expressed as simple dicts)
  entities = p | 'ReadFromDatastore' >> ReadFromDatastore(query)
  def AnomalyEntityToRowDict(entity):
    rows_read.inc()
    entity = entity.to_client_entity()
    try:
      d = {
          'id': entity.key.id,
          # TODO: sheriff
          # TODO: subscriptions
          'subscription_names': entity.get('subscription_names', []),
          'test': TestPath(entity['test']),
          'start_revision': entity['start_revision'],
          'end_revision': entity['end_revision'],
          'display_start': entity.get('display_start'),
          'display_end': entity.get('display_end'),
          # TODO: ownership
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
          't_statistic': entity.get('t_statistic'),
          'degrees_of_freedom': entity.get('degrees_of_freedom'),
          'p_value': entity.get('p_value'),
          'is_improvement': entity.get('is_improvement', False),
          'recovered': entity.get('recovered', False),
          # TODO: ref_test
          'units': entity.get('units'),
          # TODO: recipe_bisects
          'pinpoint_bisects': entity.get('pinpoint_bisects', []),
      }
      return [d]
    except KeyError:
      failed_anomaly_transforms.inc()
      return []
  row_dicts = (
      entities
      | 'ConvertEntityToRow(Anomaly)' >> FlatMap(AnomalyEntityToRowDict))

  # BQ
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

  bq = row_dicts | beam.io.WriteToBigQuery(
      '{}:chromeperf_dashboard_data.anomalies_test'.format(project),
      schema=bq_anomaly_schema,
      #validate=True,
      method=beam.io.WriteToBigQuery.Method.STREAMING_INSERTS,
      write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE,
      create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED)

  def CountFailed(element):
    failed_bq_rows.inc()
    #print(repr(element))
  failed_rows = bq[BigQueryWriteFn.FAILED_ROWS]
  failed_rows | beam.Map(CountFailed)
  #failed_rows | beam.ToString.Iterables() | beam.Map(print)

  print(p)
  result = p.run()
  result.wait_until_finish()
  import pprint
  #for counter in result.monitoring_metrics().query(filter=MetricsFilter().with_step('WriteToBigQuery'))['counters']:
  for counter in result.metrics().query()['counters']:
    print('Counter: ' + repr(counter))
    print('  = ' + str(counter.result))
  print(result)


if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  main()
