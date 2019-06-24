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

  // Map from 'suite/bot/range' to the max revision available out of all
  // fetchDescriptors.
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

  haveAllRevisions_(timeseriesesByRange, fetchDescriptor) {
    if (timeseriesesByRange.length < this.revisions_.length) return false;

    for (const {range, timeserieses} of timeseriesesByRange) {
      const key = [
        fetchDescriptor.suite, fetchDescriptor.bot, range,
      ].join('/');
      const revision = this.suiteBotRevisions_.get(key);

      let found = false;
      for (const datum of timeserieses) {
        if ((datum.fetchDescriptor.fetchIndex === fetchDescriptor.fetchIndex) &&
            (datum.revision === revision)) {
          found = true;
          break;
        }
      }
      if (!found) {
        return false;
      }
    }
    return true;
  }

  // `target` is a lineDescriptor. `source` is a fetchDescriptor.
  mergeDescriptor_(target, source) {
    if (!target.measurement) {
      target.measurement = source.measurement;
    } else if (target.measurement !== source.measurement) {
      throw new Error('Report template rows cannot have multiple measurements');
    }

    if (!target.suites) target.suites = new Set();
    target.suites.add(source.suite);

    if (!target.bots) target.bots = new Set();
    target.bots.add(source.bot);

    if (!target.cases) target.cases = new Set();
    if (source.case) target.cases.add(source.case);
  }

  get mergedRows() {
    const rows = [];
    for (const {lineDescriptor, timeseriesesByRange} of
      this.timeseriesesByLine_) {
      const row = {...lineDescriptor, data: {}, descriptor: {}};
      let rowOk = true;

      for (const {range, timeserieses} of timeseriesesByRange) {
        let statistics;
        const revisions = new Set();
        for (const datum of timeserieses) {
          if (!this.haveAllRevisions_(
              timeseriesesByRange, datum.fetchDescriptor)) {
            continue;
          }

          // Report template rows should have exactly one measurement.
          // All suites, bots, and cases should record the same unit for the
          // same measurement. Scalars with different units cannot be merged.
          if (!row.unit) {
            row.unit = datum.unit;
          } else if (datum.unit !== row.unit) {
            continue;
          }

          revisions.add(datum.revision);
          statistics = statistics ? statistics.merge(datum.statistics) :
            datum.statistics;
          this.mergeDescriptor_(row.descriptor, datum.fetchDescriptor);
        }

        if (statistics) {
          row.data[range] = {statistics, revisions};
        } else {
          rowOk = false;
          break;
        }
      }

      if (!rowOk) continue;
      row.descriptor.cases = [...row.descriptor.cases];
      rows.push(row);
    }
    return rows;
  }
}
