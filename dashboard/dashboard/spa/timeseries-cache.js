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
   *           {
   *             minRev, maxRev, minTimestampMs, maxTimestampMs,
   *             promise, abortController,
   *           },
   *         ],
   *         annotations: [...],
   *         histogram: [...],
   *       },
   *     },
   *   },
   * }
   *
   * While a Request is in-flight, its |promise| and |abortController| are set
   * in the corresponding range in |ranges|. When a Request completes, its
   * promise and abortController are undefined, but the range remains in Ranges
   * to indicate that its data is stored in timeseries[testPath].data.
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

  FastHistogram.fromRow = (dict, fetchDescriptor) => {
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
      hist.running[fetchDescriptor.statistic] = dict.value;
    }
    if (dict.d_avg !== undefined) {
      hist.running.avg = dict.d_avg;
    }
    if (dict.error !== undefined) {
      hist.running.std = dict.error;
    }
    hist.running.count = 1;
    return hist;
  };

  const TimeseriesCache = {};

  function findCachePromises(fetchDescriptor, refStatePath, rootState) {
    const promises = [];
    if (rootState.timeseries === undefined) return promises;
    const cacheEntry = rootState.timeseries[fetchDescriptor.cacheKey];
    if (cacheEntry === undefined) return promises;
    // TODO handle other levels of detail
    for (const range of cacheEntry.ranges.xy) {
      if (range.promise) promises.push(range.promise);
    }
    return promises;
  }

  function shouldFetch(fetchDescriptor, rootState) {
    if (rootState.timeseries === undefined) return true;
    const cacheEntry = rootState.timeseries[fetchDescriptor.cacheKey];
    if (cacheEntry === undefined) return true;
    // TODO handle other levels of detail
    return false;
  }

  const cacheFill = (fetchDescriptor, legacyTBM2, signal) =>
    async (dispatch, getState) => {
      const rootState = getState();
      const columns = ['r_commit_pos', 'timestamp', 'value', 'error'];
      if (!legacyTBM2 && !['avg', 'std'].includes(fetchDescriptor.statistic)) {
        // If this testpath is created by
        // add_histograms_queue._ProcessRowAndHistogram with the unsuffixed
        // test_name (measurement), then this statistic is in a supplemental
        // column created by _PopulateNumericalFields.
        columns.push('d_' + fetchDescriptor.statistic);
        // If this is a pre-TBM2-style timeseries, then the d_statistic column
        // will be null, and the corresponding line in the chart-timeseries will
        // be empty, and that's the best we can do.
      }
      const {timeseries, units} = await TimeseriesCache.fetch(
          fetchDescriptor, legacyTBM2, columns, rootState.authHeaders, signal);
      dispatch({
        type: TimeseriesCache.reducers.receive.typeName,
        fetchDescriptor,
        columns,
        timeseries,
        units,
      });
    };

  TimeseriesCache.fetchLocalhost = async (
      fetchDescriptor, legacyTBM2, columns, url, signal) => {
    if (legacyTBM2) {
      return {error: `legacyTBM2 dummyTimeseries not supported`};
    }
    await tr.b.timeout(1000);
    let units = 'unitlessNumber';
    if (fetchDescriptor.measurement.startsWith('memory:')) {
      units = 'sizeInBytes';
    }
    return {
      timeseries: cp.dummyTimeseries(columns),
      units,
    };
  };

  TimeseriesCache.compileTestPath = (fetchDescriptor, opt_legacy) => {
    let measurement = fetchDescriptor.measurement;
    if (opt_legacy) measurement += '_' + fetchDescriptor.statistic;
    const measurementParts = [measurement];  // TODO v8 test paths
    let testCaseParts = [];
    if (fetchDescriptor.testCase) {
      testCaseParts = fetchDescriptor.testCase.split(':');
      if (fetchDescriptor.testSuite.startsWith('system_health')) {
        testCaseParts = [
          testCaseParts.slice(0, 2).join('_'),
          testCaseParts.join('_'),
        ];
      }
    }
    // TODO _ref
    const buildTypeParts = (
      (fetchDescriptor.buildType === 'reference') ? ['ref'] : []);
    return [
      ...fetchDescriptor.bot.split(':'),
      ...fetchDescriptor.testSuite.split(':'),
      ...measurementParts,
      ...testCaseParts,
      ...buildTypeParts,
    ].join('/');
  };

  TimeseriesCache.fetch = async (
      fetchDescriptor, legacyTBM2, columns, headers, signal) => {
    headers = new Headers(headers);
    headers.set('Content-type', 'application/x-www-form-urlencoded');
    const testPath = legacyTBM2 ?
        TimeseriesCache.compileTestPath(fetchDescriptor, true) :
        fetchDescriptor.testPath;
    const options = new URLSearchParams({
      columns: columns.join(','),
      // TODO min/max_rev/timestamp
    });
    const url = `/api/timeseries2/${testPath}?${options}`;
    const fetchMark = tr.b.Timing.mark('fetch', 'timeseries');
    let responseJson;
    if (location.hostname === 'localhost') {
      responseJson = await TimeseriesCache.fetchLocalhost(
          fetchDescriptor, legacyTBM2, options, url, signal);
    } else {
      const response = await fetch(url, {headers, signal});
      responseJson = await response.json();
    }
    fetchMark.end();
    if (responseJson.error) throw new Error(responseJson.error);
    return responseJson;
  };

  function csvRow(columns, cells) {
    const dict = {};
    for (let i = 0; i < columns.length; ++i) {
      dict[columns[i]] = cells[i];
    }
    return dict;
  }

  function abortSignal() {
    if (!window.AbortController) return {};
    const abortController = new AbortController();
    return {abortController, signal: abortController.signal};
  }

  class AggregateError {
    constructor(errors) {
      this.errors = errors;
    }
  }

  // Resolve with the value of the first promise that resolves.
  // If all promises reject, then reject with an AggregateError.
  Promise.any = async promises => {
    const errors = [];
    for (const p of promises) {
      try {
        return await p;
      } catch (error) {
        errors.push(error);
      }
    }
    throw new AggregateError(errors);
  };

  TimeseriesCache.fetchTestSuites = async headers => {
    headers = new Headers(headers);
    const fetchMark = tr.b.Timing.mark('fetch', 'test_suites');
    let responseJson;
    if (location.hostname === 'localhost') {
      responseJson = cp.dummyTestSuites();
    } else {
      const response = await fetch('/api/test_suites', {headers});
      responseJson = await response.json();
    }
    fetchMark.end();
    return responseJson;
  };

  TimeseriesCache.fetchDescribe = async headers => {
    headers = new Headers(headers);
    const fetchMark = tr.b.Timing.mark('fetch', 'test_suites');
    let responseJson;
    if (location.hostname === 'localhost') {
      responseJson = cp.dummyTestSuites();
    } else {
      const response = await fetch('/api/test_suites', {headers});
      responseJson = await response.json();
    }
    fetchMark.end();
    return responseJson;
  };

  // TODO refactor all types of fetches to share more code

  TimeseriesCache.actions = {
    testSuites: () => async (dispatch, getState) => {
      const rootState = getState();
      let path = 'testSuites';
      if (rootState.authHeaders) path += 'Internal';
      if (rootState[path]) return await rootState[path];
      const promise = TimeseriesCache.fetchTestSuites(
          rootState.authHeaders);
      dispatch(cp.ElementBase.actions.updateObject(
          '', {[path]: promise}));
      const testSuites = await promise;
      const options = cp.OptionGroup.groupValues(testSuites);
      const entry = {options, count: testSuites.length};
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
      const promise = TimeseriesCache.fetchDescribe(
          rootState.authHeaders, testSuite);
      dispatch(cp.ElementBase.actions.updateObject(
          'testSuiteDescriptors', {[cacheKey]: promise}));
      const descriptor = await promise;
      dispatch(cp.ElementBase.actions.updateObject(
          'testSuiteDescriptors', {[cacheKey]: descriptor}));
      return descriptor;
    },

    load: (fetchDescriptor, refStatePath) => async (dispatch, getState) => {
      // If fetchDescriptor is already satisfiable by the data in
      // rootState.timeseries, return. Otherwise await fetch it and store it
      // in rootState.timeseries.
      let rootState = getState();

      const cachePromises = findCachePromises(
          fetchDescriptor, refStatePath, rootState);
      // `await Promise.all([])` is not synchronous, so another load() could
      // sneak into that await and start a parallel fetch for the same data.
      if (cachePromises.length) {
        await Promise.all(cachePromises);
        rootState = getState();
      }

      if (shouldFetch(fetchDescriptor, rootState)) {
        await dispatch(TimeseriesCache.actions.fetch_(
            fetchDescriptor, refStatePath));
        rootState = getState();
      }

      const cacheEntry = rootState.timeseries[fetchDescriptor.cacheKey];
      return {
        unit: cacheEntry.unit,
        data: cacheEntry.data,
      };
    },

    fetch_: (fetchDescriptor, refStatePath) => async (dispatch, getState) => {
      const {abortController, signal} = abortSignal();
      let promise;
      if (location.hostname === 'localhost') {
        promise = dispatch(cacheFill(fetchDescriptor, false, signal));
      } else {
        promise = Promise.any([
          dispatch(cacheFill(fetchDescriptor, false, signal)),
          dispatch(cacheFill(fetchDescriptor, true, signal)),
        ]);
      }

      dispatch({
        type: TimeseriesCache.reducers.request.typeName,
        refStatePath,
        fetchDescriptor,
        abortController,
        promise,
      });

      await promise;
    },

    sweep: () => async (dispatch, getState) => {
      dispatch({
        type: TimeseriesCache.reducers.sweep.typeName,
      });
    },
  };

  TimeseriesCache.reducers = {
    request: (rootState, action) => {
      // Store action.abortController and action.promise in
      // rootState.timeseries[cacheKey].ranges[levelOfDetail]

      let timeseries;
      if (rootState.timeseries) {
        timeseries = rootState.timeseries[action.fetchDescriptor.cacheKey];
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
        promise: action.promise,
        abortController: action.abortController,
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
          [action.fetchDescriptor.cacheKey]: {
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
      const cacheTimeseries = rootState.timeseries[
          action.fetchDescriptor.cacheKey];
      const data = action.timeseries.map(row => FastHistogram.fromRow(
          csvRow(action.columns, row), action.fetchDescriptor));
      /*
      if (cacheTimeseries) {
        data.push(...cacheTimeseries.data);
      }
      let dataIndex = 0;
      for (const row of action.timeseries) {
        const rowDict = csvRow(action.columns, row);
        while (dataIndex < data.length &&
               data[dataIndex].revision < rowDict.revision) {
          ++dataIndex;
        }
        if (dataIndex === data.length) {
          data.push(new FastHistogram(rowDict));
          ++dataIndex;
        } else if (data[dataIndex].revision > rowDict.revision) {
          data.splice(dataIndex, 0, new FastHistogram(rowDict));
        } else {
          data[dataIndex].addDict(rowDict);
        }
      }
      */

      const unit = tr.b.Unit.byJSONName[action.units] ||
        tr.v.LEGACY_UNIT_INFO.get(action.units) ||
        tr.b.Unit.byName.unitlessNumber;

      return {
        ...rootState,
        timeseries: {
          ...rootState.timeseries,
          [action.fetchDescriptor.cacheKey]: {
            ...cacheTimeseries,
            unit,
            data,
          }
        },
      };
    },

    sweep: (rootState, action) => {
      // Abort fetches and free memory.
      const timeseries = {...rootState.timeseries};
      'TODO abortController.abort()';
      'TODO delete timeseries[cacheKey]';
      return {...rootState, timeseries};
    },
  };

  cp.ElementBase.registerReducers(TimeseriesCache);

  return {
    FastHistogram,
    LEVEL_OF_DETAIL,
    TimeseriesCache,
  };
});
