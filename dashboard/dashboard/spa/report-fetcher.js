/* Copyright 2019 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import {BatchIterator} from '@chopsui/batch-iterator';
import {ChartTimeseries} from './chart-timeseries.js';
import {TimeseriesesByLine} from './details-fetcher.js';
import {enumerate} from './utils.js';

import {
  LEVEL_OF_DETAIL,
  TimeseriesRequest,
  createFetchDescriptors,
} from './timeseries-request.js';

export const LATEST_REVISION = 'latest';

// ReportFetcher takes
// 1. a report info {id, name, modified, template, owners, internal}
// 2. an array `revisions` containing things that suggest
// revisions. Those things could be LATEST_REVISION or numbers, or arrays of
// numbers from different revision schedules.

// ReportFetcher is an async iterator that yields
// {errors, timeseriesesByLine, ...reportInfo}.
// reportInfo is included in order to allow callers to iterate over multiple
// ReportFetchers simultaneously using BatchIterator.

export class ReportFetcher {
  constructor(info, revisions) {
    this.info_ = info;
    this.revisions_ = revisions;

    this.fetchDescriptorsByRow_ = [];

    // Map from 'suite/bot' to RangeFinder
    this.rangeFindersBySuiteBot_ = new Map();

    this.createFetchDescriptors_(info);

    // This collates results.
    this.timeseriesesByLine_ = new TimeseriesesByLine(
        this.fetchDescriptorsByRow_, revisions);

    // This batches the stream of results to reduce unnecessary rendering.
    // This does not batch the results themselves, they need to be collated by
    // this.timeseriesesByLine_.
    this.batches_ = new BatchIterator();
  }

  createFetchDescriptors_() {
    for (const [rowIndex, row] of enumerate(this.info_.template.rows)) {
      const lineDescriptor = {
        label: row.label,
        suites: row.testSuites,
        bots: row.bots,
        measurement: row.measurement,
        cases: row.testCases,
        buildType: 'test',
      };
      const fetchDescriptors = createFetchDescriptors(
          lineDescriptor, LEVEL_OF_DETAIL.XY);
      this.fetchDescriptorsByRow_.push({lineDescriptor, fetchDescriptors});
      for (const [fetchIndex, fetchDescriptor] of enumerate(fetchDescriptors)) {
        fetchDescriptor.statistics = this.info_.template.statistics;
        fetchDescriptor.rowIndex = rowIndex;
        fetchDescriptor.fetchIndex = fetchIndex;

        const suiteBot = fetchDescriptor.suite + '/' + fetchDescriptor.bot;
        if (!this.rangeFindersBySuiteBot_.has(suiteBot)) {
          this.rangeFindersBySuiteBot_.set(suiteBot, new RangeFinder());
        }
        this.rangeFindersBySuiteBot_.get(suiteBot).addSource(fetchDescriptor);
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
        yield {errors, timeseriesesByLine, ...this.info_};
      }
    }).call(this);
  }

  fetchCell_(fetchDescriptor, revIndex, revision) {
    return (async function* () {
      const suiteBot = fetchDescriptor.suite + '/' + fetchDescriptor.bot;
      const rangeFinder = this.rangeFindersBySuiteBot_.get(suiteBot);
      const revisionRange = await rangeFinder.findRange(revision);
      fetchDescriptor = {...fetchDescriptor, ...revisionRange};
      const request = new TimeseriesRequest(fetchDescriptor);
      for await (const timeseries of request.reader()) {
        const datum = this.getDatum_(timeseries, revision);
        if (!datum) continue;
        this.timeseriesesByLine_.receive(
            fetchDescriptor.rowIndex, revIndex, fetchDescriptor.fetchIndex,
            {fetchDescriptor, ...datum});
        yield {/* Pump BatchIterator. */};
      }
    }).call(this);
  }

  transformDatum_(datum) {
    const std = datum.std || 0;
    const statistics = tr.b.math.RunningStatistics.fromDict([
      datum.count || 1,
      datum.max || datum.avg,
      undefined,
      datum.avg,
      datum.min || datum.avg,
      datum.sum || (datum.avg * (datum.count || 1)),
      std * std,
    ]);
    return {statistics, revision: datum.revision, unit: datum.unit};
  }

  getDatum_(timeseries, revisions) {
    if (!timeseries || !timeseries.length) {
      return undefined;
    }

    if (revisions === LATEST_REVISION) {
      return this.transformDatum_(timeseries[timeseries.length - 1]);
    }

    if (typeof(revisions) === 'number') {
      revisions = [revisions];
    }

    for (const revision of revisions) {
      if (!isSameSchedule(revision, timeseries[0].revision,
          timeseries[timeseries.length - 1].revision)) {
        continue;
      }
      if (timeseries[0].revision > revision) return undefined;

      let index = tr.b.findLowIndexInSortedArray(
          timeseries, d => d.revision, revision);
      // Now, timeseries[index].revision >= revision.
      if (timeseries[index].revision > revision) --index;
      return this.transformDatum_(timeseries[index]);
    }

    return undefined;
  }
}

export const SCHEDULE_TOLERANCE = 0.9;

function isSameSchedule(revision, minRev, maxRev) {
  return ((revision > (minRev * SCHEDULE_TOLERANCE)) &&
          (revision < (maxRev * (1 + (1 - SCHEDULE_TOLERANCE)))));
}

export class RangeFinder {
  constructor() {
    this.fetchDescriptors_ = [];
    this.revisions_ = [];
    this.readyPromise__ = undefined;
  }

  addSource(fetchDescriptor) {
    this.fetchDescriptors_.push(fetchDescriptor);
  }

  async findRange(revisions) {
    await this.readyPromise_;

    if (revisions === LATEST_REVISION) {
      return {minRevision: this.revisions_[this.revisions_.length - 1]};
    }

    // `revisions` may be an array of revisions numbers from different schedules
    // (e.g. chromium commit pos, v8 commit pos, timestamp, etc). The suite/bot
    // represented by this RangeFinder could use a different schedule than other
    // suite/bots.

    if (typeof(revisions) === 'number') {
      revisions = [revisions];
    }

    for (const revision of revisions) {
      if (!this.isSameSchedule_(revision)) continue;

      if (revision > this.revisions_[this.revisions_.length - 1]) {
        return {minRevision: this.revisions_[this.revisions_.length - 1]};
      }
      if (revision < this.revisions_[0]) {
        return {maxRevision: this.revisions_[0]};
      }

      const index = tr.b.findLowIndexInSortedArray(
          this.revisions_, r => r, revision);
      // Now, this.revisions_[index] >= revision
      return {
        minRevision: this.revisions_[index - 1],
        maxRevision: this.revisions_[index],
      };
    }

    // Unable to find a revision in `revisions` with the same revisions schedule
    // as the constructor's `fetchDescriptor`. The caller should fetch the full
    // history for their fetchDescriptor.

    return {};
  }

  get readyPromise_() {
    if (!this.readyPromise__) this.readyPromise__ = this.fetchRevisions_();
    return this.readyPromise__;
  }

  async fetchRevisions_() {
    // Fetch the full history for each fetch descriptor, one at a time, until
    // one of them returns some data.
    for (const fetchDescriptor of this.fetchDescriptors_) {
      const request = new TimeseriesRequest({
        ...fetchDescriptor,
        statistic: 'avg',
        statistics: ['avg'],
      });
      for await (const data of request.reader()) {
        this.mergeRevisions_(data);
        if (this.revisions_.length) return;
      }
    }
  }

  mergeRevisions_(data) {
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

  isSameSchedule_(revision) {
    return isSameSchedule(revision, this.revisions_[0],
        this.revisions_[this.revisions_.length - 1]);
  }
}
