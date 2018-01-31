/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class Descriptor {
    constructor(options) {
      this.testSuites = options.testSuites;
      this.measurement = options.measurement;
      this.bots = options.bots || [];
      this.testCases = options.testCases || [];
    }

    get hash() {
      return 'TODO';
    }

    get testPaths() {
      return [];
    }
  }

  class FastHistogram {
    constructor(diagnostics, statistics) {
      this.diagnostics = diagnostics;
      this.running = statistics;
    }
  }

  class ChartTimeseries extends cp.ElementBase {
    onDotMouseOver_(event) {
      this.dispatch('dotMouseOver', this.statePath, event.detail.datum);
    }
  }

  ChartTimeseries.properties = cp.ElementBase.statePathProperties('statePath', {
    lines: {type: Array},
  });

  ChartTimeseries.newState = () => {
    return {
      abortControllers: {},
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
   *
   * {timeseries: {$descriptorHash: [(FastHistogram|Histogram)]}}
   *
   * pass boolean 'annotations' to /api/timeseries to control whether it returns
   * annotations. This merges /graph_revisions with /graph_json into
   * /api/timeseries.
   *
   * Levels of detail:
   *  * minimap: /api/timeseries?annotations=false
   *    Entries: {diagnostics, running: RunningStatistics} containing only the
   *    needed statistics and diagnostics (point id, timestamp, commit positions
   *    or whatever).
   *  * chart-section.chartLayout: /api/timeseries?annotations=true
   *    Entries are real Histogram objects with RunningStatistics and some
   *    diagnostics, but no samples.
   *  * Histogram: /api/histograms
   *    Entries have samples and all diagnostics.
   *
   * Memory control triggers:
   *  * load()
   *  * ChartTimeseries.detached
   *
   * Memory control:
   * Downgrade full Histograms to FastHistograms.
   * Prune timeseries.
   *
   * Fetch everything via service worker.
   */

  ChartTimeseries.actions = {
    load: (statePath, descriptors) => async (dispatch, getState) => {
      dispatch({
        type: ChartTimeseries.reducers.clear_.typeName,
        statePath,
      });
      for (const descriptor of descriptors) {
        dispatch(ChartTimeseries.actions.loadSingle_(statePath, descriptor));
      }
    },

    loadSingle_: (statePath, descriptor) => async (dispatch, getState) => {
      descriptor.hash = ChartTimeseries.descriptorHash(descriptor);

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

    dotMouseOver: (statePath, datum) => async (dispatch, getState) => {
      dispatch(cp.ChartBase.actions.tooltip(statePath, [
        {name: 'value', value: datum.value},
        {name: 'chromium', value: datum.chromiumCommitPositions.join('-')},
      ]));
    },
  };

  ChartTimeseries.reducers = {
    clear_: cp.ElementBase.statePathReducer((state, action) => {
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

  function stringHash(str) {
    let hash = 0;
    for (let i = 0; i < str.length; ++i) {
      hash = (hash + 37 * hash + 11 * str.charCodeAt(i)) % 0xFFFFFFFF;
    }
    return hash;
  }

  ChartTimeseries.descriptorHash = descriptor => stringHash(JSON.stringify({
    testSuites: descriptor.testSuites,
    measurements: descriptor.measurements,
    bots: descriptor.bots,
    testCases: descriptor.testCases,
    statistic: descriptor.statistic,
  }));

  cp.ElementBase.register(ChartTimeseries);

  return {
    ChartTimeseries,
  };
});
