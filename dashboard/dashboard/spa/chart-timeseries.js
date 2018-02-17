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

  class TimeseriesIterator {
    constructor(lineDescriptor, timeseries) {
      this.lineDescriptor_ = lineDescriptor;
      this.timeseries_ = timeseries;
      this.index_ = this.findStartIndex_();
      // The index of the last Histogram that will be yielded:
      this.endIndex_ = Math.min(
          this.findEndIndex_(), this.timeseries_.length - 1);
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
        xTickRange.addValue(line.data[0].x);
        xTickRange.addValue(line.data[line.data.length - 1].x);
      }

      const round = x => cp.roundDigits(x * 100, 1);

      if (state.xAxis.generateTicks) {
        const ticks = ChartTimeseries.generateTicks(xTickRange).map(text => {
          let x = text;
          if (rawXs) {
            x = tr.b.findLowIndexInSortedArray(rawXs, x => x, text);
          }
          return {
            text,
            xPct: round(xRange.normalize(x)) + '%',
          };
        });
        state = {...state, xAxis: {...state.xAxis, ticks}};
      }

      if (state.yAxis.generateTicks) {
        const yTicksForUnitName = new Map();
        for (const [unitName, range] of yRangeForUnitName) {
          const unit = tr.b.Unit.byName[unitName];
          // Use the extended range to compute yPct, but the unextended range to
          // compute the ticks. TODO store both in yRangesForUnitName
          const trueRange = tr.b.math.Range.fromExplicitRange(
              range.min + (range.range * yExtension),
              range.max - (range.range * yExtension));
          const ticks = ChartTimeseries.generateTicks(trueRange).map(y => {
            return {
              text: unit.format(y),
              yPct: round(1 - range.normalize(y)) + '%',
            };
          });
          yTicksForUnitName.set(unitName, ticks);
        }
        // TODO generate ticks for each line in case state.normalize
        state = {...state, yTicksForUnitName};
        if (yTicksForUnitName.size === 1) {
          const ticks = [...yTicksForUnitName.values()][0];
          state = {...state, yAxis: {...state.yAxis, ticks}};
        } else {
          state = {...state, yAxis: {...state.yAxis, ticks: []}};
        }
      }

      return state;
    }),

    mouseYTicks: cp.ElementBase.statePathReducer((state, action) => {
      // TODO use action.line.yTicks in case state.normalize
      if (state.yTicksForUnitName.size === 1) return state;
      const ticks = action.line ? state.yTicksForUnitName.get(
          action.line.unit.unitName) : [];
      state = {...state, yAxis: {...state.yAxis, ticks}};
      return state;
    }),
  };

  ChartTimeseries.generateTicks = range => {
    let tickDelta = tr.b.math.lesserPower(range.range);
    if ((range.range / tickDelta) < 5) tickDelta /= 10;
    range = tr.b.math.Range.fromExplicitRange(
        (range.min + tickDelta), range.max);
    range = tr.b.math.Range.fromExplicitRange(
        (range.min - (range.min % tickDelta)),
        (range.max - (range.max % tickDelta)));
    tickDelta = range.range / 4;
    const ticks = [];
    for (let x = range.min; x <= range.max; x += tickDelta) {
      ticks.push(x);
    }
    return ticks;
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
