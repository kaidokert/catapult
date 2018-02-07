/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  /*
   * Main entry point: actions.load(lineDescriptors)
   *
   * A lineDescriptor describes a single line in the chart-base.
   * A lineDescriptor must specify
   *  * at least one testSuite
   *  * at least one bot
   *  * exactly one measurement
   *  * exactly one statistic
   *  * zero or more testCases
   *  * boolean ref
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
      this.running = {count: 0, avg: undefined};
    }

    clone() {
      const clone = new FastHistogram();
      clone.diagnostics.addDiagnostics(this.diagnostics);
      clone.running = {...this.running};
      return clone;
    }

    addHistogram(other) {
      this.diagnostics.addDiagnostics(other.diagnostics);
      this.running.avg = ((this.running.avg * this.running.count) +
                          (other.running.avg * other.running.count)) / (
                            this.running.count + other.running.count);
      this.running.count += other.running.count;
    }
  }

  FastHistogram.fromRow = (dict, fetchDescriptor) => {
    const hist = new FastHistogram();
    if (dict.r_commit_pos !== undefined) {
      hist.diagnostics.set(
          tr.v.d.RESERVED_NAMES.CHROMIUM_COMMIT_POSITIONS,
          new tr.v.d.GenericSet([dict.r_commit_pos]));
    }
    if (dict.value !== undefined) {
      hist.running[fetchDescriptor.statistic] = dict.value;
    }
    if (dict.d_avg !== undefined) {
      hist.running.avg = dict.d_avg;
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

  const cacheFill = (fetchDescriptor, rowStyle, signal) =>
    async (dispatch, getState) => {
      const rootState = getState();
      // TODO fall back to another well-defined column like timestamp (not
      // revision)
      const columns = ['r_commit_pos'];
      if (rowStyle === ROW_STYLE.HISTOGRAM) {
        columns.push('d_' + fetchDescriptor.statistic);
      } else {
        if (fetchDescriptor.statistic === 'avg') {
          columns.push('value');
        } else if (fetchDescriptor.statistic === 'std') {
          columns.push('error');
        }
      }
      const {timeseries, units} = await TimeseriesCache.fetch(
          fetchDescriptor, rowStyle, columns, rootState.authHeaders, signal);
      dispatch({
        type: TimeseriesCache.reducers.receive.typeName,
        fetchDescriptor,
        columns,
        timeseries,
        units,
      });
    };

  TimeseriesCache.fetchLocalhost = async (
      fetchDescriptor, rowStyle, columns, url, signal) => {
    if (rowStyle !== ROW_STYLE.HISTOGRAM) {
      return {error: `fake ${rowStyle} not supported`};
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
      // TODO TIR label
      testCaseParts = fetchDescriptor.testCase.split(':');
    }
    return [
      ...fetchDescriptor.bot.split(':'),
      ...fetchDescriptor.testSuite.split(':'),
      ...measurementParts,
      ...testCaseParts
    ].join('/');
  };

  TimeseriesCache.fetch = async (
      fetchDescriptor, rowStyle, columns, headers, signal) => {
    headers = new Headers(headers);
    headers.set('Content-type', 'application/x-www-form-urlencoded');

    let testPath = fetchDescriptor.testPath;
    if (rowStyle === ROW_STYLE.LEGACY_TBM2) {
      testPath = TimeseriesCache.compileTestPath(fetchDescriptor, true);
    }
    const options = new URLSearchParams({
      columns: columns.join(','),
      // TODO min/max_rev/timestamp
    });

    const url = `/api/timeseries2/${testPath}?${options}`;
    const fetchMark = tr.b.Timing.mark('fetch', 'timeseries');
    let responseJson;
    if (location.hostname === 'localhost') {
      responseJson = await TimeseriesCache.fetchLocalhost(
          fetchDescriptor, rowStyle, options, url, signal);
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

  const ROW_STYLE = {
    LEGACY: 'LEGACY',
    LEGACY_TBM2: 'LEGACY_TBM2',
    HISTOGRAM: 'HISTOGRAM',
  };

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

  TimeseriesCache.actions = {
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
      const promise = Promise.any([
        dispatch(cacheFill(fetchDescriptor, ROW_STYLE.HISTOGRAM, signal)),
        dispatch(cacheFill(fetchDescriptor, ROW_STYLE.LEGACY_TBM2, signal)),
        dispatch(cacheFill(fetchDescriptor, ROW_STYLE.LEGACY, signal)),
      ]);

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

      const unit = tr.b.Unit.byName[action.units] ||
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
      const timeseries = {...state.timeseries};
      'TODO abortController.abort()';
      'TODO delete timeseries[cacheKey]';
      return {...state, timeseries};
    },
  };

  cp.ElementBase.registerReducers(TimeseriesCache);

  return {
    FastHistogram,
    LEVEL_OF_DETAIL,
    TimeseriesCache,
  };
});
