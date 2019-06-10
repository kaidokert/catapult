/* Copyright 2019 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

// `timeserieses` is generated by ReportFetcher.
// `mergedReport` is handled by ReportSection.reducers.receiveReports.
export class ReportMerger {
  constructor(timeseriesesByLine, revisions) {
    this.timeseriesesByLine_ = timeseriesesByLine;
    this.revisions_ = revisions;
  }

  get mergedReport() {
    const rows = [];
    for (const {lineDescriptor, timeseriesesByRange} of
      this.timeseriesesByLine_) {
      const row = {};
      for (const {range, timeserieses} of timeseriesesByRange) {
      }
      rows.push(row);
    }
    return rows;
  }
}
