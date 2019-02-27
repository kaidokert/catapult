/* Copyright 2019 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  // Maximum number of data points to take from source timeseries.
  // http://crbug.com/936305
  const MAX_POINTS = 1000;

  // Get the x-coordinate for a datum. http://crbug.com/936307
  function getX(datum) {
    return datum.revision;
  }

  // Merge source datum into target datum.
  function mergeData(target, source) {
    if (target.revision === undefined) {
      // target is empty, so clone source into it.
      Object.assign(target, source);
      if (target.diagnostics) {
        const shallowClone = new tr.v.d.DiagnosticMap();
        shallowClone.addDiagnostics(target.diagnostics);
        target.diagnostics = shallowClone;
      }
      return;
    }

    // Merge diagnostics from source into target.
    if (source.diagnostics) {
      if (!target.diagnostics) {
        target.diagnostics = new tr.v.d.DiagnosticMap();
      }
      target.diagnostics.addDiagnostics(source.diagnostics);
    }

    target.revision = Math.min(target.revision, source.revision);
    if (source.timestamp < target.timestamp) {
      target.timestamp = source.timestamp;
    }

    // Merge avg, std, count, sum, min, max from source into target.
    // See also tr.b.math.RunningStatistics.merge()
    // The following uses Welford's algorithm for computing running mean
    // and variance. See http://www.johndcook.com/blog/standard_deviation.
    const deltaMean = target.avg - source.avg;
    target.avg = (
      (target.avg * target.count) + (source.avg * source.count)) /
      (target.count + source.count);
    const thisVar = target.std * target.std;
    const otherVar = source.std * source.std;
    const thisCount = target.count;
    target.count += source.count;
    target.std = Math.sqrt(thisVar + otherVar + (
      thisCount * source.count * deltaMean * deltaMean /
      target.count));
    if (target.sum === undefined) target.sum = 0;
    if (source.sum) target.sum += source.sum;
    if (target.min === undefined) {
      if (source.min !== undefined) {
        target.min = source.min;
      }
    } else if (source.min !== undefined) {
      target.min = Math.min(target.min, source.min);
    }
    if (target.max === undefined) {
      if (source.max !== undefined) {
        target.max = source.max;
      }
    } else if (source.max !== undefined) {
      target.max = Math.max(target.max, source.max);
    }
  }

  class TimeseriesIterator {
    constructor(timeseries, range) {
      this.minRevision_ = range.minRevision;
      this.maxRevision_ = range.maxRevision;
      this.timeseries_ = timeseries;

      // This may be fractional. See roundIndex_ and indexDelta_.
      this.index_ = this.findStartIndex_();

      // The index of the last datum that will be yielded:
      this.endIndex_ = Math.min(
          this.findEndIndex_(), this.timeseries_.length - 1);

      // this.timeseries_ may have many thousands of data points. Processing
      // that much data could take a lot of time, and would be wasted since
      // there are only so many horizontal pixels.
      // indexDelta_ allows TimeseriesIterator to uniformly sample
      // this.timeseries_.
      // When indexDelta_ is 2, every other data point from this source
      // timeseries will be skipped. When 3, two points are skipped.
      // When 1.5, every third data point is skipped.
      this.indexDelta_ = Math.max(
          1, (this.endIndex_ - this.index_) / MAX_POINTS);
    }

    findStartIndex_() {
      if (this.minRevision_) {
        return tr.b.findLowIndexInSortedArray(
            this.timeseries_, getX,
            this.minRevision_);
      }
      return 0;
    }

    findEndIndex_() {
      if (this.maxRevision_) {
        return tr.b.findLowIndexInSortedArray(
            this.timeseries_, getX,
            this.maxRevision_);
      }
      return this.timeseries_.length - 1;
    }

    get current() {
      return this.timeseries_[Math.min(this.roundIndex_, this.endIndex_)];
    }

    get roundIndex_() {
      return Math.round(this.index_);
    }

    get done() {
      return !this.current || (this.roundIndex_ > this.endIndex_);
    }

    next() {
      this.index_ += this.indexDelta_;
    }
  }

  class TimeseriesMerger {
    constructor(timeserieses, range) {
      this.iterators_ = timeserieses.map(timeseries => new TimeseriesIterator(
          timeseries, range));
    }

    get allDone_() {
      for (const iterator of this.iterators_) {
        if (!iterator.done) return false;
      }
      return true;
    }

    * [Symbol.iterator]() {
      while (!this.allDone_) {
        // Merge the current data points from all iterators_ into a new merged
        // data point, and find the minimum x-coordinate from those current data
        // points.
        const merged = {};
        let minX = Infinity;
        for (const iterator of this.iterators_) {
          if (!iterator.current) continue;
          mergeData(merged, iterator.current);
          if (!iterator.done) {
            minX = Math.min(minX, getX(iterator.current));
          }
        }
        yield [minX, merged];

        // Increment all iterators whose X coordinate is minX.
        for (const iterator of this.iterators_) {
          if (!iterator.done && getX(iterator.current) === minX) {
            iterator.next();
          }
        }
      }
    }
  }

  return {TimeseriesMerger};
});
