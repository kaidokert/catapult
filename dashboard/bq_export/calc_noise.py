# Copyright (c) 2021 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Calculate sample noise from BigQuery rows export, output to BigQuery.

Example command line to start a Dataflow job::

  $ SVC_ACCT=bigquery-exporter@chromeperf.iam.gserviceaccount.com
  $ python bq_export/calc_noise.py \
        --service_account_email=$SVC_ACCT \
        --runner=DataflowRunner \
        --region=us-central1 \
        --temp_location=gs://chromeperf-dataflow-temp/ \
        --setup_file=bq_export/setup.py \
        --autoscaling_algorithm=NONE \
        --num_workers=20 \
        --no_use_public_ips \
        --subnetwork=regions/us-central1/subnetworks/dashboard-batch \
        --project=chromeperf \
        --job_name=calc-noise-test-28d \
        --window_in_days=28
"""

import logging

from bq_export import bq_noise

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  bq_noise.main()
