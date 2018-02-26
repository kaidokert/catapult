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
    return tr.b.math.Statistics.min(commitPos);
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
      this.dispatch('dotMouseOver', this.statePath,
          event.detail.line, event.detail.datum);
    }

    onDotMouseOut_(event) {
      this.dispatch('dotMouseOut', this.statePath);
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
    load: (statePath, lineDescriptors, opt_options) =>
      async (dispatch, getState) => {
        const options = opt_options || {};
        const fixedXAxis = options.fixedXAxis || false;
        const normalize = options.normalize || false;
        const zeroYAxis = options.zeroYAxis || false;
        dispatch(cp.ElementBase.actions.updateObject(statePath, {
          fixedXAxis,
          isLoading: true,
          lineDescriptors,
          lines: [],
          normalize,
          zeroYAxis,
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

    dotMouseOver: (statePath, line, datum) => async (dispatch, getState) => {
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

    dotMouseOut: statePath => async (dispatch, getState) => {
      dispatch({
        type: ChartTimeseries.reducers.mouseYTicks.typeName,
        statePath,
      });
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

      let rawXs;
      if (state.fixedXAxis) {
        rawXs = cp.ChartBase.fixLinesXInPlace(lines);
      }

      // Extend xRange by 1% in both directions in order to make it easier to
      // click on the endpoint dots. Without this, only half of the endpoint
      // dots would be drawn and clickable. Chart width can vary widely, but
      // 600px is is a good enough approximation.
      const xExtension = state.dotRadius ? 0.01 : 0;

      // Extend yRange by 3.75% in both directions in order to make it easier to
      // click on extreme dots. Without this, only half of the extreme dots
      // would be drawn and clickable. The main chart is 200
      // px tall and has dots with radius=6px, which is 3% of 200. This will
      // also reduce clipping yAxis.ticks, which are 15px tall and so can extend
      // 7.5px (3.75% of 200px) above/below extreme points if they happen to be
      // a round number.
      const yExtension = state.dotRadius ? 0.0375 : 0;

      const {xRange, yRangeForUnitName} = cp.ChartBase.normalizeLinesInPlace(
          lines, {
            normalize: state.normalize,
            zeroYAxis: state.zeroYAxis,
            xExtension,
            yExtension,
          });
      state = {...state, lines};

      const xTickRange = new tr.b.math.Range();
      for (const line of lines) {
        if (line.data.length === 0) continue;
        xTickRange.addValue(line.data[0].x);
        xTickRange.addValue(line.data[line.data.length - 1].x);
      }

      if (state.xAxis.generateTicks) {
        const ticks = ChartTimeseries.generateTicks(xTickRange).map(text => {
          let x = text;
          if (rawXs) {
            x = tr.b.findLowIndexInSortedArray(rawXs, x => x, text);
          }
          return {
            text,
            xPct: cp.roundDigits(xRange.normalize(x) * 100, 1) + '%',
          };
        });
        state = {...state, xAxis: {...state.xAxis, ticks}};
      }

      if (state.yAxis.generateTicks) {
        let yAxis = state.yAxis;
        let ticks = [];
        if (state.normalize) {
          for (const line of lines) {
            line.ticks = ChartTimeseries.generateYTicks(
                line.yRange, line.unit, yExtension);
          }
          if (lines.length === 1) {
            ticks = lines[0].ticks;
          }
        } else {
          const ticksForUnitName = new Map();
          for (const [unitName, range] of yRangeForUnitName) {
            const unit = tr.b.Unit.byName[unitName];
            const ticks = ChartTimeseries.generateYTicks(
                range, unit, yExtension);
            ticksForUnitName.set(unitName, ticks);
          }
          yAxis = {...yAxis, ticksForUnitName};
          if (ticksForUnitName.size === 1) {
            ticks = [...ticksForUnitName.values()][0];
          }
        }
        yAxis = {...yAxis, ticks};
        state = {...state, yAxis};
      }

      return state;
    }),

    mouseYTicks: cp.ElementBase.statePathReducer((state, action) => {
      if (!state.yAxis.generateTicks) return state;
      if (!state.normalize && (state.yAxis.ticksForUnitName.size === 1)) {
        return state;
      }
      let ticks = [];
      if (action.line) {
        if (state.normalize) {
          ticks = action.line.ticks;
        } else {
          ticks = state.yAxis.ticksForUnitName.get(
              action.line.unit.unitName);
        }
      }
      return {...state, yAxis: {...state.yAxis, ticks}};
    }),
  };

  ChartTimeseries.generateYTicks = (displayRange, unit, yExtension) => {
    // Use the extended range to compute yPct, but the unextended range
    // to compute the ticks. TODO store both in normalizeLinesInPlace
    const dataRange = tr.b.math.Range.fromExplicitRange(
        displayRange.min + (displayRange.range * yExtension),
        displayRange.max - (displayRange.range * yExtension));
    return ChartTimeseries.generateTicks(dataRange).map(y => {
      return {
        text: unit.format(y),
        yPct: cp.roundDigits(100 * (1 - displayRange.normalize(y)), 1) + '%',
      };
    });
  };

  ChartTimeseries.generateTicks = range => {
    let tickDelta = tr.b.math.lesserPower(range.range);
    if ((range.range / tickDelta) < 5) tickDelta /= 10;
    range = tr.b.math.Range.fromExplicitRange(
        (range.min + tickDelta), range.max);
    range = tr.b.math.Range.fromExplicitRange(
        (range.min - (range.min % tickDelta)),
        (range.max - (range.max % tickDelta)));
    tickDelta = range.range / 5;
    const ticks = [];
    for (let x = range.min; x <= range.max; x += tickDelta) {
      ticks.push(x);
    }
    return ticks;
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
    for (const [x, hist] of iter) {
      lineData.push({
        hist,
        x,
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
