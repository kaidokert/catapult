#!/bin/bash -x -e
# Copyright 2021 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

LOOKBACK=100
DESC=''

find_first_version_before_x_days(){
  local LOOKBACK_EXP=$(date -I --date="-${LOOKBACK} day")
  gcloud app versions list \
    --project=chromeperf \
    --sort-by=${DESC}LAST_DEPLOYED \
    --format="table[no-heading](VERSION.ID, LAST_DEPLOYED)" \
    --filter="SERVICE=${SERVICE} AND
              LAST_DEPLOYED.date()<${LOOKBACK_EXP}" \
  | tail -n 1 \
  | cut -d " " -f1 \
  | xargs --no-run-if-empty echo
}

for SERVICE in "$@"; do
  LOOKBACK=14
  prod_version=$(find_first_version_before_x_days)
  echo P1: $prod_version
  if [ -z "$prod_version"]
  then
    LOOKBACK=7
    DESC='~'
    prod_version=$(find_first_version_before_x_days)
    echo P1-2: $prod_version
  fi

  LOOKBACK=7
  DESC=''
  canary_version=$(find_first_version_before_x_days)
  echo C1: $canary_version
  if [ -z "$canary_version"]
  then
    LOOKBACK=''
    DESC='~'
    canary_version=$(find_first_version_before_x_days)
    echo C1-2: $canary_version
  fi

  LOOKBACK=''
  DESC=''
  latest_version=$(find_first_version_before_x_days)
  echo DEV: $latest_version
done