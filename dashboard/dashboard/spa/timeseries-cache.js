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
   * actions.sweep (dispatched by actions.load and actions.disconnected) prunes
   * timeseries data that is no longer in use in order to free memory.
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
                          (other.running.avg * other.running.count)) / (
                            this.running.count + other.running.count);
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
    if (dict.r_commit_pos !== undefined) {
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
    testSuites: () => async (dispatch, getState) => {
      const rootState = getState();
      let path = 'testSuites';
      if (rootState.authHeaders) {
        path += 'Internal';
      }
      if (rootState[path]) {
        return await rootState[path];
      }
      const request = new cp.TestSuitesRequest({
        headers: rootState.authHeaders,
      });
      dispatch(cp.ElementBase.actions.updateObject(
          '', {[path]: request.response}));
      const entry = await request.response;
      dispatch(cp.ElementBase.actions.updateObject(
          '', {[path]: entry}));
      return entry;
    },

    describe: testSuite => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.ensureObject('testSuiteDescriptors'));
      const rootState = getState();
      const descriptors = rootState.testSuiteDescriptors;
      const cacheKey = testSuite.replace(/\./g, '_');
      if (descriptors[cacheKey]) return await descriptors[cacheKey];
      const request = new cp.DescribeRequest({
        headers: rootState.authHeaders,
        testSuite,
      });
      dispatch(cp.ElementBase.actions.updateObject(
          'testSuiteDescriptors', {[cacheKey]: request.response}));
      const descriptor = await request.response;
      dispatch(cp.ElementBase.actions.updateObject(
          'testSuiteDescriptors', {[cacheKey]: descriptor}));
      return descriptor;
    },

    load: (fetchDescriptor, refStatePath) => async (dispatch, getState) => {
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
      async (dispatch, getState) => {
        const rootState = getState();
        const columns = ['r_commit_pos', 'timestamp', 'value'];
        // TODO min/maxRev/Timestamp
        const request = new cp.TimeseriesRequest({
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

    sweep: () => async (dispatch, getState) => {
      dispatch({
        type: TimeseriesCache.reducers.sweep.typeName,
      });
    },
  };

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

      // TODO optimize and remove the slice(-1000)
      const data = (action.timeseries || []).slice(-1000).map(
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

    sweep: (rootState, action) => {
      // Abort fetches and free memory.
      const timeseries = {...rootState.timeseries};
      'TODO request.abort()';
      'TODO delete timeseries[cacheKey]';
      return {...rootState, timeseries};
    },
  };

  TimeseriesCache.cacheKey = fetchDescriptor => [
    fetchDescriptor.testSuite,
    fetchDescriptor.measurement,
    fetchDescriptor.bot,
    fetchDescriptor.testCase,
    fetchDescriptor.buildType,
  ].join('/').replace(/\./g, '_');

  cp.ElementBase.registerReducers(TimeseriesCache);

  return {
    FastHistogram,
    LEVEL_OF_DETAIL,
    TimeseriesCache,
  };
});
