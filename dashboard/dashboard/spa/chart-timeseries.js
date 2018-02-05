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
    // y) coordinates to draw the line. FastHistograms contain only the needed
    // statistic and revision, timestamp, r_chromium_commit_pos.
    // Fetches /api/timeseries2/testpath&columns=revision,value
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
      clone.running = {...clone.running};
      return clone;
    }

    addHistogram(other) {
      this.diagnostics.addDiagnostics(other.diagnostics);
      this.running.avg = ((this.running.avg * this.running.count) +
                          (other.running.avg * other.running.count)) / (
                            this.running.count + other.running.count);
      this.running.count += other.count;
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

  class MultiTimeseriesIterator {
    constructor(lineDescriptor, timeserieses) {
      this.lineDescriptor_ = lineDescriptor;
      this.timeserieses_ = timeserieses;
      this.indices_ = this.timeserieses_.map(timeseries =>
        this.findStartIndex_(timeseries));
    }

    findStartIndex_(timeseries) {
      return 0;
    }

    * [Symbol.iterator]() {
    }
  }

  class ChartTimeseries extends cp.ElementBase {
    disconnectedCallback() {
      this.dispatch('disconnected', this.statePath);
    }

    onDotMouseOver_(event) {
      this.dispatch('dotMouseOver', this.statePath,
          event.detail.line, event.detail.datum);
    }
  }

  ChartTimeseries.properties = cp.ElementBase.statePathProperties('statePath', {
    lines: {type: Array},
  });

  ChartTimeseries.newState = () => {
    return {
      ...cp.ChartBase.newState(),
      isLoading: false,
    };
  };

  ChartTimeseries.actions = {
    load: (statePath, lineDescriptors) => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(statePath, {lines: []}));
      // Load each lineDescriptor in parallel.
      for (const lineDescriptor of lineDescriptors) {
        dispatch(ChartTimeseries.actions.loadLineDescriptor(
            statePath, lineDescriptor));
      }
    },

    loadLineDescriptor: (statePath, lineDescriptor) =>
      async (dispatch, getState) => {
        const fetchDescriptors = ChartTimeseries.createFetchDescriptors(
            lineDescriptor);
        await Promise.all(fetchDescriptors.map(fetchDescriptor =>
          dispatch(ChartTimeseries.cache(fetchDescriptor, statePath))));
        await cp.ElementBase.afterRender();  // TODO remove
        dispatch({
          type: ChartTimeseries.reducers.layout.typeName,
          statePath,
          lineDescriptor,
          fetchDescriptors,
        });
      },

    dotMouseOver: (statePath, line, datum) => async (dispatch, getState) => {
      const rows = [];
      rows.push({name: 'value', value: datum.x});
      const commitPos = datum.hist.diagnostics.get(
          tr.v.d.RESERVED_NAMES.CHROMIUM_COMMIT_POSITIONS);
      if (commitPos) {
        const range = new tr.b.math.Range();
        for (const pos of commitPos) range.addValue(pos);
        let value = range.min;
        if (range.range) value += '-' + range.max;
        rows.push({name: 'chromium', value});
      }
      dispatch(cp.ChartBase.actions.tooltip(statePath, rows));
    },

    disconnected: statePath => async (dispatch, getState) => {
      dispatch({
        type: ChartTimeseries.reducers.cleanUp.typeName,
        statePath,
      });
    },
  };

  ChartTimeseries.reducers = {
    cleanUp: (state, action) => {
      // Abort fetches and free memory.
      const timeseries = {...state.timeseries};
      'TODO abortController.abort()';
      'TODO delete timeseries[cacheKey]';
      return {...state, timeseries};
    },

    request: (rootState, action) => {
      // Store action.abortController and action.promise in
      // rootState.timeseries[cacheKey].ranges[levelOfDetail]

      let timeseries;
      if (rootState.timeseries) {
        timeseries = rootState.timeseries[action.fetchDescriptor.cacheKey];
      }

      const references = [action.chartStatePath];
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
          ChartTimeseries.csvRow(action.columns, row),
          action.fetchDescriptor));
      /*
      if (cacheTimeseries) {
        data.push(...cacheTimeseries.data);
      }
      let dataIndex = 0;
      for (const row of action.timeseries) {
        const rowDict = ChartTimeseries.csvRow(action.columns, row);
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

    layout: (rootState, action) => {
      // Transform data from rootState to build a line to append to state.lines.
      const chartState = Polymer.Path.get(rootState, action.statePath);

      const lines = [];
      for (const line of chartState.lines) {
        // Clone the line object so we can reassign its color later.
        // Clone the data so we can re-normalize it later along with the new
        // line.
        lines.push({
          ...line,
          data: line.data.map(datum => {
            return {...datum};
          }),
        });
      }

      const timeserieses = action.fetchDescriptors.map(fetchDescriptor =>
          rootState.timeseries[fetchDescriptor.cacheKey].data);
      lines.push({
        descriptor: action.lineDescriptor,
        unit: rootState.timeseries[action.fetchDescriptors[0].cacheKey].unit,
        data: ChartTimeseries.layout(action.lineDescriptor, timeserieses),
        strokeWidth: 1,
      });

      // [Re]Assign colors.
      if (lines.length > 15) {
        cp.todo('brightnessRange');
      }
      const colors = tr.b.generateFixedColorScheme(
          lines.length, {hueOffset: 0.64});
      for (let i = 0; i < colors.length; ++i) {
        lines[i].color = colors[i].toString();
      }

      cp.ChartBase.fixLinesXInPlace(lines);
      cp.ChartBase.normalizeLinesInPlace(lines);

      cp.todo('[re]generate xAxisTicks');
      cp.todo('[re]generate yAxisTicks');

      return Polymer.Path.setImmutable(rootState, action.statePath, {
        ...chartState,
        lines,
      });
    },
  };

  ChartTimeseries.createFetchDescriptors = lineDescriptor => {
    // Short-cut for alerts-section to bypass experimental testPath computation.
    if (lineDescriptor.testPath) {
      return [
        {
          ...lineDescriptor,
          cacheKey: lineDescriptor.testPath.replace('.', '_'),
          levelOfDetail: LEVEL_OF_DETAIL.XY,
        }
      ];
    }

    const testSuites = lineDescriptor.testSuites || [lineDescriptor.testSuite];
    const bots = lineDescriptor.bots || [lineDescriptor.bot];
    if (bots.length === 0) throw new Error('At least 1 bot is required');
    let testCases = lineDescriptor.testCases || [lineDescriptor.testCase];
    if (testCases.length === 0) testCases = [undefined];

    const fetchDescriptors = [];
    for (const testSuite of testSuites) {
      for (const bot of bots) {
        for (const testCase of testCases) {
          const fetchDescriptor = {
            testSuite,
            bot,
            measurement: lineDescriptor.measurement,
            testCase,
            statistic: lineDescriptor.statistic,
            levelOfDetail: LEVEL_OF_DETAIL.XY,
          };
          fetchDescriptor.testPath = ChartTimeseries.compileTestPath(
              fetchDescriptor);
          fetchDescriptor.cacheKey = fetchDescriptor.testPath.replace('.', '_');
          fetchDescriptors.push(fetchDescriptor);
        }
      }
    }
    return fetchDescriptors;
  };

  ChartTimeseries.compileTestPath = (fetchDescriptor, opt_legacy) => {
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

  ChartTimeseries.findCachePromises = (fetchDescriptors, rootState) => {
    const promises = [];
    return promises;
  };

  ChartTimeseries.cache = (fetchDescriptor, chartStatePath) =>
    async (dispatch, getState) => {
      // If (testPath, options) is in rootState.timeseries, return.
      // Otherwise await fetch it and dispatch it into rootState.timeseries.

      const rootState = getState();
      await Promise.all(ChartTimeseries.findCachePromises(
          fetchDescriptor, rootState));
      if (!ChartTimeseries.shouldFetch(fetchDescriptor, rootState)) {
        return;
      }

      let abortController;
      let signal;
      if (window.AbortController) {
        abortController = new AbortController();
        signal = abortController.signal;
      }

      const promise = Promise.all([
        dispatch(ChartTimeseries.cacheFill(fetchDescriptor, true, signal)),
        // TODO try to fetch non-legacy rows
        // dispatch(ChartTimeseries.cacheFill(fetchDescriptor, false, signal)),
      ]);

      dispatch({
        type: ChartTimeseries.reducers.request.typeName,
        chartStatePath,
        fetchDescriptor,
        abortController,
        promise,
      });

      return await promise;
    };

  ChartTimeseries.shouldFetch = (fetchDescriptor, rootState) => {
    if (rootState.timeseries === undefined) return true;
    const existing = rootState.timeseries[fetchDescriptor.cacheKey];
    return true;
  };

  ChartTimeseries.cacheFill = (fetchDescriptor, legacy, signal) =>
    async (dispatch, getState) => {
      const rootState = getState();
      // TODO fall back to another well-defined column like timestamp (not
      // revision)
      const columns = ['r_commit_pos'];
      if (legacy) {
        columns.push('value');
      } else {
        columns.push('d_' + fetchDescriptor.statistic);
      }
      const {timeseries, units} = await ChartTimeseries.fetch(
          fetchDescriptor, legacy, columns, rootState.authHeaders, signal);
      dispatch({
        type: ChartTimeseries.reducers.receive.typeName,
        fetchDescriptor,
        columns,
        timeseries,
        units,
      });
    };

  ChartTimeseries.fetchLocalhost = async (
      fetchDescriptor, legacy, columns, url, signal) => {
    await tr.b.timeout(500);
    let units = 'unitlessNumber';
    if (fetchDescriptor.measurement.startsWith('memory:')) {
      units = 'sizeInBytes';
    }
    return {
      timeseries: cp.dummyTimeseries(columns),
      units,
    };
  };

  ChartTimeseries.fetch = async (
      fetchDescriptor, legacy, columns, headers, signal) => {
    headers = new Headers(headers);
    headers.set('Content-type', 'application/x-www-form-urlencoded');

    let testPath = fetchDescriptor.testPath;
    if (legacy) {
      testPath = ChartTimeseries.compileTestPath(fetchDescriptor, true);
    }
    const options = new URLSearchParams({
      columns: columns.join(','),
      // TODO min/max_rev/timestamp
    });

    const url = `/api/timeseries2/${testPath}?${options}`;
    const fetchMark = tr.b.Timing.mark('fetch', 'timeseries');
    let responseJson;
    if (location.hostname === 'localhost') {
      responseJson = await ChartTimeseries.fetchLocalhost(
          fetchDescriptor, legacy, options, url, signal);
    } else {
      const response = await fetch(url, {headers, signal});
      responseJson = await response.json();
    }
    fetchMark.end();
    if (responseJson.error) throw new Error(responseJson.error);
    return responseJson;
  };

  ChartTimeseries.layout = (lineDescriptor, timeserieses) => {
    // TODO sort timeseries by getX

    const histIndices = timeserieses.map(hists => {
      if (!lineDescriptor.minRev && !lineDescriptor.minTimestamp) return 0;
      // TODO binary search
      for (let histIndex = 0; histIndex < hists.length; ++histIndex) {
        const hist = hists[histIndex];
        /*
        if (lineDescriptor.minRev && hist.revision >= lineDescriptor.minRev) {
          return histIndex;
        }
        */
      }
    });

    function mergeHistograms() {
      let merged = timeserieses[0][histIndices[0]];
      if (timeserieses.length === 1) return merged;

      merged = merged.clone();
      for (let seriesIndex = 1; seriesIndex < timeserieses.length;
          ++seriesIndex) {
        const timeseries = timeserieses[seriesIndex];
        const histIndex = histIndices[seriesIndex];
        merged.addHistogram(timeseries[histIndex]);
      }
      return merged;
    }

    function getX(hist) {
      const commitPos = hist.diagnostics.get(
          tr.v.d.RESERVED_NAMES.CHROMIUM_COMMIT_POSITIONS);
      return tr.b.math.Statistics.mean(commitPos);
    }

    function canIncrementHistIndex(seriesIndex) {
      const timeseries = timeserieses[seriesIndex];
      const histIndex = histIndices[seriesIndex];
      if (histIndex === (timeseries.length - 1)) return false;
      /*
      if (lineDescriptor.maxRev && (hist.revision <= lineDescriptor.maxRev)) {
        return false;
      }
      if (lineDescriptor.maxTimestamp &&
          (hist.timestamp <= lineDescriptor.maxTimestamp)) {
        return false;
      }
      */
      return true;
    }

    function nextHist() {
      // Increment all histIndices that can be incremented and whose hists have
      // the smallest x coordinate.
      let minX = Infinity;
      for (let seriesIndex = 0; seriesIndex < timeserieses.length;
          ++seriesIndex) {
        if (!canIncrementHistIndex(seriesIndex)) continue;
        const timeseries = timeserieses[seriesIndex];
        const histIndex = histIndices[seriesIndex];
        const hist = timeseries[histIndex];
        const x = getX(hist);
        if (x < minX) {
          minX = x;
        }
      }

      if (minX === Infinity) {
        // Done iterating over all timeserieses.
        return undefined;
      }

      for (let seriesIndex = 0; seriesIndex < timeserieses.length;
          ++seriesIndex) {
        if (!canIncrementHistIndex(seriesIndex)) continue;
        const timeseries = timeserieses[seriesIndex];
        const histIndex = histIndices[seriesIndex];
        const hist = timeseries[histIndex];
        if (getX(hist) > minX) continue;

        ++histIndices[seriesIndex];
      }

      return mergeHistograms();
    }

    function getIcon(hist) {
      if (hist.alert) return hist.improvement ? 'thumb-up' : 'error';
      if (!lineDescriptor.icons) return '';
      // TODO remove lineDescriptor.icons
      const revisions = [...hist.diagnostics.get(
          tr.v.d.RESERVED_NAMES.CHROMIUM_COMMIT_POSITIONS)];
      for (const icon of lineDescriptor.icons) {
        if (revisions.includes(icon.revision)) return icon.icon;
      }
      return '';
    }

    const lineData = [];
    let hist;
    while (hist = nextHist()) {
      lineData.push({
        hist,
        x: getX(hist),
        y: hist.running[lineDescriptor.statistic],
        icon: getIcon(hist),
      });
    }
    return lineData;
  };

  ChartTimeseries.csvRow = (columns, cells) => {
    const dict = {};
    for (let i = 0; i < columns.length; ++i) {
      dict[columns[i]] = cells[i];
    }
    return dict;
  };

  cp.ElementBase.register(ChartTimeseries);

  return {
    ChartTimeseries,
  };
});
