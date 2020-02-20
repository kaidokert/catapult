# Chromeperf Datastore → BigQuery export pipeline.

Apache Beam pipelines for exporting Anomaly and Row entities from chromeperf's
Datastore into BigQuery tables.

## Set up a development environment

Follow the instructions at
https://cloud.google.com/dataflow/docs/quickstarts/quickstart-python#set-up-your-environment

## Deployment

### Upload job templates

In the virtualenv with the Beam SDK installed:

```
$ cd dashboard/
```

```
$ PYTHONPATH=$PYTHONPATH:"$(pwd)/bq_export" python bq_export/export_rows.py \
  --service_account_email=bigquery-exporter@chromeperf.iam.gserviceaccount.com \
  --runner=DataflowRunner
  --region=us-central1 \
  --experiments=use_beam_bq_sink  \
  --setup_file=bq_export/setup.py \
  --staging_location=gs://chromeperf-dataflow/staging \
  --template_location=gs://chromeperf-dataflow/templates/export_rows
```

```
$ PYTHONPATH=$PYTHONPATH:"$(pwd)/bq_export" python \
  bq_export/export_anomalies.py \
  --service_account_email=bigquery-exporter@chromeperf.iam.gserviceaccount.com \
  --runner=DataflowRunner
  --region=us-central1 \
  --experiments=use_beam_bq_sink  \
  --setup_file=bq_export/setup.py \
  --staging_location=gs://chromeperf-dataflow/staging \
  --template_location=gs://chromeperf-dataflow/templates/export_anomalies
```

## Executing jobs

### Manually trigger jobs from templates

You can execute one-off jobs with the `gcloud` tool.  For example:

```
$ gcloud dataflow jobs run export-anomalies-example-job \
  --service-account-email=bigquery-exporter@chromeperf.iam.gserviceaccount.com \
  --gcs-location=gs://chromeperf-dataflow/templates/export_anomalies \
  --disable-public-ips --max-workers=10 --region=us-central1
  --staging-location=gs://chromeperf-dataflow-temp/export_anomalies
  --parameters=experiments=shuffle_mode=sink,subnetwork=regions/us-central1/subnetworks/dashboard-batch
```

To execute a manual backfill, specify the `--end_date` and/or `num_days`
parameters:

```
$ gcloud dataflow jobs run export-anomalies-backfill-example \
  --service-account-email=bigquery-exporter@chromeperf.iam.gserviceaccount.com \
  --gcs-location=gs://chromeperf-dataflow/templates/export_anomalies \
  --disable-public-ips --max-workers=10 --region=us-central1
  --staging-location=gs://chromeperf-dataflow-temp/export_anomalies
  --parameters=experiments=shuffle_mode=sink,subnetwork=regions/us-central1/subnetworks/dashboard-batch,end_date=20191231,num_days=31
```

### Execute a job without a template

In the virtualenv with the Beam SDK you can run a job without creating a
template by specifying all the job execution parameters and omitting the
template parameters (i.e. omit `--staging_location` and `--template_location`).

For example:

```
PYTHONPATH=$PYTHONPATH:"$(pwd)/bq_export" python bq_export/export_rows.py
--service_account_email=bigquery-exporter@chromeperf.iam.gserviceaccount.com
--runner=DataflowRunner --region=us-central1
--temp_location=gs://chromeperf-dataflow-temp/anomalies_test
--experiments=use_beam_bq_sink --num_workers=70
--experiments=shuffle_mode=service  --setup_file=bq_export/setup.py
--no_use_public_ips --subnetwork=regions/us-central1/subnetworks/dashboard-batch
--autoscaling_algorithm=NONE
```
