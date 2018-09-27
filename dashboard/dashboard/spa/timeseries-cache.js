/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  /*
   * A lineDescriptor describes a single line in the chart-base.
   * A lineDescriptor must specify
   *  * at least one testSuite
   *  * at least one bot
   *  * exactly one measurement
   *  * exactly one statistic
   *  * zero or more testCases
   *  * buildType (enum 'test' or 'ref')
   * When multiple testSuites, bots, or testCases are specified, the timeseries
   * are merged using RunningStatistics.merge().
   *
   * In order to load the data for a lineDescriptor, one or more
   * fetchDescriptors are generated for /api/timeseries2. See
   * Timeseries2Handler.
   * A fetchDescriptor contains a single testPath, columns, and optionally
   * minRev, maxRev, minTimestampMs, and maxTimestampMs.
   * Requests return timeseries, which are arrays of FastHistograms.
   */

  const PRIORITY = {
    // Requests with priority=PREFETCH are not directly blocking the user, so
    // they can wait until either
    // 0. a user gesture increases their priority (e.g. opening a sparkline
    //    tab), or
    // 1. the priority queue is empty, or
    // 2. they are canceled.
    PREFETCH: 1,

    // Additional priorities may be added to support, for example, guessing
    // which PREFETCH requests are more or less likely to become USER requests,
    // or prioritizing requests for earlier sections over requests for sections
    // that are lower on the page.  Priority numbers won't be serialized
    // anywhere, so they can be changed when those features are added, so
    // there's no need to leave room between constants.

    // Requests with priority=USER are directly blocking the user, so always
    // pass them directly to the network.
    USER: 2,
  };

  const LEVEL_OF_DETAIL = Object.freeze({
    XY: 'XY',
    ANNOTATIONS_ONLY: 'ANNOTATIONS_ONLY',
    ANNOTATIONS: 'ANNOTATIONS',
    HISTOGRAM: 'HISTOGRAM',
  });

  function getColumnsByLevelOfDetail(levelOfDetail, statistic) {
    switch (levelOfDetail) {
      case LEVEL_OF_DETAIL.XY: return ['revision', 'timestamp', statistic];
      case LEVEL_OF_DETAIL.ANNOTATIONS_ONLY: return ['alert', 'diagnostic'];
      case LEVEL_OF_DETAIL.ANNOTATIONS:
        return [
          'revision', 'timestamp', statistic, 'alert', 'diagnostics',
          'revisions',
        ];
      case LEVEL_OF_DETAIL.HISTOGRAMS: return ['revision', 'histogram'];
      default: throw new Error(`${level} is not a valid Level Of Detail`);
    }
  }

  // Supports XY and ANNOTATIONS levels of detail.
  // [Re]implements only the Histogram functionality needed for those levels.
  // Can be merged with real Histograms.
  class FastHistogram {
    constructor() {
      this.diagnostics = new tr.v.d.DiagnosticMap();
      // TODO use tr.b.math.RunningStatistic
      this.running = {count: 0, avg: 0, std: 0};
      this.unit = undefined;
    }

    addHistogram(other) {
      this.diagnostics.addDiagnostics(other.diagnostics);
      const deltaMean = this.running.avg - other.running.avg;
      this.running.avg = ((this.running.avg * this.running.count) +
                          (other.running.avg * other.running.count)) /
                         (this.running.count + other.running.count);
      const thisVar = this.running.std * this.running.std;
      const otherVar = other.running.std * other.running.std;
      const thisCount = this.running.count;
      this.running.count += other.running.count;
      this.running.std = Math.sqrt(thisVar + otherVar + (
        thisCount * other.running.count * deltaMean * deltaMean /
        this.running.count));
    }
  }

  FastHistogram.fromRow = (dict, statistic, conversionFactor, unit) => {
    const hist = new FastHistogram();
    hist.unit = unit;
    const commitPos = dict.revision;
    if (commitPos !== null && commitPos !== undefined) {
      hist.diagnostics.set(
          tr.v.d.RESERVED_NAMES.CHROMIUM_COMMIT_POSITIONS,
          new tr.v.d.GenericSet([parseInt(commitPos)]));
    }

    if (dict.timestamp) {
      hist.diagnostics.set(
          tr.v.d.RESERVED_NAMES.UPLOAD_TIMESTAMP,
          new tr.v.d.DateRange(new Date(dict.timestamp) - 0));
    }
    if (dict.value !== undefined) {
      hist.running[statistic] = dict.value * conversionFactor;
    }
    if (dict.avg !== undefined) {
      hist.running.avg = dict.avg * conversionFactor;
    }
    if (dict.error !== undefined) {
      hist.running.std = dict.error * conversionFactor;
    }
    hist.running.count = 1;
    return hist;
  };

  class TimeseriesRequest extends cp.RequestBase {
    /*
     * type options = {
     *   testSuite: string,
     *   measurement: string,
     *   bot: string,
     *   testCase?: string,
     *   statistic: string,
     *   buildType?: any,
     *
     *   columns: [string],
     *
     *   // Commit revision range
     *   minRevision?: number,
     *   maxRevision?: number,
     * }
     */
    constructor(options) {
      super(options);
      this.method_ = 'POST';
      this.measurement_ = options.measurement;
      this.queryParams_ = new URLSearchParams();
      this.queryParams_.set('test_suite', options.testSuite);
      this.queryParams_.set('measurement', options.measurement);
      this.queryParams_.set('bot', options.bot);

      if (options.testCase) {
        this.queryParams_.set('test_case', options.testCase);
      }

      this.statistic_ = options.statistic || 'avg';
      if (options.statistic) {
        this.queryParams_.set('statistic', options.statistic);
      }

      // Question(Sam): What is buildType?
      if (options.buildType) {
        this.queryParams_.set('build_type', options.buildType);
      }

      this.columns_ = getColumnsByLevelOfDetail(
          options.levelOfDetail, this.statistic_);
      this.queryParams_.set('columns', this.columns_.join(','));

      if (options.minRevision) {
        this.queryParams_.set('min_revision', options.minRevision);
      }
      if (options.maxRevision) {
        this.queryParams_.set('max_revision', options.maxRevision);
      }
      if (options.minTimestamp) {
        this.queryParams_.set('min_timestamp', options.minTimestamp);
      }
      if (options.maxTimestamp) {
        this.queryParams_.set('max_timestamp', options.maxTimestamp);
      }

      this.timeseries_ = [];
    }

    postProcess_(json, doNormalize=true) {
      if (!json) return;
      let unit = tr.b.Unit.byJSONName[json.units];
      let conversionFactor = 1;
      if (!unit) {
        const info = tr.v.LEGACY_UNIT_INFO.get(action.units);
        if (info) {
          conversionFactor = info.conversionFactor || 1;
          unit = tr.b.Unit.byName[info.name];
        } else {
          unit = tr.b.Unit.byName.unitlessNumber;
        }
      }
      // The backend returns denormalized (tabular) data, but
      // TimeseriesCacheRequest yields normalized (objects) data for speed.
      // Rely on TimeseriesCacheRequest to merge data from network requests in
      // with previous data, so that json is always the total data available.
      this.timeseries_ = json.data.map(row => FastHistogram.fromRow(
          (doNormalize ? normalize(this.columns_, row) : row),
          this.statistic_, conversionFactor, unit));
    }

    async* reader() {
      const listener = new cp.ServiceWorkerListener(this.url_);
      await this.response; // calls postProcess_
      if (this.timeseries_.length) {
        yield this.timeseries_;
      }
      for await (const update of listener) {
        this.postProcess_(update, false);
        yield this.timeseries_;
      }
    }

    get url_() {
      return `/api/timeseries2?${this.queryParams_}`;
    }

    async localhostResponse_() {
      let units = 'unitlessNumber';
      if (this.measurement_.startsWith('memory:')) {
        units = 'sizeInBytes_smallerIsBetter';
      }
      if (this.measurement_.startsWith('cpu:') ||
          this.measurement_.startsWith('loading') ||
          this.measurement_.startsWith('startup')) {
        units = 'ms_smallerIsBetter';
      }
      if (this.measurement_.startsWith('power')) {
        units = 'W_smallerIsBetter';
      }
      const data = [];
      const sequenceLength = 100;
      const nowMs = new Date() - 0;
      for (let i = 0; i < sequenceLength; i += 1) {
        // revision, timestamp, value
        data.push([
          i * 100,
          nowMs - ((sequenceLength - i - 1) * (2592105834 / 50)),
          parseInt(100 * Math.random()),
        ]);
      }
      return {data, units};
    }
  }

  // TODO merge with normalize() in timeseries-cache-request.js via ES6 module
  function normalize(columns, cells) {
    const dict = {};
    for (let i = 0; i < columns.length; ++i) {
      dict[columns[i]] = cells[i];
    }
    return dict;
  }

  const TimeseriesReader = options => new TimeseriesRequest(options).reader();

  return {
    FastHistogram,
    LEVEL_OF_DETAIL,
    TimeseriesReader,
    TimeseriesRequest,
  };
});
