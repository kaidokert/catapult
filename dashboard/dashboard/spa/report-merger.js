/* Copyright 2019 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

export class ReportMerger {
  constructor(timeseriesesByLine, revisions) {
    this.timeseriesesByLine_ = timeseriesesByLine;
    this.revisions_ = revisions;
  }

  get mergedRows() {
    // Map from 'suite/bot/revision' to max revision.
    const suiteBotRevisions = new Map();

    const rows = [];
    for (const {lineDescriptor, timeseriesesByRange} of
      this.timeseriesesByLine_) {
      const row = {
        ...lineDescriptor,
        data: {},
        units: timeseriesesByRange[0].timeserieses[0].units,
      };
      rows.push(row);

      for (const {range, timeserieses} of timeseriesesByRange) {
        let count = 0;
        let mean = 0;
        let max = 0;
        let min = 0;
        let sum = 0;
        let variance = 0;
        for (const timeseries of timeserieses) {
          // TODO suiteBotRevisions
          // TODO merge statistics
        }
        row.data[range] = {statistics: [count, max, undefined, mean, min, sum, variance]};
      }
    }
    return rows;
  }
}
