/* Copyright 2019 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import {BatchIterator} from '@chopsui/batch-iterator';
import {TimeseriesesByLine} from './details-fetcher.js';
import {enumerate} from './utils.js';

import {
  TimeseriesRequest,
  LEVEL_OF_DETAIL,
  createFetchDescriptors,
} from './timeseries-request.js';

// Each lineDescriptor may require data from one or more fetchDescriptors.
// Fetch one or more fetchDescriptors per line, batch the readers, collate the
// data.
// Yields {timeseriesesByLine: [{lineDescriptor, timeserieses}], errors}.
export class ChartFetcher {
  constructor(lineDescriptors, revisions, levelOfDetail) {
    // These describe the timeseries that will be fetched.
    this.fetchDescriptorsByLine_ = [];
    for (const lineDescriptor of lineDescriptors) {
      const fetchDescriptors = createFetchDescriptors(
          lineDescriptor, levelOfDetail);
      for (const fetchDescriptor of fetchDescriptors) {
        Object.assign(fetchDescriptor, revisions);
      }
      this.fetchDescriptorsByLine_.push({lineDescriptor, fetchDescriptors});
    }

    // This collates results.
    this.timeseriesesByLine_ = new TimeseriesesByLine(
        this.fetchDescriptorsByLine_, [revisions]);

    this.histogramsByLine_ = new TimeseriesesByLine(
        this.fetchDescriptorsByLine_, [{}]);

    // This batches the stream of results to reduce unnecessary rendering.
    // This does not batch the results themselves, they need to be collated by
    // this.timeseriesesByLine_.
    this.batches_ = new BatchIterator();
  }

  [Symbol.asyncIterator]() {
    return (async function* () {
      for (const [lineIndex, {fetchDescriptors}] of enumerate(
          this.fetchDescriptorsByLine_)) {
        for (const [fetchIndex, fetchDescriptor] of enumerate(
            fetchDescriptors)) {
          this.batches_.add(this.fetchTimeseries_(
              lineIndex, fetchIndex, fetchDescriptor));
        }
        this.batches_.add(this.fetchHistogram_(lineIndex));
      }

      for await (const {results, errors} of this.batches_) {
        const timeseriesesByLine = this.timeseriesesByLine_.populatedResults;
        const histogramsByLine = this.histogramsByLine_.populatedResults;

        // ChartFetcher only supports a single revision range.
        for (const lineData of timeseriesesByLine) {
          lineData.timeserieses = lineData.timeseriesesByRange[0].timeserieses;
        }
        for (const lineData of histogramsByLine) {
          lineData.timeserieses = lineData.timeseriesesByRange[0].timeserieses;
        }

        yield {errors, timeseriesesByLine, histogramsByLine};
      }
    }).call(this);
  }

  fetchTimeseries_(lineIndex, fetchIndex, fetchDescriptor) {
    return (async function* () {
      const request = new TimeseriesRequest(fetchDescriptor);
      for await (const timeseries of request.reader()) {
        this.timeseriesesByLine_.receive(lineIndex, 0, fetchIndex, timeseries);
        yield {/* Pump BatchIterator. See timeseriesesByLine. */};
      }
    }).call(this);
  }

  fetchHistogram_(lineIndex) {
    return (async function* () {
      for (const [fetchIndex, fetchDescriptor] of enumerate(
          this.fetchDescriptorsByLine_[lineIndex].fetchDescriptors)) {
        const request = new TimeseriesRequest({
          ...fetchDescriptor,
          minRevision: undefined,
          maxRevision: undefined,
          limit: 1,
          levelOfDetail: LEVEL_OF_DETAIL.HISTOGRAM,
        });
        for await (const timeseries of request.reader()) {
          this.timeseriesesByLine_.receive(
              lineIndex, 0, fetchIndex, timeseries);
          yield {/* Pump BatchIterator. See timeseriesesByLine. */};

          // Stop after finding a Histogram.
          return;
        }
      }
    }).call(this);
  }
}
