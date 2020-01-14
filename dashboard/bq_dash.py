from __future__ import absolute_import
from __future__ import division
#from __future__ import google_type_annotations
from __future__ import print_function

import datetime
import sys
import time

import apache_beam as beam
from apache_beam.io.gcp.datastore.v1new.datastoreio import ReadFromDatastore
from apache_beam.io.gcp.datastore.v1new.datastoreio import types as ds_types
from apache_beam.options.pipeline_options import GoogleCloudOptions
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.options.pipeline_options import SetupOptions
from apache_beam.transforms.core import Map
#from google.cloud.datastore import query as ds_query
#from google.cloud.proto.datastore.v1 import entity_pb2
#from google.cloud.proto.datastore.v1 import query_pb2
#from google.protobuf import timestamp_pb2


## Copy of dashboard.common.utils.TestPath for google.cloud.datastore.key.Key
## rather than ndb.Key.
def TestPath(key):
  if key.kind == 'Test':
    # The Test key looks like ('Master', 'name', 'Bot', 'name', 'Test' 'name'..)
    # Pull out every other entry and join with '/' to form the path.
    return '/'.join(key.flat_path[1::2])
  assert key.kind == 'TestMetadata' or key.kind == 'TestContainer'
  return key.id


def DaysAgoTimestamp(days_ago):
  """Return a timestamp_pb2.Timestamp for a day the given number of days in the past."""
  now = datetime.datetime.now()
  result_datetime = now - datetime.timedelta(days=days_ago)
  #result_secs = time.mktime(result_datetime.utctimetuple())
  #result_pb = timestamp_pb2.Timestamp(seconds=long(result_secs), nanos=0)
  return result_datetime


def main():
  project = 'chromeperf'
  options = PipelineOptions()
  options.view_as(GoogleCloudOptions).project = project

  with beam.Pipeline(options=options) as p:
    # Query for Anomalies with timestamp >= 180 days ago.
    query = ds_types.Query(
        project=project,
        kind='Anomaly',
        filters=[('timestamp', '>=', DaysAgoTimestamp(180))])

    #query = ds_query.Query(client=None, project=project, namespace='[default]', kind='Anomaly')
    #query.add_filter('timestamp', '>=', DaysAgoTimestamp(180))

    #query = query_pb2.Query()
    #query.kind.add().name = 'Anomaly'
    #query.filter.CopyFrom(query_pb2.Filter(
    #    property_filter=query_pb2.PropertyFilter(
    #        property=query_pb2.PropertyReference(name='timestamp'),
    #        op=query_pb2.PropertyFilter.GREATER_THAN_OR_EQUAL,
    #        value=entity_pb2.Value(timestamp_value=DaysAgoTimestamp(180)))))

    # Transform entities to rows (expressed as simple dicts)
    entities = p | 'Read from Datastore' >> ReadFromDatastore(query)
    def AnomalyEntityToRowDict(entity):
      entity = entity.to_client_entity()
      d = {
          'id': entity.key.id,
          'test': TestPath(entity['test']),
          'start_revision': entity['start_revision'],
          'end_revision': entity['end_revision'],
          'statistic': entity['statistic'],
          'bug_id': entity['bug_id'],
          #'pinpoint_bisects': x,  # TODO
          'internal_only': entity['internal_only'],
      }
      return d
    row_dicts = entities | Map(AnomalyEntityToRowDict)

    # BQ
    bq_anomaly_schema = {'fields': [
        {'name': 'id', 'type': 'INT64', 'mode': 'REQUIRED'},
        {'name': 'test', 'type': 'STRING', 'mode': 'REQUIRED'},
        {'name': 'start_revision', 'type': 'INT64', 'mode': 'REQUIRED'},
        {'name': 'end_revision', 'type': 'INT64', 'mode': 'REQUIRED'},
        {'name': 'statistic', 'type': 'STRING', 'mode': 'REQUIRED'},
        {'name': 'bug_id', 'type': 'INT64', 'mode': 'NULLABLE'},
        #{'name': 'pinpoint_bisects', 'type': XX, 'mode': 'NULLABLE'},  # TODO
        {'name': 'internal_only', 'type': 'BOOLEAN', 'mode': 'REQUIRED'},

    ]}

    bq = row_dicts | beam.io.WriteToBigQuery(
        '{}:test_dataset.anomalies_test'.format(project),
        schema=bq_anomaly_schema,
        write_disposition=beam.io.BigQueryDisposition.WRITE_TRUNCATE,
        create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED)


if __name__ == '__main__':
  main()
