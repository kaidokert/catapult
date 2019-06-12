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
        for (const datum of timeserieses) {
          const key = [
            datum.fetchDescriptor.suite, datum.fetchDescriptor.bot, range,
          ].join('/');
          if (datum.revision > (this.suiteBotRevisions__.get(key) || 0)) {
            this.suiteBotRevisions__.set(key, datum.revision);
          }
        }
      }
    }
    return this.suiteBotRevisions__;
  }

  findUnit_(timeseriesesByRange) {
    if (!timeseriesesByRange) return undefined;
    for (const {timeserieses} of timeseriesesByRange) {
      if (!timeserieses) continue;
      for (const datum of timeserieses) {
        if (datum.unit) return datum.unit;
      }
    }
    return undefined;
  }

  haveAllRevisions_(timeseriesesByRange, fetchDescriptor) {
    for (const {range, timeserieses} of timeseriesesByRange) {
      let found = false;
      for (const datum of timeserieses) {
        if (datum.fetchDescriptor.fetchIndex === fetchDescriptor.fetchIndex) {
          found = true;
          break;
        }
      }
      console.log('!haveAllRevisions_', timeseriesesByRange, fetchDescriptor);
      if (!found) return false;
    }
    return true;
  }

  get mergedRows() {
    const suiteBotRevisions = this.suiteBotRevisions;
    const rows = [];
    console.log(this.timeseriesesByLine_);
    for (const {lineDescriptor, timeseriesesByRange} of
      this.timeseriesesByLine_) {
      const unit = this.findUnit_(timeseriesesByRange);
      if (!unit) {
        continue;
      }

      const row = {...lineDescriptor, data: {}, unit};
      rows.push(row);

      for (const {range, timeserieses} of timeseriesesByRange) {
        let statistics;
        const revisions = new Set();
        for (const datum of timeserieses) {
          if (datum.unit !== unit) {
            continue;
          }

          const key = [
            datum.fetchDescriptor.suite, datum.fetchDescriptor.bot, range,
          ].join('/');
          if ((datum.revision !== this.suiteBotRevisions_.get(key)) ||
              !this.haveAllRevisions_(
                  timeseriesesByRange, datum.fetchDescriptor)) {
            continue;
          }

          revisions.add(datum.revision);
          statistics = statistics ? statistics.merge(datum.statistics) :
            datum.statistics;
        }
        row.data[range] = {statistics, revisions};
      }
    }
    return rows;
  }
}
