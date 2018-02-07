/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  function getX(hist) {
    const commitPos = hist.diagnostics.get(
        tr.v.d.RESERVED_NAMES.CHROMIUM_COMMIT_POSITIONS);
    // TODO support timeseries that don't have r_commit_pos
    return tr.b.math.Statistics.mean(commitPos);
  }

  class TimeseriesIterator {
    constructor(lineDescriptor, timeseries) {
      this.lineDescriptor_ = lineDescriptor;
      this.timeseries_ = timeseries;
      this.index_ = this.findStartIndex_();
      // The index of the last Histogram that will be yielded:
      this.endIndex_ = this.findEndIndex_();
    }

    findStartIndex_() {
      // TODO bsearch lineDescriptor.minRev
      return 0;
    }

    findEndIndex_() {
      // TODO bsearch lineDescriptor.maxRev
      return this.timeseries_.length - 1;
    }

    get current() {
      return this.timeseries_[Math.min(this.index_, this.endIndex_)];
    }

    get done() {
      return this.index_ > this.endIndex_;
    }

    next() {
      ++this.index_;
    }
  }

  class MultiTimeseriesIterator {
    constructor(lineDescriptor, timeserieses) {
      this.iterators_ = timeserieses.map(timeseries => new TimeseriesIterator(
        lineDescriptor, timeseries));
    }

    get allDone_() {
      for (const iterator of this.iterators_) {
        if (!iterator.done) return false;
      }
      return true;
    }

    * [Symbol.iterator]() {
      while (!this.allDone_) {
        let merged = this.iterators_[0].current;
        let minX = getX(merged);
        if (this.iterators_.length > 1) {
          merged = merged.clone();
          for (const iterator of this.iterators_) {
            merged.addHistogram(iterator.current);
            minX = Math.min(minX, getX(iterator.current));
          }
        }
        yield merged;

        for (const iterator of this.iterators_) {
          if (!iterator.done && getX(iterator.current) === minX) {
            iterator.next();
          }
        }
      }
    }
  }

  class ChartTimeseries extends cp.ElementBase {
    disconnectedCallback() {
      this.dispatch('disconnected', this.statePath);
    }

    showPlaceholder(isLoading, lines) {
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
        const timeserieses = await Promise.all(fetchDescriptors.map(
            fetchDescriptor => dispatch(cp.TimeseriesCache.actions.load(
                fetchDescriptor, statePath))));
        await cp.ElementBase.afterRender();  // TODO remove
        dispatch({
          type: ChartTimeseries.reducers.layout.typeName,
          statePath,
          lineDescriptor,
          timeserieses,
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
    layout: cp.ElementBase.statePathReducer((state, action) => {
      // Transform action.timeserieses to build a line to append to state.lines.

      const lines = [];
      for (const line of state.lines) {
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

      const timeserieses = action.timeserieses.map(ts => ts.data);
      lines.push({
        descriptor: action.lineDescriptor,
        unit: action.timeserieses[0].unit,
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

      return {...state, lines};
    }),
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
    function getIcon(hist) {
      if (hist.alert) return hist.alert.improvement ? 'thumb-up' : 'error';
      if (!lineDescriptor.icons) return '';
      // TODO remove lineDescriptor.icons
      const revisions = [...hist.diagnostics.get(
          tr.v.d.RESERVED_NAMES.CHROMIUM_COMMIT_POSITIONS)];
      for (const icon of lineDescriptor.icons) {
        if (revisions.includes(icon.revision)) return icon.icon;
      }
      return '';
    }

    const iter = new MultiTimeseriesIterator(lineDescriptor, timeserieses);
    const lineData = [];
    for (const hist of iter) {
      lineData.push({
        hist,
        x: getX(hist),
        y: hist.running[lineDescriptor.statistic],
        icon: getIcon(hist),
      });
    }
    return lineData;
  };

  cp.ElementBase.register(ChartTimeseries);

  return {
    ChartTimeseries,
    MultiTimeseriesIterator,
  };
});
