/* Copyright 2019 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import NotesRequest from './notes-request.js';
import {BatchIterator} from '@chopsui/batch-iterator';
import {TimeseriesesByLine} from './details-fetcher.js';
import {enumerate} from './utils.js';

export class NotesFetcher {
  constructor(lineDescriptors, revisionRanges) {
    this.revisionRanges_ = revisionRanges;
    this.fetchDescriptorsByLine_ = [];
    for (const lineDescriptor of lineDescriptors) {
      const fetchDescriptors = NotesFetcher.createFetchDescriptors(
          lineDescriptor);
      this.fetchDescriptorsByLine_.push({lineDescriptor, fetchDescriptors});
    }
    this.timeseriesesByLine_ = new TimeseriesesByLine(
        this.fetchDescriptorsByLine_, revisionRanges);
    this.batches_ = new BatchIterator();
  }

  static createFetchDescriptors(lineDescriptor) {
    const fetchDescriptors = [];
    const suites = ['', ...lineDescriptor.suites];
    const measurements = ['', lineDescriptor.measurements];
    const bots = ['', ...lineDescriptor.bots];
    const cases = ['', ...lineDescriptor.cases];
    for (const suite of suites) {
      for (const measurement of measurements) {
        for (const bots of bots) {
          for (const cas of cases) {
            fetchDescriptors.push({suite, measurement, bot, case: cas});
          }
        }
      }
    }
    return fetchDescriptors;
  }

  [Symbol.asyncIterator]() {
    return (async function* () {
      if (!this.revisionRanges_ || this.revisionRanges_.length === 0) return;

      for (const [lineIndex, {fetchDescriptors}] of enumerate(
          this.fetchDescriptorsByLine_)) {
        for (const [fetchIndex] of enumerate(fetchDescriptors)) {
          for (const [rangeIndex] of enumerate(this.revisionRanges_)) {
            this.batches_.add(this.fetchNotes_(
                lineIndex, rangeIndex, fetchIndex));
          }
        }
      }

      for await (const {results, errors} of this.batches_) {
        const timeseriesesByLine = this.timeseriesesByLine_.populatedResults;
        yield {errors, timeseriesesByLine};
      }
    }).call(this);
  }

  fetchNotes_(lineIndex, rangeIndex, fetchIndex) {
    return (async function* () {
      const request = new NotesRequest({
        ...this.fetchDescriptorsByLine_[lineIndex].fetchDescriptors[fetchIndex],
        ...this.revisionRanges_[rangeIndex],
      });
      for await (const timeseries of request.reader()) {
        this.timeseriesesByLine_.receive(
            lineIndex, rangeIndex, fetchIndex, timeseries);
        yield {/* Pump BatchIterator. */};
      }
    }).call(this);
  }
}
