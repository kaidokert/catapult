/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  function getX(hist) {
    // TODO revisionTimestamp
    const commitPos = hist.diagnostics.get(
        tr.v.d.RESERVED_NAMES.CHROMIUM_COMMIT_POSITIONS);
    if (commitPos) {
      return tr.b.math.Statistics.min(commitPos);
    }
    return getTimestamp(hist).getTime();
  }

  function getTimestamp(hist) {
    const timestamp = hist.diagnostics.get(
        tr.v.d.RESERVED_NAMES.UPLOAD_TIMESTAMP);
    return timestamp.minDate;
  }

  // TODO compute this based on how multiple timeseries x coordinates line up
  const MAX_POINTS = 500;

  class TimeseriesIterator {
    constructor(lineDescriptor, timeseries) {
      this.lineDescriptor_ = lineDescriptor;
      this.timeseries_ = timeseries;
      this.index_ = this.findStartIndex_();
      // The index of the last Histogram that will be yielded:
      this.endIndex_ = Math.min(
          this.findEndIndex_(), this.timeseries_.length - 1);
      this.indexDelta_ = Math.max(
          1, (this.endIndex_ - this.index_) / MAX_POINTS);
    }

    findStartIndex_() {
      if (this.lineDescriptor_.minTimestampMs) {
        return tr.b.findLowIndexInSortedArray(
            this.timeseries_, getTimestamp,
            this.lineDescriptor_.minTimestampMs);
      }
      if (this.lineDescriptor_.minRevision) {
        return tr.b.findLowIndexInSortedArray(
            this.timeseries_, getX, this.lineDescriptor_.minRevision);
      }
      return 0;
    }

    findEndIndex_() {
      if (this.lineDescriptor_.maxTimestampMs) {
        return tr.b.findLowIndexInSortedArray(
            this.timeseries_, getTimestamp,
            this.lineDescriptor_.maxTimestampMs);
      }
      if (this.lineDescriptor_.maxRevision) {
        return tr.b.findLowIndexInSortedArray(
            this.timeseries_, getX, this.lineDescriptor_.maxRevision);
      }
      return this.timeseries_.length - 1;
    }

    get current() {
      return this.timeseries_[Math.min(this.roundIndex_, this.endIndex_)];
    }

    get roundIndex_() {
      return Math.round(this.index_);
    }

    get done() {
      return this.roundIndex_ > this.endIndex_;
    }

    next() {
      this.index_ += this.indexDelta_;
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
        const merged = new cp.FastHistogram();
        let minX = Infinity;
        for (const iterator of this.iterators_) {
          merged.addHistogram(iterator.current);
          if (!iterator.done) minX = Math.min(minX, getX(iterator.current));
        }
        yield [minX, merged];

        // Increment all iterators whose X coordinate is minX.
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
      this.dispatch('dotMouseOver_', this.statePath,
          event.detail.line, event.detail.datum);
    }

    onDotMouseOut_(event) {
      this.dispatch('dotMouseOut_', this.statePath);
    }
  }

  ChartTimeseries.properties = cp.ElementBase.statePathProperties('statePath', {
    isLoading: {type: Boolean},
    lines: {type: Array},
  });

  ChartTimeseries.newState = () => {
    const state = cp.ChartBase.newState();
    return {
      ...state,
      isLoading: false,
      xAxis: {
        ...state.xAxis,
        generateTicks: true,
      },
      yAxis: {
        ...state.yAxis,
        generateTicks: true,
      },
    };
  };

  function arraySetEqual(a, b) {
    if (a.length !== b.length) return false;
    for (const e of a) {
      if (!b.includes(e)) return false;
    }
    return true;
  }

  ChartTimeseries.lineDescriptorEqual = (a, b) => {
    if (!arraySetEqual(a.testSuites, b.testSuites)) return false;
    if (!arraySetEqual(a.bots, b.bots)) return false;
    if (!arraySetEqual(a.testCases, b.testCases)) return false;
    if (a.measurement !== b.measurement) return false;
    if (a.statistic !== b.statistic) return false;
    if (a.buildType !== b.buildType) return false;
    if (a.minTimestampMs !== b.minTimestampMs) return false;
    if (a.maxTimestampMs !== b.maxTimestampMs) return false;
    if (a.minRevision !== b.minRevision) return false;
    if (a.maxRevision !== b.maxRevision) return false;
    return true;
  };

  ChartTimeseries.actions = {
    prefetch: (statePath, lineDescriptors) => async (dispatch, getState) => {
      await Promise.all(lineDescriptors.map(lineDescriptor =>
        dispatch(ChartTimeseries.actions.fetchLineDescriptor_(
            statePath, lineDescriptor))));
    },

    load: (statePath, lineDescriptors, opt_options) =>
      async (dispatch, getState) => {
        const options = opt_options || {};
        const fixedXAxis = options.fixedXAxis || false;
        const normalize = options.normalize || false;
        const center = options.center || false;
        const zeroYAxis = options.zeroYAxis || false;
        dispatch(cp.ElementBase.actions.updateObject(statePath, {
          fixedXAxis,
          isLoading: true,
          lineDescriptors,
          lines: [],
          normalize,
          center,
          zeroYAxis,
        }));

        // Load each lineDescriptor in parallel.
        await Promise.all(lineDescriptors.map(lineDescriptor =>
          dispatch(ChartTimeseries.actions.loadLineDescriptor_(
              statePath, lineDescriptor))));
        dispatch(cp.ElementBase.actions.updateObject(
            statePath, {isLoading: false}));
      },

    fetchLineDescriptor_: (statePath, lineDescriptor) =>
      async (dispatch, getState) => {
        const fetchDescriptors = ChartTimeseries.createFetchDescriptors(
            lineDescriptor);
        const promises = fetchDescriptors.map(
            fetchDescriptor => dispatch(cp.TimeseriesCache.actions.load(
                fetchDescriptor, statePath)));
        const timeserieses = [];
        for (const promise of promises) {
          try {
            timeserieses.push(await promise);
          } catch (err) {
          }
        }
        return timeserieses;
      },

    loadLineDescriptor_: (statePath, lineDescriptor) =>
      async (dispatch, getState) => {
        const timeserieses = await dispatch(
            ChartTimeseries.actions.fetchLineDescriptor_(
                statePath, lineDescriptor));
        if (timeserieses.length === 0) return;
        await cp.ElementBase.afterRender();  // TODO remove
        const state = Polymer.Path.get(getState(), statePath);
        if (!state) return;
        if (0 === state.lineDescriptors.filter(other =>
            ChartTimeseries.lineDescriptorEqual(
                lineDescriptor, other)).length) {
          return;
        }
        dispatch({
          type: ChartTimeseries.reducers.layout.typeName,
          statePath,
          lineDescriptor,
          timeserieses,
        });
      },

    dotMouseOver_: (statePath, line, datum) => async (dispatch, getState) => {
      dispatch({
        type: ChartTimeseries.reducers.mouseYTicks.typeName,
        statePath,
        line,
      });
      const rows = [];
      rows.push({name: 'value', value: line.unit.format(datum.y)});
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

    dotMouseOut_: statePath => async (dispatch, getState) => {
      dispatch({
        type: ChartTimeseries.reducers.mouseYTicks.typeName,
        statePath,
      });
    },

    disconnected: statePath => async (dispatch, getState) => {
      dispatch(cp.TimeseriesCache.actions.sweep());
    },
  };

  ChartTimeseries.assignColors = lines => {
    const isTestLine = line => line.descriptor.buildType !== 'reference';
    const testLines = lines.filter(isTestLine);
    const colors = tr.b.generateFixedColorScheme(
        testLines.length, {hueOffset: 0.64});
    const colorByDescriptor = new Map();
    for (const line of testLines) {
      const color = colors.shift();
      colorByDescriptor.set(ChartTimeseries.stringifyDescriptor(
        {...line.descriptor, buildType: undefined}), color);
      line.color = color.toString();
    }
    for (const line of lines) {
      if (isTestLine(line)) continue;
      const color = colorByDescriptor.get(ChartTimeseries.stringifyDescriptor(
          {...line.descriptor, buildType: undefined}));
      if (color) {
        const hsl = color.toHSL();
        line.color = tr.b.Color.fromHSL({
          h: hsl.h,
          s: 1,
          l: 0.9,
        }).toString();
      } else {
        line.color = 'white';
      }
    }
  };

  ChartTimeseries.reducers = {
    layout: cp.ElementBase.statePathReducer((state, action) => {
      // Transform action.timeserieses to build a line to append to state.lines.
      state = ChartTimeseries.cloneLines(state);
      const timeserieses = action.timeserieses.map(ts => ts.data);
      state.lines.push({
        descriptor: action.lineDescriptor,
        unit: action.timeserieses[0].unit,
        data: ChartTimeseries.mergeTimeserieses(
            action.lineDescriptor, timeserieses),
        strokeWidth: 1,
      });
      ChartTimeseries.assignColors(state.lines);
      return cp.ChartBase.layoutLinesInPlace(state);
    }),

    mouseYTicks: cp.ElementBase.statePathReducer((state, action) => {
      if (!state.yAxis.generateTicks) return state;
      if (!(state.normalize || state.center) &&
          (state.yAxis.ticksForUnitName.size === 1)) {
        return state;
      }
      let ticks = [];
      if (action.line) {
        if (state.normalize || state.center) {
          ticks = action.line.ticks;
        } else {
          ticks = state.yAxis.ticksForUnitName.get(
              action.line.unit.unitName);
        }
      }
      return {...state, yAxis: {...state.yAxis, ticks}};
    }),
  };

  ChartTimeseries.cloneLines = state => {
    // Clone the line object so we can reassign its color later.
    // Clone the data so we can re-normalize it later along with the new
    // line.
    return {...state, lines: state.lines.map(line => {
      return {...line, data: line.data.map(datum => {
        return {...datum};
      })};
    })};
  };

  // Strip out min/maxRevision/Timestamp and ensure a consistent key order.
  ChartTimeseries.stringifyDescriptor = lineDescriptor => JSON.stringify([
    lineDescriptor.testSuites,
    lineDescriptor.measurement,
    lineDescriptor.bots,
    lineDescriptor.testCases,
    lineDescriptor.statistic,
    lineDescriptor.buildType,
  ]);

  ChartTimeseries.createFetchDescriptors = lineDescriptor => {
    let testCases = lineDescriptor.testCases;
    if (testCases.length === 0) testCases = [undefined];
    const fetchDescriptors = [];
    for (const testSuite of lineDescriptor.testSuites) {
      for (const bot of lineDescriptor.bots) {
        for (const testCase of testCases) {
          fetchDescriptors.push({
            testSuite,
            bot,
            measurement: lineDescriptor.measurement,
            testCase,
            statistic: lineDescriptor.statistic,
            buildType: lineDescriptor.buildType,
            levelOfDetail: cp.LEVEL_OF_DETAIL.XY,
          });
        }
      }
    }
    return fetchDescriptors;
  };

  ChartTimeseries.mergeTimeserieses = (lineDescriptor, timeserieses) => {
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

    const lineData = [];
    const iter = new MultiTimeseriesIterator(lineDescriptor, timeserieses);
    for (const [x, hist] of iter) {
      lineData.push({
        hist,
        x,
        y: hist.running[lineDescriptor.statistic],
        icon: getIcon(hist),
      });
    }
    lineData.sort((a, b) => a.x - b.x);
    return lineData;
  };

  cp.ElementBase.register(ChartTimeseries);

  return {
    ChartTimeseries,
    MultiTimeseriesIterator,
  };
});
