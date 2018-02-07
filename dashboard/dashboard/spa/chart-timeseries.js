/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
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

    showPlaceholder_(isLoading, lines) {
      return !isLoading && this._empty(lines);
    }

    onDotMouseOver_(event) {
      this.dispatch('dotMouseOver', this.statePath,
          event.detail.line, event.detail.datum);
    }
  }

  ChartTimeseries.properties = cp.ElementBase.statePathProperties('statePath', {
    isLoading: {type: Boolean},
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
      dispatch(cp.ElementBase.actions.updateObject(statePath, {
        isLoading: true,
        lines: [],
      }));
      // Load each lineDescriptor in parallel.
      await Promise.all(lineDescriptors.map(lineDescriptor =>
        dispatch(ChartTimeseries.actions.loadLineDescriptor(
            statePath, lineDescriptor))));
      dispatch(cp.ElementBase.actions.updateObject(
          statePath, {isLoading: false}));
    },

    loadLineDescriptor: (statePath, lineDescriptor) =>
      async (dispatch, getState) => {
        const fetchDescriptors = ChartTimeseries.createFetchDescriptors(
            lineDescriptor);
        await Promise.all(fetchDescriptors.map(fetchDescriptor =>
          dispatch(cp.TimeseriesCache.load(fetchDescriptor, statePath))));
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
      rows.push({name: 'value', value: datum.y});
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
      dispatch(cp.TimeseriesCache.actions.sweep());
    },
  };

  ChartTimeseries.reducers = {
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
          levelOfDetail: cp.LEVEL_OF_DETAIL.XY,
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
            levelOfDetail: cp.LEVEL_OF_DETAIL.XY,
          };
          fetchDescriptor.testPath = cp.TimeseriesCache.compileTestPath(
              fetchDescriptor);
          fetchDescriptor.cacheKey = fetchDescriptor.testPath.replace('.', '_');
          fetchDescriptors.push(fetchDescriptor);
        }
      }
    }
    return fetchDescriptors;
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
