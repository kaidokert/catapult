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
  class FastHistogram {
    constructor() {
      this.diagnostics = new Map();
      this.running = {};
    }
  }

  class ChartTimeseries extends cp.ElementBase {
    disconnectedCallback() {
      this.dispatch('disconnected', this.statePath);
    }

    onDotMouseOver_(event) {
      this.dispatch('dotMouseOver', this.statePath, event.detail.datum);
    }
  }

  ChartTimeseries.properties = cp.ElementBase.statePathProperties('statePath', {
    lines: {type: Array},
  });

  ChartTimeseries.newState = () => {
    return {
      brushWidth: 10,
      dotCursor: 'pointer',
      dotRadius: 6,
      height: 200,
      isLoading: false,
      lines: [],
      showXAxisTickLines: false,
      showYAxisTickLines: false,
      tooltip: {isVisible: false},
      xAxisHeight: 0,
      xAxisTicks: [],
      xBrushes: [],
      yAxisTicks: [],
      yAxisWidth: 0,
      yBrushes: [],
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
        const fetchDescriptors = ChartTimeseries.fetchDescriptors(
            lineDescriptor);
        await Promise.all(fetchDescriptors.map(fetchDescriptor =>
          ChartTimeseries.cache(
              fetchDescriptor, statePath, dispatch, getState)));
        dispatch({
          reducer: ChartTimeseries.reducers.layout,
          statePath,
          lineDescriptor,
          fetchDescriptors,
        });
      },

    dotMouseOver: (statePath, datum) => async (dispatch, getState) => {
      dispatch(cp.ChartBase.actions.tooltip(statePath, [
        {name: 'value', value: datum.value},
        {name: 'chromium', value: datum.chromiumCommitPositions.join('-')},
      ]));
    },

    disconnected: statePath => async (dispatch, getState) => {
      dispatch({
        reducer: ChartTimeseries.reducers.cleanUp,
        statePath,
      });
    },
  };

  ChartTimeseries.reducers = {
    cleanUp: (state, action) => {
      // Cancel requests and free memory
      const timeseries = {...state.timeseries};
      'TODO abortController.abort()';
      'TODO delete timeseries[cacheKey]';
      return {...state, timeseries};
    },

    request: (rootState, action) => {
      // Store action.abortController and action.promise in
      // rootState.timeseries[cacheKey].ranges[levelOfDetail]
      const timeseries = rootState.timeseries[action.fetchDescriptor.cacheKey];

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
          },
        },
      };
    },

    receive: (rootState, action) => {
      const cacheTimeseries = rootState.timeseries[action.cacheKey];
      const data = [];
      if (cacheTimeseries) {
        data.push(...cacheTimeseries.data);
      }
      let dataIndex = 1;
      for (const row of action.timeseries) {
        const rowDict = ChartTimeseries.csvRow(action.options.columns, row);
        while (dataIndex < data.length &&
               data[dataIndex].revision < rowDict.revision) {
          ++dataIndex;
        }
        if (dataIndex === data.length) {
          data.push(new FastHistogram(rowDict));
        } else if (data[dataIndex].revision > rowDict.revision) {
          data.splice(dataIndex, 0, new FastHistogram(rowDict));
        } else {
          data[dataIndex].addDict(rowDict);
        }
      }

      return {
        ...state,
        timeseries: {
          ...rootState.timeseries,
          [action.cacheKey]: {
            ...cacheTimeseries,
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

      lines.push({
        descriptor: action.lineDescriptor,
        data: ChartTimeseries.layout(
            lineDescriptor, action.fetchDescriptors.map(fetchDescriptor =>
              rootState.timeseries[fetchDescriptor.cacheKey].data)),
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

  ChartTimeseries.fetchDescriptors = lineDescriptor => {
    // Short-cut for alerts-section to bypass experimental testPath computation.
    if (lineDescriptor.testPath) {
      return [
        {
          ...lineDescriptor,
          cacheKey: lineDescriptor.testPath.replace('.', '_'),
        }
      ];
    }

    const testSuites = lineDescriptor.testSuites || [lineDescriptor.testSuite];
    const bots = lineDescriptor.bots || [lineDescriptor.bot];
    const testCases = lineDescriptor.testCases || [];
    if (lineDescriptor.testCase) {
      testCases.push(lineDescriptor.testCase);
    } else {
      testCases.push(undefined);
    }

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
          };
          fetchDescriptor.testPath = ChartTimeseries.testPath(fetchDescriptor);
          fetchDescriptor.cacheKey = testPath.replace('.', '_'),
          fetchDescriptors.push(fetchDescriptor);
        }
      }
    }
    return fetchDescriptors;
  };

  ChartTimeseries.testPath = (fetchDescriptor, opt_legacy) => {
    let measurement = fetchDescriptor.measurement;
    if (opt_legacy) measurement += '_' + fetchDescriptor.statistic;
    const measurementParts = [measurement];  // TODO v8 test paths
    return [
      ...fetchDescriptor.bot.split(':'),
      ...fetchDescriptor.testSuite.split(':'),
      ...measurementParts,
      ...fetchDescriptor.testCase.split(':').filter(x => x),  // TODO TIR label
    ].join('/');
  };

  ChartTimeseries.findCachePromises = (fetchDescriptors, rootState) => {
    const promises = [];
    return promises;
  };

  ChartTimeseries.cache = async (
      fetchDescriptor, options, rootState, chartStatePath, dispatch) => {
    // If (testPath, options) is in rootState.timeseries, return.
    // Otherwise await fetch it and dispatch it into rootState.timeseries.

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
      ChartTimeseries.fetch(fetchDescriptor, false,
          rootState.authHeaders, signal, options, dispatch),
      ChartTimeseries.fetch(fetchDescriptor, true,
          rootState.authHeaders, signal, options, dispatch),
    ]);

    dispatch({
      reducer: ChartTimeseries.reducers.request,
      chartStatePath,
      fetchDescriptor,
      options,
      abortController,
      promise,
    });

    return await promise;
  };

  ChartTimeseries.shouldFetch = (testPath, options, rootState) => {
    const existing = rootState.timeseries[testPath];
    return true;
  };

  ChartTimeseries.fetch =
    async (fetchDescriptor, legacy, headers, signal, options, dispatch) => {
      if (location.hostname === 'localhost') {
        const fetchMark = tr.b.Timing.mark('fetch', 'timeseries');
        await tr.b.timeout(500);
        fetchMark.end();
        return {timeseries: cp.dummyTimeseries()};
      }

      let testPath = fetchDescriptor.testPath;
      let columns = ['revision', 'timestamp', 'd_' + fetchDescriptor.statistic];
      if (legacy) {
        testPath = ChartTimeseries.testPath(fetchDescriptor, true);
        columns = ['revision', 'timestamp', 'value'];
      }
      headers = new Headers(headers);
      headers.set('Content-type', 'application/x-www-form-urlencoded');
      options = new URLSearchParams(options);
      const url = `/api/timeseries2/${testPath}?${options}`;
      const fetchMark = tr.b.Timing.mark('fetch', 'timeseries');
      const response = await fetch(url, {headers, signal});
      fetchMark.end();
      const responseJson = await response.json();
      if (responseJson.error) throw new Error(responseJson.error);

      dispatch({
        reducer: ChartTimeseries.reducers.receive,
        testPath,
        options,
        timeseries: responseJson.timeseries,
      });
    };

  ChartTimeseries.layout = (lineDescriptor, timeserieses) => {
    'TODO filter by min/max rev/timestamp';
    'TODO pick statistic';
    'TODO merge using synced iterator';

    const data = [];
    let prevRow;
    for (const hist of timeseries) {
      if (prevRow !== undefined) {
        const datum = {
          row,
          x: row.revision,
          y: row.value,
          icon: '',
        };
        // TODO set datum.icon
        data.push(datum);

        for (const icon of lineDescriptor.icons) {
          if (row.revision === icon.revision) {
            datum.icon = icon.icon;
          }
        }
      }
      prevRow = row;
    }
    return data;
  };

  ChartTimeseries.csvRow = (columns, cells) => {
    const dict = {};
    for (let i = 0; i < columns.length; ++i) {
      dict[columns[i]] = cells[i];
    }
    return dict;
  };

  ChartTimeseries.findHistogram = (histograms, rowDict) => {
    // TODO use binary search
    for (const hist of histograms) {
    }
  };

  cp.ElementBase.register(ChartTimeseries);

  return {
    ChartTimeseries,
  };
});
