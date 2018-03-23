/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  /*
   * Main entry point: actions.load(fetchDescriptor, refStatePath) returns
   * {unit: tr.b.Unit, data: [(tr.v.Histogram|cp.FastHistogram)]}
   *
   * A lineDescriptor describes a single line in the chart-base.
   * A lineDescriptor must specify
   *  * at least one testSuite
   *  * at least one bot
   *  * exactly one measurement
   *  * exactly one statistic
   *  * zero or more testCases
   *  * buildType (enum 'test' or 'reference')
   * When multiple testSuites, bots, or testCases are specified, the timeseries
   * are merged using RunningStatistics.merge().
   *
   * In order to load the data for a lineDescriptor, one or more
   * fetchDescriptors are generated for /api/timeseries2. See
   * Timeseries2Handler.
   * A fetchDescriptor contains a single testPath, columns, and optionally
   * minRev, maxRev, minTimestampMs, and maxTimestampMs.
   * Requests return timeseries, which are transformed into FastHistograms and
   * stored on the root state in the following cache structure:
   *
   * {
   *   ...rootState,
   *   timeseries: {
   *     $cacheKey: {
   *       references: [$statePath],
   *       unit: tr.b.Unit,
   *       data: [(FastHistogram|Histogram)],
   *       ranges: {
   *         xy: [
   *           {minRev, maxRev, minTimestampMs, maxTimestampMs, request},
   *         ],
   *         annotations: [...],
   *         histogram: [...],
   *       },
   *     },
   *   },
   * }
   *
   * While a Request is in-flight, it's in the corresponding range in |ranges|.
   * When a Request completes, it's |request| is undefined, but the range
   * remains in Ranges to indicate that its data is stored in
   * timeseries[testPath].data.
   *
   * Requests are cached separately by service-worker.js, so timeseries data
   * can only contain the data that is currently in use by chart-timeseries
   * and pivot-cell elements, as recorded by timeseries[testPath].references,
   * which is a list of statePaths pointing to chart-timeseries and pivot-cell
   * elements' states.
   *
   * The output of this big machine is chart-base.lines[].data.
   */

  const LEVEL_OF_DETAIL = {
    // chart-section's minimaps and alert-section's previews only need the (x,
    // y) coordinates to draw the line. FastHistograms contain only r_commit_pos
    // and the needed statistic.
    // Fetches /api/timeseries2/testpath&columns=r_commit_pos,value
    XY: 'xy',

    // chart-section's main chart can draw its lines using XY FastHistograms
    // while asynchronously fetching annotations (e.g.  alerts)
    // for a given revision range for tooltips and icons.
    // If an extant request overlaps a new request, then the new request can
    // fetch the difference and await the extant request.
    // Fetches /api/timeseries2/testpath&min_rev&max_rev&columns=revision,alert
    ANNOTATIONS: 'annotations',

    // pivot-table in chart-section and pivot-section need the full real
    // Histogram with all its statistics and diagnostics and samples.
    // chart-section will also request the full Histogram for the last point in
    // each timeseries in order to get its RelatedNameMaps.
    // Real Histograms contain full RunningStatistics, all diagnostics, all
    // samples. Request single Histograms at a time, even if the user brushes a
    // large range.
    // Fetches /api/histogram/testpath?rev
    HISTOGRAM: 'histogram',
  };

  // Supports XY and ANNOTATIONS levels of detail.
  // [Re]implements only the Histogram functionality needed for those levels.
  // Can be merged with real Histograms.
  class FastHistogram {
    constructor() {
      this.diagnostics = new tr.v.d.DiagnosticMap();
      // TODO use tr.b.math.RunningStatistic
      this.running = {count: 0, avg: 0, std: 0};
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

  FastHistogram.fromRow = (dict, fetchDescriptor, conversionFactor) => {
    const hist = new FastHistogram();
    if (![undefined, null].includes(dict.r_commit_pos)) {
      hist.diagnostics.set(
          tr.v.d.RESERVED_NAMES.CHROMIUM_COMMIT_POSITIONS,
          new tr.v.d.GenericSet([parseInt(dict.r_commit_pos)]));
    }
    if (dict.timestamp) {
      hist.diagnostics.set(
          tr.v.d.RESERVED_NAMES.UPLOAD_TIMESTAMP,
          new tr.v.d.DateRange(new Date(dict.timestamp) - 0));
    }
    if (dict.value !== undefined) {
      hist.running[fetchDescriptor.statistic] = dict.value * conversionFactor;
    }
    if (dict.d_avg !== undefined) {
      hist.running.avg = dict.d_avg * conversionFactor;
    }
    if (dict.error !== undefined) {
      hist.running.std = dict.error * conversionFactor;
    }
    hist.running.count = 1;
    return hist;
  };

  class TimeseriesRequest extends cp.RequestBase {
    constructor(options) {
      super(options);
      this.measurement_ = options.measurement;
      this.queryParams_ = new URLSearchParams();
      this.queryParams_.set('testSuite', options.testSuite);
      this.queryParams_.set('measurement', options.measurement);
      this.queryParams_.set('bot', options.bot);
      if (options.testCase) {
        this.queryParams_.set('testCase', options.testCase);
      }
      this.queryParams_.set('statistic', options.statistic);
      if (options.buildType) {
        this.queryParams_.set('buildType', options.buildType);
      }
      this.queryParams_.set('columns', options.columns.join(','));
      if (options.minRevision) {
        this.queryParams_.set('minRevision', options.minRevision);
      }
      if (options.maxRevision) {
        this.queryParams_.set('maxRevision', options.maxRevision);
      }
      if (options.minTimestamp) {
        this.queryParams_.set('minTimestamp', options.minTimestamp);
      }
      if (options.maxTimestamp) {
        this.queryParams_.set('maxTimestamp', options.maxTimestamp);
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
      const timeseries = [];
      const sequenceLength = 100;
      const nowMs = new Date() - 0;
      for (let i = 0; i < sequenceLength; i += 1) {
        // r_commit_pos, timestamp, value
        timeseries.push([
          i,
          nowMs - ((sequenceLength - i - 1) * (2592105834 / 50)),
          parseInt(100 * Math.random()),
        ]);
      }
      return {timeseries, units};
    }
  }

  if (1) {
    class TimeseriesCache extends cp.CacheBase {
      constructor(options, dispatch, getState) {
        super(options, dispatch, getState);
        this.fetchDescriptor_ = this.options_.fetchDescriptor;
        this.refStatePath_ = this.options_.refStatePath;
        this.columns_ = ['r_commit_pos', 'timestamp', 'value'];
      }

      get cacheStatePath_() {
        return 'timeseries';
      }

      async computeCacheKey_() {
        return [
          this.fetchDescriptor_.testSuite,
          this.fetchDescriptor_.measurement,
          this.fetchDescriptor_.bot,
          this.fetchDescriptor_.testCase,
          this.fetchDescriptor_.buildType,
        ].join('/').replace(/\./g, '_');
      }

      get isInCache_() {
        return this.rootState_.timeseries[this.cacheKey_] !== undefined;
      }

      async readFromCache_() {
        const entry = this.rootState_.timeseries[this.cacheKey_];
        return {unit: entry.unit, data: entry.data};
      }

      createRequest_() {
        return new TimeseriesRequest({
          headers: this.rootState_.authHeaders,
          testSuite: this.fetchDescriptor_.testSuite,
          measurement: this.fetchDescriptor_.measurement,
          bot: this.fetchDescriptor_.bot,
          testCase: this.fetchDescriptor_.testCase,
          statistic: this.fetchDescriptor_.statistic,
          buildType: this.fetchDescriptor_.buildType,
          columns: this.columns_,
        });
      }

      onStartRequest_(promise) {
        dispatch({
          type: TimeseriesCache.reducers.request.typeName,
          fetchDescriptor: this.fetchDescriptor_,
          cacheKey: this.cacheKey_,
          refStatePath: this.refStatePath_,
          promise,
        });
      }

      onFinishRequest_(result) {
        dispatch({
          type: TimeseriesCache.reducers.receive.typeName,
          fetchDescriptor: this.fetchDescriptor_,
          cacheKey: this.cacheKey_,
          columns: this.columns_,
          timeseries: result.timeseries,
          units: result.units,
        });
      }
    }

    const ReadTimeseries = options => async(dispatch, getState) =>
      await new TimeseriesCache(options, dispatch, getState).read();
  } else {
    const TimeseriesCache = {};

    function findCachePromises(cacheKey, refStatePath, rootState) {
      const promises = [];
      if (rootState.timeseries === undefined) return promises;
      const cacheEntry = rootState.timeseries[cacheKey];
      if (cacheEntry === undefined) return promises;
      // TODO handle other levels of detail
      for (const range of cacheEntry.ranges.xy) {
        if (range.request) promises.push(range.request.response);
      }
      return promises;
    }

    function shouldFetch(cacheKey, rootState) {
      if (rootState.timeseries === undefined) return true;
      const cacheEntry = rootState.timeseries[cacheKey];
      if (cacheEntry === undefined) return true;
      // TODO handle other levels of detail
      return false;
    }

    function csvRow(columns, cells) {
      const dict = {};
      for (let i = 0; i < columns.length; ++i) {
        dict[columns[i]] = cells[i];
      }
      return dict;
    }

    class AggregateError {
      constructor(errors) {
        this.errors = errors;
      }
    }

    TimeseriesCache.actions = {
      load: (fetchDescriptor, refStatePath) => async(dispatch, getState) => {
        // If fetchDescriptor is already satisfiable by the data in
        // rootState.timeseries, return. Otherwise await fetch it and store it
        // in rootState.timeseries.
        let rootState = getState();
        const cacheKey = TimeseriesCache.cacheKey(fetchDescriptor);

        const cachePromises = findCachePromises(
            cacheKey, refStatePath, rootState);
        // `await Promise.all([])` is not synchronous, so another load() could
        // sneak into that await and start a parallel fetch for the same data.
        if (cachePromises.length) {
          await Promise.all(cachePromises);
          rootState = getState();
        }

        if (shouldFetch(cacheKey, rootState)) {
          await dispatch(TimeseriesCache.actions.fetch_(
              fetchDescriptor, refStatePath, cacheKey));
          rootState = getState();
        }

        const cacheEntry = rootState.timeseries[cacheKey];
        return {
          unit: cacheEntry.unit,
          data: cacheEntry.data,
        };
      },

      fetch_: (fetchDescriptor, refStatePath, cacheKey) =>
        async(dispatch, getState) => {
          const rootState = getState();
          const columns = ['r_commit_pos', 'timestamp', 'value'];
          // TODO min/maxRev/Timestamp
          const request = new TimeseriesRequest({
            headers: rootState.authHeaders,
            testSuite: fetchDescriptor.testSuite,
            measurement: fetchDescriptor.measurement,
            bot: fetchDescriptor.bot,
            testCase: fetchDescriptor.testCase,
            statistic: fetchDescriptor.statistic,
            buildType: fetchDescriptor.buildType,
            columns,
          });
          dispatch({
            type: TimeseriesCache.reducers.request.typeName,
            fetchDescriptor,
            cacheKey,
            refStatePath,
            request,
          });
          const {timeseries, units} = await request.response;
          dispatch({
            type: TimeseriesCache.reducers.receive.typeName,
            fetchDescriptor,
            cacheKey,
            columns,
            timeseries,
            units,
          });
        },
    };

    TimeseriesCache.cacheKey = fetchDescriptor => [
      fetchDescriptor.testSuite,
      fetchDescriptor.measurement,
      fetchDescriptor.bot,
      fetchDescriptor.testCase,
      fetchDescriptor.buildType,
    ].join('/').replace(/\./g, '_');
  }

  TimeseriesCache.reducers = {
    request: (rootState, action) => {
      // Store action.request in
      // rootState.timeseries[cacheKey].ranges[levelOfDetail]

      let timeseries;
      if (rootState.timeseries) {
        timeseries = rootState.timeseries[action.cacheKey];
      }

      const references = [action.refStatePath];
      let ranges;
      if (timeseries) {
        references.push(...timeseries.references);
        ranges = {...timeseries.ranges};
        ranges[action.fetchDescriptor.levelOfDetail] = [
          ...ranges[action.fetchDescriptor.levelOfDetail]];
      } else {
        ranges = {
          [LEVEL_OF_DETAIL.XY]: [],
          [LEVEL_OF_DETAIL.ANNOTATIONS]: [],
          [LEVEL_OF_DETAIL.HISTOGRAM]: [],
        };
      }

      ranges[action.fetchDescriptor.levelOfDetail].push({
        request: action.request,
        // Some of these might be undefined. shouldFetch will need to handle
        // that. reducers.receive will populate all of them.
        minRev: action.fetchDescriptor.minRev,
        maxRev: action.fetchDescriptor.maxRev,
        minTimestampMs: action.fetchDescriptor.minTimestampMs,
        maxTimestampMs: action.fetchDescriptor.maxTimestampMs,
      });

      return {
        ...rootState,
        timeseries: {
          ...rootState.timeseries,
          [action.cacheKey]: {
            ...timeseries,
            references,
            ranges,
            data: [],
            unit: tr.b.Unit.byName.unitlessNumber,
          },
        },
      };
    },

    receive: (rootState, action) => {
      let unit = tr.b.Unit.byJSONName[action.units];
      let conversionFactor = 1;
      if (!unit) {
        const info = tr.v.LEGACY_UNIT_INFO.get(action.units);
        if (info) {
          conversionFactor = info.conversionFactor;
          unit = tr.b.Unit.byName[info.name];
        } else {
          unit = tr.b.Unit.byName.unitlessNumber;
        }
      }

      const data = (action.timeseries || []).map(
          row => FastHistogram.fromRow(
              csvRow(action.columns, row),
              action.fetchDescriptor,
              conversionFactor));

      return {
        ...rootState,
        timeseries: {
          ...rootState.timeseries,
          [action.cacheKey]: {
            ...rootState.timeseries[action.cacheKey],
            unit,
            data,
          }
        },
      };
    },
  };

  cp.ElementBase.registerReducers(TimeseriesCache);

  return {
    FastHistogram,
    LEVEL_OF_DETAIL,
    TimeseriesCache,
  };
});
