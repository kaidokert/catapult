/* Copyright 2019 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

// This class merges the data that was collected by ReportFetcher into a form
// that can be displayed by ReportTable after being transformed by
// ReportSection.
export class ReportMerger {
  constructor(timeseriesesByLine, revisions) {
    this.timeseriesesByLine_ = timeseriesesByLine;
    this.revisions_ = revisions;
  }

  get suiteBotRevisions_() {
    if (this.suiteBotRevisions__) return this.suiteBotRevisions__;

    this.suiteBotRevisions__ = new Map();
    for (const {lineDescriptor, timeseriesesByRange} of
      this.timeseriesesByLine_) {
      for (const {range, timeserieses} of timeseriesesByRange) {
        for (const {fetchDescriptor, timeseries} of timeserieses) {
          if (!timeseries.length) continue;
          const key = [
            fetchDescriptor.suite, fetchDescriptor.bot, range,
          ].join('/');
          const lastRev = timeseries[timeseries.length - 1].revision;
          const maxRev = Math.max(this.suiteBotRevisions__.get(key) || 0, lastRev);
          this.suiteBotRevisions__.set(key, maxRev);
        }
      }
    }
    return this.suiteBotRevisions__;
  }

  findDatum_(fetchDescriptor, range, timeseries) {
    const key = [
      fetchDescriptor.suite, fetchDescriptor.bot, range,
    ].join('/');
    const revision = this.suiteBotRevisions_.get(key);
    for (const datum of timeseries) {
      if (datum.revision === revision) return datum;
    }
  }

  get mergedRows() {
    const suiteBotRevisions = this.suiteBotRevisions;
    const rows = [];
    console.log(this.timeseriesesByLine_);
    for (const {lineDescriptor, timeseriesesByRange} of
      this.timeseriesesByLine_) {
      const row = {
        ...lineDescriptor,
        data: {},
        unit: timeseriesesByRange[0].timeserieses[0].timeseries[0].unit,
      };
      rows.push(row);

      for (const {range, timeserieses} of timeseriesesByRange) {
        let statistics;
        const revisions = new Set();
        for (const {fetchDescriptor, timeseries} of timeserieses) {
          const datum = this.findDatum_(fetchDescriptor, range, timeseries);
          if (!datum) continue;
          if (datum.unit !== row.unit) {
            console.log('Warning: unit mismatch. Discarding datum',
              datum, row.unit);
            continue;
          }

          revisions.add(datum.revision);
          const std = datum.std || 0;
          const datumStats = tr.b.math.RunningStatistics.fromDict([
            datum.count || 1,
            datum.max || datum.avg,
            undefined,
            datum.avg,
            datum.min || datum.avg,
            datum.sum || (datum.avg * (datum.count || 1)),
            std * std,
          ]);
          statistics = statistics ? statistics.merge(datumStats) : datumStats;
        }
        row.data[range] = {statistics, revisions};
      }
    }
    return rows;
  }
}
