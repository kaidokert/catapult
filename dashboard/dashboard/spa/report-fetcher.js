/* Copyright 2019 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import ChartTimeseries from './chart-timeseries.js';
import {BatchIterator, enumerate} from './utils.js';
import {LEVEL_OF_DETAIL, TimeseriesRequest} from './timeseries-request.js';
import {TimeseriesesByLine} from './details-fetcher.js';

export const LATEST_REVISION = 'latest';

// ReportFetcher takes an array `revisions` containing things that suggest
// revisions. Those things could be LATEST_REVISION or numbers, or arrays of
// numbers from different revision schedules.

// Find revision ranges per suitebot, but collate data per row/fetch.
// There's a many-to-many relationship between suitebot and row.
// 1. Fetch the full history of revisions for the first fetchDescriptor.
//    (Beware it may not cover all this.revisions_ because test cases may be
//    enabled/disabled.)
// 2. Narrow the revision ranges as much as possible. They may need to stay
//    somewhat open until more data is received.
// 3. Add fetches to this.batches_ for all the fetchDescriptors, a few at a
//    time.
// All these fetchDescriptors share a suite/bot, so they all have the same
// revision schedule (e.g. chromium commit pos, v8 commit pos, ms timestamp, s
// timestamp), but they might not all have the same revision range because
// test cases can be enabled/disabled at different times.

export class ReportFetcher {
  constructor(template, revisions) {
    this.createFetchDescriptors_(template);
    this.revisions_ = revisions;

    // This collates results.
    this.timeseriesesByLine_ = new TimeseriesesByLine(
        this.fetchDescriptorsByRow_, revisions);

    // This batches the stream of results to reduce unnecessary rendering.
    // This does not batch the results themselves, they need to be collated by
    // this.timeseriesesByLine_.
    this.batches_ = new BatchIterator();
  }

  createFetchDescriptors_(template) {
    this.fetchDescriptorsByRow_ = [];

    // Map from 'suite/bot' to RangeFinder
    this.rangeFindersBySuiteBot_ = new Map();

    for (const [rowIndex, lineDescriptor] of enumerate(template.rows)) {
      const lineDescriptor = {
        suites: lineDescriptor.testSuites,
        bots: lineDescriptor.bots,
        measurement: lineDescriptor.measurement,
        cases: lineDescriptor.testCases,
        buildType: 'test',
        statistic: 'avg',
      };
      const fetchDescriptors = ChartTimeseries.createFetchDescriptors(
          lineDescriptor, LEVEL_OF_DETAIL.XY);
      this.fetchDescriptorsByRow_.push({lineDescriptor, fetchDescriptors});
      for (const [fetchIndex, fetchDescriptor] of enumerate(fetchDescriptors)) {
        fetchDescriptor.rowIndex = rowIndex;
        fetchDescriptor.fetchIndex = fetchIndex;

        const suiteBot = fetchDescriptor.suite + '/' + fetchDescriptor.bot;
        if (!this.rangeFindersBySuiteBot_.has(suiteBot)) {
          this.rangeFindersBySuiteBot_.set(
              suiteBot, new RangeFinder(fetchDescriptor));
        }
      }
    }
  }

  [Symbol.asyncIterator]() {
    return (async function* () {
      for (const {fetchDescriptors} of this.fetchDescriptorsByRow_) {
        for (const fetchDescriptor of fetchDescriptors) {
          for (const [revIndex, revision] of enumerate(this.revisions_)) {
            this.batches_.add(this.fetchCell_(
                fetchDescriptor, revIndex, revision));
          }
        }
      }

      for await (const {results, errors} of this.batches_) {
        const timeseriesesByLine = this.timeseriesesByLine_.populatedResults;
        yield {errors, timeseriesesByLine};
      }
    }).call(this);
  }

  fetchCell_(fetchDescriptor, revIndex, revision) {
    return (async function* () {
      const suiteBot = fetchDescriptor.suite + '/' + fetchDescriptor.bot;
      const rangeFinder = this.rangeFindersBySuiteBot_.get(suiteBot);
      const revisionRange = await rangeFinder.findRange(revision);
      fetchDescriptor = {
        ...fetchDescriptor,
        ...revisionRange,
      };
      const request = new TimeseriesRequest(fetchDescriptor);
      for await (const timeseries of request.reader()) {
        this.timeseriesesByLine_.receive(
            fetchDescriptor.rowIndex,
            revIndex,
            fetchDescriptor.fetchIndex,
            timeseries);
        yield {/* Pump BatchIterator. */};
      }
    }).call(this);
  }
}

export const SCHEDULE_TOLERANCE = 0.9;

class RangeFinder {
  constructor(fetchDescriptor) {
    this.revisions_ = [];

    // somePromise_ resolves when the service worker returns whatever's
    // cached for this fetchDescriptor. firstPromise_ resolves when all the data
    // for this fetchDescriptor is received.
    this.somePromise_ = new Promise(resolve => {
      this.resolveSome_ = resolve;
    });
    this.firstPromise_ = this.fetchXYTimeseries_(fetchDescriptor);
  }

  receive(data) {
    for (const {revision} of data) {
      if ((this.revisions_.length === 0) ||
          (revision > this.revisions_[this.revisions_.length - 1])) {
        this.revisions_.push(revision);
        continue;
      }

      const index = tr.b.findLowIndexInSortedArray(
          this.revisions_, r => r, revision);
      // Now, this.revisions_[index] >= revision.
      if (revision === this.revisions_[index]) continue;
      this.revisions_.splice(index, 0, revision);
    }
  }

  async findRange(revision) {
    if (revision === LATEST_REVISION) {
      await this.firstPromise_;
      return {minRevision: this.revisions_[this.revisions_.length - 1]};
    }

    await this.somePromise_;

    // `revision` may be an array of revision numbers from different schedules
    // (e.g. chromium commit pos, v8 commit pos, timestamp, etc). The suite/bot
    // represented by this RangeFinder could use a different schedule than other
    // suite/bots.

    if (typeof(revision) === 'number') {
      revision = [revision];
    }

    for (const revNum of revision) {
      if (!this.isSameSchedule_(revNum)) continue;

      if (revNum > this.revisions_[this.revisions_.length - 1]) {
        return {minRevision: this.revisions_[this.revisions_.length - 1]};
      }
      if (revNum < this.revisions_[0]) {
        return {maxRevision: this.revisions_[0]};
      }

      const index = tr.b.findLowIndexInSortedArray(
          this.revisions_, r => r, revNum);
      // Now, this.revisions_[index] >= revNum
      return {
        minRevision: this.revisions_[index - 1],
        maxRevision: this.revisions_[index],
      };
    }

    // Unable to find a revNum in `revision` with the same revision schedule as
    // the constructor's `fetchDescriptor`. The caller should fetch the full
    // history for their fetchDescriptor, call receive(data), and maybe future
    // findRange() calls will have better luck.

    return {};
  }

  isSameSchedule_(revision) {
    return ((revision > (this.revisions_[0] * SCHEDULE_TOLERANCE)) &&
            (revision < (this.revisions_[this.revisions_.length - 1] *
              (1 + (1 - SCHEDULE_TOLERANCE)))));
  }

  async fetchXYTimeseries_(fetchDescriptor) {
    const request = new TimeseriesRequest(fetchDescriptor);
    for await (const data of request.reader()) {
      this.receive(data);
      this.resolveSome_();
    }
  }
}
