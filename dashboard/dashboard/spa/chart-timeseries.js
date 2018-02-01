/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
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

  class Descriptor {
    constructor(options) {
      this.levelOfDetail = options.levelOfDetail;

      this.testSuites = options.testSuites || [];
      if (options.testSuite) this.testSuites.push(options.testSuite);

      this.measurement = options.measurement;

      this.bots = options.bots || [];
      if (options.bot) this.bots.push(options.bot);

      this.testCases = options.testCases || [];
      if (options.testCase) this.testCases.push(options.testCase);

      this.statistics = options.statistics || [];
      if (options.statistic) this.statistics.push(options.statistic);
      if (this.statistics.length === 0) this.statistics.push('avg');

      this.minRev = options.minRev || undefined;
      this.maxRev = options.maxRev || undefined;
      this.minTimestamp = options.minTimestamp || undefined;
      this.maxTimestamp = options.maxTimestamp || undefined;
    }

    get requests() {
      const requests = [];
      for (const testSuite of this.testSuites) {
        for (const bot of this.bots) {
          for (const testCase of this.testCases) {
            for (const statistic of this.statistics) {
              requests.push({
                testPath: this.testPath(
                    testSuite, this.measurement, bot, testCase, statistic),
                min_timestamp: this.minTimestamp,
                columns: this.columns,
              });
              requests.push({
                testPath: this.testPath(
                    testSuite, this.measurement, bot, testCase, ''),
                min_timestamp: this.minTimestamp,
                columns: this.columns,
              });
            }
          }
        }
      }
      return requests;
    }

    static testPath(testSuite, measurement, bot, testCase, statistic) {
    }
  }

  // Supports XY and ANNOTATIONS levels of detail.
  class FastHistogram {
    constructor(diagnostics, statistics) {
      this.diagnostics = diagnostics;
      this.running = statistics;
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

  /*
   * timeseries cache on root state because a timeseries could be displayed in
   * both alerts-section and chart-section or multiple chart-sections.
   * Also store full real Histograms in timeseries, see pivot-cell.
   *
   * {
   *   timeseries: {
   *     testpath: {
   *       references: ["statePath"],
   *       data: [(FastHistogram|Histogram)],
   *       ranges: {
   *         xy: [
   *           {
   *             minRev, maxRev, minTimestamp, maxTimestamp,
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
   * Memory control strategies:
   * Prune timeseries that are no longer in use.
   * Downgrade full Histograms to FastHistograms.
   *
   * Memory control triggers:
   *  * actions.load
   *  * actions.disconnected
   *
   * service-worker.js caches minimaps and individual histograms.
   * TODO cache chart-section.chartLayout requests in service-worker using
   * revision range logic.
   */

  ChartTimeseries.actions = {
    load: (statePath, descriptors) => async (dispatch, getState) => {
      dispatch({
        type: ChartTimeseries.reducers.clear.typeName,
        statePath,
      });
      for (const descriptor of descriptors) {
        dispatch(ChartTimeseries.actions.loadDescriptor(statePath, descriptor));
      }
    },

    loadDescriptor: (statePath, descriptor) => async (dispatch, getState) => {
      let controller;
      let signal;
      if (window.AbortController) {
        controller = new AbortController();
        signal = controller.signal;
      }

      dispatch({
        type: ChartTimeseries.reducers.requestRows_.typeName,
        statePath,
        descriptor,
        controller,
      });

      const rootState = getState();

      let timeserieses;
      try {
        timeserieses = await ChartTimeseries.fetch(
            rootState.authHeaders, signal, descriptor);
      } catch (error) {
        // eslint-disable-next-line no-console
        console.error('Error fetching timeseries', err);
      }

      dispatch({
        type: ChartTimeseries.reducers.receiveTimeserieses.typeName,
        statePath,
        descriptor,
        timeserieses,
      });
    },

    loadTestPath: (statePath, testPath) => async (dispatch, getState) => {
    },

    dotMouseOver: (statePath, datum) => async (dispatch, getState) => {
      dispatch(cp.ChartBase.actions.tooltip(statePath, [
        {name: 'value', value: datum.value},
        {name: 'chromium', value: datum.chromiumCommitPositions.join('-')},
      ]));
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
      // TODO cancel requests and free memory
    },

    clear: cp.ElementBase.statePathReducer((state, action) => {
      for (const controller of Object.values(state.abortControllers)) {
        // TODO use a separate cache layer and don't abort requests that will
        // just be re-started.
        controller.abort();
      }

      return {
        ...state,
        abortControllers: {},
        lines: [],
      };
    }),

    requestRows_: cp.ElementBase.statePathReducer((state, action) => {
      const abortControllers = {...state.abortControllers};
      if (action.controller) {
        abortControllers[action.descriptor.hash] = action.controller;
      }
      return {
        ...state,
        isLoading: true,
        abortControllers,
      };
    }),

    receiveTimeserieses: cp.ElementBase.statePathReducer((state, action) => {
      const lines = [];
      for (const line of state.lines) {
        // Don't add multiple lines for the same descriptor.
        if (line.descriptor.hash === action.descriptor.hash) continue;

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

      if (action.timeserieses) {
        lines.push({
          chartParameters: action.descriptor,
          descriptor: action.descriptor,
          data: ChartTimeseries.transformTimeserieses(
              action.timeserieses, action.descriptor),
          strokeWidth: 1,
        });
      }

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

      const abortControllers = {...state.abortControllers};
      delete abortControllers[action.descriptor.hash];

      return {
        ...state,
        isLoading: Object.keys(abortControllers).length > 0,
        abortControllers,
        lines,
      };
    }),
  };

  ChartTimeseries.fetch = async (headers, signal, descriptor) => {
    if (!descriptor.testPaths) {
      descriptor.testPaths = ChartTimeseries.testPaths(descriptor);
    }
    return await Promise.all(descriptor.testPaths.map(testPath =>
      ChartTimeseries.fetchSingle(headers, signal, testPath)));
  };

  ChartTimeseries.testPaths = descriptor => {
    const testPaths = [];
    for (const testSuite of descriptor.testSuites) {
      for (const bots of descriptor.bots) {
        for (const testCase of descriptor.testCases) {
          testPaths.push(ChartTimeseries.testPath(
              testSuite,
              descriptor.measurement,
              bot,
              testCase,
              descriptor.statistic));
        }
      }
    }
    return testPaths;
  };

  ChartTimeseries.testPath =
    (testSuite, measurement, bot, testCase, statistic) => {
      const botParts = bot.split(':');
      const master = botParts[0];
      const components = [master];
      return components.join('/');
    };

  ChartTimeseries.fetchSingle = async (headers, signal, testPath) => {
    if (location.hostname === 'localhost') {
      const fetchMark = tr.b.Timing.mark('fetch', 'timeseries');
      await tr.b.timeout(500);
      fetchMark.end();
      return {timeseries: cp.dummyTimeseries()};
    }

    headers = new Headers(headers);
    headers.set('Content-type', 'application/x-www-form-urlencoded');
    const body = new URLSearchParams();
    const fetchMark = tr.b.Timing.mark('fetch', 'timeseries');
    const response = await fetch('/api/timeseries/' + testPath, {
      method: 'POST',
      headers,
      body,
      signal,
    });
    fetchMark.end();
    const responseJson = await response.json();
    if (responseJson.error) throw new Error(responseJson.error);
    return responseJson.timeseries;
  };

  ChartTimeseries.readCSV = csv => {
    const dicts = [];
    const columns = csv[0];
    for (let i = 1; i < csv.length; ++i) {
      const dict = {};
      for (let j = 0; j < columns.length; ++j) {
        dict[columns[j]] = csv[i][j];
      }
      dicts.push(dict);
    }
    return dicts;
  };

  ChartTimeseries.transformTimeserieses = (timeserieses, descriptor) => {
    timeserieses = timeserieses.map(ChartTimeseries.readCSV);
    if (timeserieses.length > 1) {
      cp.todo('reduce timeserieses');
    }
    return ChartTimeseries.transformRows(timeserieses[0], descriptor);
  };

  ChartTimeseries.transformRows = (rows, descriptor) => {
    const data = [];
    let prevRow;
    for (const row of rows) {
      if (prevRow !== undefined) {
        const datum = {
          chromiumCommitPositions: [prevRow.revision + 1, row.revision],
          value: descriptor.baseUnit.format(row.value),
          x: row.revision,
          y: row.value,
          icon: '',
        };
        data.push(datum);

        // TODO derive this information from the backend instead of sneaking it
        // in through the descriptor.
        for (const icon of descriptor.icons) {
          if (row.revision === icon.revision) {
            datum.icon = icon.icon;
          }
        }
      }
      prevRow = row;
    }
    return data;
  };

  cp.ElementBase.register(ChartTimeseries);

  return {
    ChartTimeseries,
  };
});
/*
r_android_base_version: {url: "https://googleplex-android.googlesource.com/platform/frameworks/base/+/{{R1}}..{{R2}}", name: "Android Base Version"}
r_arc: {url: "https://chrome-internal.googlesource.com/arc/arc/+log/{{R1}}..{{R2}}", name: "ARC Revision"}
r_chrome_version: {url: "https://omahaproxy.appspot.com/changelog?old_version={{R1}}&new_version={{R2}}", name: "Chrome Version"}
r_chromium: {url: "https://chromium.googlesource.com/chromium/src/+log/{{R1}}..{{R2}}", name: "Chromium Git Hash"}
r_chromium_commit_pos: {url: "http://test-results.appspot.com/revision_range?start={{R1}}&end={{R2}}", name: "Chromium Commit Position"}
r_chromium_git: {url: "https://chromium.googlesource.com/chromium/src/+log/{{R1}}..{{R2}}", name: "Chromium Git Hash"}
r_chromium_rev: {url: "https://chromium.googlesource.com/chromium/src/+log/{{R1}}..{{R2}}", name: "Chromium Git Hash"}
r_clang_rev: {url: "http://llvm.org/viewvc/llvm-project?view=revision&revision={{R2}}#start={{R1}}", name: "Clang Revision"}
r_clank: {url: "https://chrome-internal.googlesource.com/clank/internal/apps/+log/{{R1}}..{{R2}}", name: "Clank Apps Git Hash"}
r_commit_pos: {url: "http://test-results.appspot.com/revision_range?start={{R1}}&end={{R2}}&n={{n}}", name: "Chromium Commit Position"}
r_cros_version: {url: "https://crosland.corp.google.com/log/{{R1_trim}}..{{R2_trim}}", name: "ChromeOS Version"}
r_deps: {url: "https://chrome-internal.googlesource.com/clank/internal/deps/+log/{{R1}}..{{R2}}", name: "Clank Deps Git Hash"}
r_infra_infra_git: {url: "https://chromium.googlesource.com/infra/infra/+log/{{R1}}..{{R2}}", name: "Infra/Infra Git Hash"}
r_lbshell: {url: "https://lbshell-internal.googlesource.com/lbshell/+/{{R1}}..{{R2}}", name: "Leanback Shell Revision"}
r_mojo: {url: "https://chromium.googlesource.com/external/mojo/+log/{{R1}}..{{R2}}", name: "Mojo Git Hash"}
r_v8_git: {url: "https://chromium.googlesource.com/v8/v8/+log/{{R1}}..{{R2}}", name: "V8 Git Hash"}
r_v8_js_comp_milestone: {url: "", name: "Milestone"}
r_v8_rev: {url: "https://chromium.googlesource.com/v8/v8/+log/{{R1}}..{{R2}}", name: "V8 Commit Position"}
r_v8_revision: {url: "https://chromium.googlesource.com/v8/v8/+log/{{R1}}..{{R2}}", name: "V8 Git Hash"}
r_webrtc_git: {url: "https://webrtc.googlesource.com/src/+log/{{R1}}..{{R2}}", name: "WebRTC Git Hash"}
r_webrtc_subtree_git: {url: "https://webrtc.googlesource.com/src/webrtc/+log/{{R1}}..{{R2}}", name: "WebRTC Git Hash"}
*/
