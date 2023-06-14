#!/bin/bash -x -e
# Copyright 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# Usage: days service_name1 service_name2 ...
# Args:
#   days: number of days from today to be deleted
#   service_name: the builds for the service to be deleted
#
# This script is to clean up the last x days of builds that don't have
# any traffic.
#

days="$1"; shift
for SERVICE in "$@"; do
  gcloud app versions list \
    --format="table[no-heading](VERSION.ID)" \
    --filter="SERVICE=${SERVICE} AND
              TRAFFIC_SPLIT=0 AND
              LAST_DEPLOYED.date()<`date -I -v-${days}d`" \
  | xargs --no-run-if-empty gcloud app versions delete -s ${SERVICE}
done

