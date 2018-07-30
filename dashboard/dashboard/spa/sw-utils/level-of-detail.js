/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

export const LEVEL_OF_DETAIL = {
  // Minimaps only need the (x, y) coordinates to draw the line.
  // FastHistograms contain only r_commit_pos and the needed statistic.
  // Fetches /api/timeseries2/testpath&columns=r_commit_pos,value
  XY: 'xy',

  // chart-pair.chartLayout can draw its lines using XY FastHistograms
  // while asynchronously fetching annotations (e.g.  alerts)
  // for a given revision range for tooltips and icons.
  // If an extant request overlaps a new request, then the new request can
  // fetch the difference and await the extant request.
  // Fetches /api/timeseries2/testpath&min_rev&max_rev&columns=revision,alert
  ANNOTATIONS: 'annotations',

  // pivot-table in chart-section and pivot-section need the full real
  // Histogram with all its statistics and diagnostics and samples.
  // chart-section will also request the full Histogram for the last point in
  // each timeseries in order to get its RelatedNameMaps.
  // Real Histograms contain full RunningStatistics, all diagnostics, all
  // samples. Request single Histograms at a time, even if the user brushes a
  // large range.
  // Fetches /api/histogram/testpath?rev
  HISTOGRAM: 'histogram',
};

export function getColumnsByLevelOfDetail(level, statistic) {
  switch (level) {
    case LEVEL_OF_DETAIL.XY:
      // TODO(Sam): Remove r_commit_pos everywhere
      return ['revision', 'timestamp', statistic];
    case LEVEL_OF_DETAIL.ANNOTATIONS:
      return ['revision', 'alert', 'diagnostics', 'revisions'];
    default:
      throw new Error(`${level} is not a valid Level Of Detail`);
  }
}

export default {
  LEVEL_OF_DETAIL,
  getColumnsByLevelOfDetail,
};
