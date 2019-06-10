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
        const statistics = new tr.b.math.RunningStatistics();
        let revision;
        for (const timeseries of timeserieses) {
          revision = timeseries[0][timeseries[0].length - 1].revision;
          statistics.merge(tr.b.math.RunningStatistics.fromDict([
          ]));
          // TODO suiteBotRevisions
        }
        row.data[range] = {statistics, revision};
      }
    }
    return rows;
  }
}
