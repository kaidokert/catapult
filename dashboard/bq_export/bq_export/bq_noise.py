"""TODO(abennetts): DO NOT SUBMIT without one-line documentation for bq_noise.

TODO(abennetts): DO NOT SUBMIT without a detailed description of bq_noise.
"""

import datetime
import logging
from typing import Dict, Any, TypeVar, List

import apache_beam as beam
from apache_beam.options.pipeline_options import (GoogleCloudOptions,
                                                  PipelineOptions)
from apache_beam.options.value_provider import (NestedValueProvider,
                                                ValueProvider)
from apache_beam.typehints import (with_input_types, with_output_types)
from bq_export.utils import WriteToPartitionedBigQuery, FloatHack
import scipy.stats



@beam.ptransform_fn
@with_input_types(Dict[str, Any])
def SQLDictToRow(pcoll):
  return pcoll | beam.Map(lambda d: beam.Row(**d))


T = TypeVar('T')

@with_input_types(List[T])
@with_output_types(List[T])
class ConcatListCombineFn(beam.CombineFn):
  """CombineFn for concatentating lists."""
  def create_accumulator(self):
    return []

  def add_input(self, accumulator, element):
    accumulator.extend(element)
    return accumulator

  def merge_accumulators(self, accumulators):
    merged = []
    for acc in accumulators:
      merged.extend(acc)
      del acc[:]
    return merged

  def extract_output(self, accumulator):
    return accumulator


@beam.ptransform_fn
def SampleValuesBy(pcoll, key_columns):
  """Group sample_values by key_columns.

  E.g. with this pcollection:
    col1=A col2=B col3=C sample_values=[1]
    col1=A col2=B col3=Z sample_values=[2, 3]

  p | SampleValuesBy(['col1', 'col2']) emits:
    (col1=A, col2=B), all_sample_values=[1, 2, 3]
  """
  return (
      pcoll
      #| beam.Select(*(key_columns + ['sample_values']))
      | beam.GroupBy(*key_columns)
          .force_tuple_keys()
          .aggregate_field('sample_values',
                           ConcatListCombineFn(),
                           'all_sample_values')
  )


@beam.ptransform_fn
def SampleValuesNoiseBy(pcoll, *key_columns):
  """Emits 2-tuple of ((key_columns...), noise_stats_row)."""
  return (
      pcoll
      | SQLDictToRow()
      | SampleValuesBy(key_columns)
      | SummariseNoise(key_columns)
  )


# TODO: .with_input_types etc.
@beam.ptransform_fn
def SummariseNoise(pcoll, key_columns):
  # def Log(elem):
  #   logging.info(repr(elem))
  #   return elem
  def KeyCols(elem):
    return beam.Row(**{k: getattr(elem, k) for k in key_columns})
  def NoiseStats(arr):
    return beam.Row(
        num_samples=len(arr),
        kurtosis=scipy.stats.kurtosis(arr),
        skewness=scipy.stats.skew(arr),
        iqr=scipy.stats.iqr(arr),
        variation=scipy.stats.variation(arr))

  return (
      pcoll
      #| 'Log(INFO)' >> beam.Map(Log)
      | 'SciPy.stats.*' >> beam.Map(
          lambda elem: (KeyCols(elem), NoiseStats(elem.all_sample_values)))
  )


@beam.ptransform_fn
def FlattenForSQL(pcoll, fixed_cols_provider):
  """Flatten KV elem, and add fixed columns.

  E.g. with this input:
    Fixed cols: fix1='f1', fix2='f2'
    Element #1: ((key1='A', key2='B'), (x=1.1, y=1.2))
    Element #2: ((key1='A', key2='C'), (x=2.1, y=2.2))

  Emits 2 elements:
    fix1='f1', fix2='f2', key1='A', key2='B', x=1.1, y=1.2
    fix1='f1', fix2='f2', key1='A', key2='C', x=2.1, y=2.2

  Inputs are 2-tuple of (beam.Row, beam.Row), and fixed_cols_provider is also a
  a beam.Row.

  Output is a single dict.
  """

  def FlattenElement(elem):
    #logging.info(repr(elem))
    #return beam.Row(
    d = dict(
        **fixed_cols_provider.get().as_dict(),
        **elem[0].as_dict(),
        **elem[1].as_dict())
    # TODO: try temp_file_format=AVRO on the BQ writer instead?
    d['variation'] = FloatHack(d['variation'])
    return d
  return pcoll | beam.Map(FlattenElement)


class BqNoiseOptions(PipelineOptions):

  @classmethod
  def _add_argparse_args(cls, parser):  # pylint: disable=invalid-name
    parser.add_value_provider_argument(
        '--end_date',
        help=('Last day of data to export in YYYYMMDD format, or special value '
              '"yesterday".  Default is yesterday.  Timezone is always UTC.'),
        default="yesterday")
    parser.add_value_provider_argument(
        '--window_in_days', help='Number of days data summarize.', type=int, default=1)
    #parser.add_argument(
    #    '--table_suffix',
    #    help='Suffix to add to table name (for dev purposes, e.g. "_test").',
    #    default='')
    parser.add_value_provider_argument(
        '--dataset',
        help='BigQuery dataset name.  Overrideable for testing/dev purposes.',
        default='chromeperf_dashboard_data')

  def GetFixedColumnsProvider(self):
    def DateTransform(yyyymmdd):
      if yyyymmdd == 'yesterday':
        d = (datetime.datetime.utcnow() - datetime.timedelta(days=1)).date()
      else:
        d = datetime.date(
            int(yyyymmdd[:4]),
            int(yyyymmdd[4:6]),
            int(yyyymmdd[6:8]))
      return beam.Row(date=d)
    return NestedValueProvider(self.end_date, DateTransform)

  def GetSQLQueryProvider(self):
    query_template = '''
        SELECT master as bot_group, bot, measurement, revision, sample_values
        FROM `chromeperf.chromeperf_dashboard_data.rows`
        WHERE
          (DATE(timestamp) BETWEEN DATE_SUB(DATE('{date}'), INTERVAL {days} DAY)
                           AND DATE('{date}'))
          AND measurement LIKE 'system_health.common%'
          AND ARRAY_LENGTH(sample_values) > 0
        ORDER BY master, bot, measurement, revision;'''

    class SQLProvider(ValueProvider):
      def __init__(self, end_date, window_in_days):
        self.end_date = end_date
        self.window_in_days = window_in_days
      def is_accessible(self):
        return self.end_date.is_accessible() and self.window_in_days.is_accessible()
      def get(self):
        end_date = self.end_date.get()
        if end_date == 'yesterday':
          end_date = (datetime.datetime.utcnow() -
                      datetime.timedelta(days=1)).strftime('%Y%m%d')
        yyyy_mm_dd = '{}-{}-{}'.format(end_date[:4], end_date[4:6], end_date[6:8])
        return query_template.format(date=yyyy_mm_dd,
                                     days=self.window_in_days.get() - 1)

    return SQLProvider(self.end_date, self.window_in_days)



def main():
  options = PipelineOptions()
  p = beam.Pipeline(options=options)
  options.view_as(GoogleCloudOptions).project = 'chromeperf'
  noise_options = options.view_as(BqNoiseOptions)
  query_provider = noise_options.GetSQLQueryProvider()

  ### 1. Query 'rows' tbl for sample_values
  rows = p | 'QueryTable' >> beam.io.ReadFromBigQuery(query=query_provider,
                                                      use_standard_sql=True,
                                                      validate=True,
                                                      flatten_results=False)

  ### 2. group data by various breakdowns
  ### 3. calculate skewness, kurtosis, etc.
  noise_by_m = (
      rows | 'CalcNoise(measurement)' >> SampleValuesNoiseBy('measurement'))
  noise_by_bg_b_m = (
      rows | 'CalcNoise(bot_group,bot,measurement)' >> SampleValuesNoiseBy(
          'bot_group', 'bot', 'measurement'))
  ### TODO:
  # noise_by_story = (
  #     rows | 'CalcNoise(story)' >> SampleValuesNoiseBy(...))

  ### 4. emit results to sink (BQ table?)
  """
  CREATE TABLE `chromeperf.chromeperf_dashboard_data.noise_by_measurement_7d`
  (`date` DATE NOT NULL,

   measurement STRING NOT NULL,

   num_samples INT64 NOT NULL,
   kurtosis FLOAT64,
   skewness FLOAT64,
   iqr FLOAT64,
   variation FLOAT64,
   )
  PARTITION BY `date`
  CLUSTER BY measurement;

  CREATE TABLE `chromeperf.chromeperf_dashboard_data.noise_by_botgroup_7d`
  (`date` DATE NOT NULL,

   bot_group STRING NOT NULL,
   bot STRING NOT NULL,
   measurement STRING NOT NULL,

   num_samples INT64 NOT NULL,
   kurtosis FLOAT64,
   skewness FLOAT64,
   iqr FLOAT64,
   variation FLOAT64,
   )
  PARTITION BY `date`
  CLUSTER BY bot_group, bot, measurement;
  """  # pylint: disable=pointless-string-statement
  bq_noise_by_measurement_schema = {
      'fields': [
          {'name': 'date', 'type': 'DATE', 'mode': 'REQUIRED'},

          {'name': 'measurement', 'type': 'STRING', 'mode': 'REQUIRED'},

          {'name': 'num_samples', 'type': 'INT64', 'mode': 'REQUIRED'},
          {'name': 'kurtosis', 'type': 'FLOAT', 'mode': 'NULLABLE'},
          {'name': 'skewness', 'type': 'FLOAT', 'mode': 'NULLABLE'},
          {'name': 'iqr', 'type': 'FLOAT', 'mode': 'NULLABLE'},
          {'name': 'variation', 'type': 'FLOAT', 'mode': 'NULLABLE'},
      ],
  }

  bq_noise_by_bg_b_m_schema = {
      'fields': [
          {'name': 'date', 'type': 'DATE', 'mode': 'REQUIRED'},

          {'name': 'bot_group', 'type': 'STRING', 'mode': 'REQUIRED'},
          {'name': 'bot', 'type': 'STRING', 'mode': 'REQUIRED'},
          {'name': 'measurement', 'type': 'STRING', 'mode': 'REQUIRED'},

          {'name': 'num_samples', 'type': 'INT64', 'mode': 'REQUIRED'},
          {'name': 'kurtosis', 'type': 'FLOAT', 'mode': 'NULLABLE'},
          {'name': 'skewness', 'type': 'FLOAT', 'mode': 'NULLABLE'},
          {'name': 'iqr', 'type': 'FLOAT', 'mode': 'NULLABLE'},
          {'name': 'variation', 'type': 'FLOAT', 'mode': 'NULLABLE'},
      ],
  }

  # Annotate elems with date, days (and flatten k,v tuples)
  def GetTableNameFn(table_name):
    def TableNameFn(unused_element):
      # The tables are partitioned by end date (only), so we have to manually
      # partition by window size so that pipelines for e.g. 7d vs. 28d
      # windows don't overwrite each other.  Thus we include days in the table
      # name (rather than as an extra column).
      return '{project}:{dataset}.{table_name}_{days}d'.format(
          project=options.view_as(GoogleCloudOptions).project,
          dataset=noise_options.dataset.get(),
          table_name=table_name,
          days=noise_options.window_in_days.get())
    return TableNameFn

  _ = (noise_by_m
       | FlattenForSQL(noise_options.GetFixedColumnsProvider())
       | 'WriteToPartitionedBigQuery(noise_by_measurement)' >> WriteToPartitionedBigQuery(
           GetTableNameFn('noise_by_measurement'),
           schema=bq_noise_by_measurement_schema,
           element_to_yyyymmdd_fn=lambda elem: elem['date'].strftime('%Y%m%d'),
           additional_bq_parameters={
               'clustering': {'fields': ['measurement']}}))
  _ = (noise_by_bg_b_m
       | 'FlattenForSQL(2)' >> FlattenForSQL(noise_options.GetFixedColumnsProvider())
       | 'WriteToPartitionedBigQuery(noise_by_botgroup)' >> WriteToPartitionedBigQuery(
           GetTableNameFn('noise_by_botgroup'),
           schema=bq_noise_by_bg_b_m_schema,
           element_to_yyyymmdd_fn=lambda elem: elem['date'].strftime('%Y%m%d'),
           additional_bq_parameters={
               'clustering': {'fields': ['bot_group', 'bot', 'measurement']}}))

  result = p.run()
  result.wait_until_finish()
