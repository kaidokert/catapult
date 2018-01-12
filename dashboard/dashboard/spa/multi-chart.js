/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  /**
   * @typedef {Object} Point
   * @property {number} x
   * @property {number} y
   */

  /**
   * @typedef {Point} RawDatum
   * @property {!Array.<String>} icons
   */

  /**
   * @typedef {Object} SequenceBase
   * @property {string} name
   * @property {string} color
   * @property {!tr.b.Unit} unit
   */

  /**
   * @typedef {SequenceBase} RawSequence
   * @property {!Array.<!RawDatum>} data
   */

  /**
   * @typedef {Point} NormalizedDatum
   * @property {!Array.<String>} icons
   * @property {!Point} normalized
   */

  /**
   * @typedef {SequenceBase} NormalizedSequence
   * @property {!Array.<!NormalizedDatum>} data
   */

  /**
   * @typedef {Object} AntiBrush
   * @property {number} x
   * @property {number} width
   */

  /**
   * @typedef {Point} Tick
   * @property {string} text
   */

  /**
   * @typedef {Object} Layout
   * @property {!Array.<NormalizedLine>} lines
   * @property {!Array.<number>} brushes
   * @param {Boolean} showYAxisTickLines
   * @param {Boolean} showXAxisTickLines
   * @param {number} graphHeight
   * @param {number} dotRadius
   * @param {string} dotCursor
   * @param {number} brushHandlePx
   * @param {number} yAxisWidth
   * @param {number} xAxisHeight
   * @param {!Array.<!Tick>} yAxisTicks
   * @param {!Array.<!Tick>} xAxisTicks
   */

  PolymerSvgTemplate('multi-chart');
  class MultiChart extends Polymer.GestureEventListeners(cp.ElementBase) {
    static get is() { return 'multi-chart'; }

    static get properties() {
      return cp.ElementBase.statePathProperties('statePath', {
        bars: {type: Array, value: []},
        bottom: {type: Number, value: 100},
        brushHandleTop: {type: Number, value: 50},
        columns: {type: Array, value: []},
        dotCursor: {type: String},
        dotRadius: {type: Number, value: 6},
        graphHeight: {type: Number},
        height: {type: Number, value: 100},
        left: {type: Number, value: 0},
        lines: {type: Array, value: []},
        right: {type: Number, value: 100},
        showXAxisTickLines: {type: Boolean, value: true},
        showYAxisTickLines: {type: Boolean, value: true},
        tooltip: {type: Object},
        top: {type: Number, value: 0},
        width: {type: Number, value: 100},
        xAxisHeight: {type: Number},
        xAxisTicks: {type: Array},
        xBrushes: {type: Array},
        xCursor: {type: Object},
        yAxisLabel: {type: String},
        yAxisTicks: {type: Array},
        yAxisWidth: {type: Number},
        yBrushes: {type: Array},
        yCursor: {type: Object},
      });
    }

    path_(line) {
      return MultiChart.path(line);
    }

    static round(x, decimals) {
      const exp = Math.pow(10, decimals);
      return Math.round(x * exp) / exp;
    }

    /**
     * @param {!Sequence} sequence
     * @return {string}
     */
    static path(line) {
      let path = '';
      for (const datum of line.data) {
        const prefix = path ? ' L' : 'M';
        const x = MultiChart.round(datum.normalized.x, 1);
        const y = MultiChart.round(datum.normalized.y, 1);
        path += prefix + x + ',' + y;
      }
      return path;
    }

    pct_(x) {
      return x + '%';
    }

    antiBrushes_(brushes) {
      return MultiChart.antiBrushes(brushes);
    }

    /**
     * @param {!Array.<number>} brushes
     * @return {!Array.<AntiBrush>}
     */
    static antiBrushes(brushes) {
      if (!brushes || brushes.length === 0) return [];
      if (brushes.length % 2 === 1) throw new Error('Odd number of brushes');
      brushes = brushes.map(brush => brush.normalized).sort((a, b) => a - b);
      let previous = {start: 0, length: undefined};
      const antiBrushes = [previous];
      for (let i = 0; i < brushes.length; i += 2) {
        previous.length = brushes[i] - previous.start;
        if (brushes[i + 1] === 100) return antiBrushes;
        previous = {start: brushes[i + 1], length: undefined};
        antiBrushes.push(previous);
      }
      previous.length = 100 - previous.start;
      return antiBrushes;
    }

    /**
     * This function transforms a high-level description of the components of a
     * complex multi-chart to a lower-level description or "layout".
     *
     * Non-Polymer-Redux Usage:
     *   this.$.line_chart.state = await MultiChart.layout(options);
     * Polymer-Redux usage:
     *   - await layout() in an action creator,
     *   - copy the layout object to your state in a reducer,
     *   - data-bind the path to the layout: <multi-chart state-path=...>
     *
     * @param {!Object} options
     * @param {!Function} options.xAxis for formatting x-axis ticks
     * @param {!Array.<!Sequence>} options.sequences
     * @param {!Array.<!Brush>} options.brushes
     * @param {Boolean} options.showYAxisTickLines
     * @param {Boolean} options.showXAxisTickLines
     * @param {number} options.dotRadius
     * @param {string} options.dotCursor
     * @param {number} options.brushHandlePx
     * @param {Boolean} options.normalize Whether to normalize sequences
     * individually. Default (false) will normalize each set of sequences with
     * the same unit.
     * @return {!Layout}
     */
    static async layout(options) {
      const yRangesByUnit = new Map();
      const xRange = new tr.b.math.Range();
      for (const rawSequence of options.sequences) {
        if (!yRangesByUnit.has(rawSequence.unit)) {
          yRangesByUnit.set(rawSequence.unit, new tr.b.math.Range());
        }
        const yRange = yRangesByUnit.get(rawSequence.unit);
        for (const rawDatum of rawSequence) {
          yRange.addValue(rawDatum.y);
          xRange.addValue(rawDatum.x);
        }
      }

      const sequences = [];
      for (const rawSequence of options.sequences) {
        let yRange = yRangesByUnit.get(rawSequence.unit);
        if (options.normalize) {
          yRange = new tr.b.math.Range();
          for (const rawDatum of rawSequence) {
            yRange.addValue(rawDatum.y);
          }
        }
        sequences.push({
          ...rawSequence,
          data: MultiChart.normalize(rawSequence, xRange, yRange),
        });
      }

      return {
        brushHandlePx: options.brushHandlePx || 0,
        dotCursor: options.dotCursor || '',
        dotRadius: options.dotRadius || 0,
        sequences,
        showXAxisTickLines: options.showXAxisTickLines || false,
        showYAxisTickLines: options.showYAxisTickLines || false,
      };
    }

    static normalize(sequence, xRange, yRange) {
      return sequence.map(datum => {
        return {
          ...datum,
          normalized: {
            x: xRange.normalize(datum.x),
            y: yRange.normalize(datum.y),
          },
        };
      });
    }

    static fixLinesXInPlace(lines) {
      let rawXs = new Set();
      for (const line of lines) {
        for (const datum of line.data) {
          rawXs.add(datum.x);
        }
      }
      rawXs = Array.from(rawXs);
      rawXs.sort((x, y) => x - y);
      for (const line of lines) {
        for (const datum of line.data) {
          datum.rawX = datum.x;
          datum.x = rawXs.indexOf(datum.rawX);
        }
      }
    }

    static normalizeLinesInPlace(lines) {
      const xRange = new tr.b.math.Range();
      for (const line of lines) {
        line.yRange = new tr.b.math.Range();
        for (const datum of line.data) {
          xRange.addValue(datum.x);
          line.yRange.addValue(datum.y);
        }
      }
      for (const line of lines) {
        MultiChart.normalizeLineInPlace(line, xRange);
      }
    }

    static normalizeLineInPlace(line, xRange) {
      for (const datum of line.data) {
        datum.normalized = {
          x: 100 * xRange.normalize(datum.x),
          y: 100 * line.yRange.normalize(datum.y),
        };
      }
    }

    onDotClick_(event) {
      event.cancelBubble = true;
      this.dispatchEvent(new CustomEvent('dot-click', {
        detail: {
          ctrlKey: event.detail.sourceEvent.ctrlKey,
          datum: event.model.datum,
          datumIndex: event.model.datumIndex,
          line: event.model.parentModel.line,
          lineIndex: event.model.parentModel.lineIndex,
        },
      }));
    }

    onMainClick_(event) {
      this.dispatchEvent(new CustomEvent('chart-click'));
    }

    async onDotMouseOver_(event) {
      const chartRect = await cp.measureElement(this);
      const dotRect = await cp.measureElement(event.path[0]);

      this.dispatch('dotMouseOver', this.statePath, chartRect,
          event.model.parentModel.lineIndex, dotRect);
      this.dispatchEvent(new CustomEvent('dot-mouseover', {
        detail: {
          datum: event.model.datum,
          datumIndex: event.model.datumIndex,
          line: event.model.parentModel.line,
          lineIndex: event.model.parentModel.lineIndex,
          sourceEvent: event,
        },
      }));
    }

    tooltipHidden_(tooltip) {
      return !tooltip || !tooltip.isVisible || this._empty(tooltip.rows);
    }

    onDotMouseOut_(event) {
      this.dispatch('dotMouseOut', this.statePath,
          event.model.parentModel.lineIndex);
      this.dispatchEvent(new CustomEvent('dot-mouseout', {
        detail: {
          datum: event.model.datum,
          datumIndex: event.model.datumIndex,
          line: event.model.parentModel.line,
          lineIndex: event.model.parentModel.lineIndex,
          sourceEvent: event,
        },
      }));
    }

    static computeBrush(x, containerRect) {
      const value = tr.b.math.normalize(
          x, containerRect.left, containerRect.right);
      return tr.b.math.clamp(100 * value, 0, 100);
    }

    async onTrackBrushHandle_(event) {
      this.dispatchEvent(new CustomEvent('brush', {
        detail: {
          brushIndex: event.model.brushIndex,
          value: MultiChart.computeBrush(
              event.detail.x, await cp.measureElement(this.$.main)),
          sourceEvent: event,
        },
      }));
    }
  }

  MultiChart.actions = {
    dotMouseOver: (statePath, chartRect, lineIndex, dotRect) =>
      async (dispatch, getState) => {
        dispatch({
          type: MultiChart.reducers.dotMouseOver.typeName,
          statePath,
          chartRect,
          lineIndex,
          dotRect,
        });
      },

    tooltip: (statePath, rows) => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(
          statePath + '.tooltip', {rows}));
    },

    dotMouseOut: (statePath, lineIndex) => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(
          `${statePath}.tooltip`, {isVisible: false}));
      dispatch(cp.ElementBase.actions.updateObject(
          `${statePath}.lines.${lineIndex}`, {strokeWidth: 1}));
    },
  };

  const SQRT2 = Math.sqrt(2);

  MultiChart.reducers = {
    dotMouseOver: cp.ElementBase.statePathReducer((state, action) => {
      const lines = Array.from(state.lines);
      // Set its strokeWidth:2
      const line = lines[action.lineIndex];
      lines.splice(action.lineIndex, 1, {
        ...line,
        strokeWidth: 2,
      });
      if (action.lineIndex !== (lines.length - 1)) {
        // Move action.lineIndex to the end.
        [lines[action.lineIndex], lines[lines.length - 1]] =
          [lines[lines.length - 1], lines[action.lineIndex]];
      }

      // dotRect contains the top and left coordinates of the dot, which is a
      // geometric circle. Offset the tooltip such that its own top left corner
      // is tangent to the bottom-right edge of the dot circle. Do not allow the
      // tooltip to overlap the dot, which can cause flickering via rapid
      // mouseover/mouseout events.
      const offset = state.dotRadius / SQRT2;

      const chartMid = {
        x: (action.chartRect.x + (action.chartRect.width / 2)),
        y: (action.chartRect.y + (action.chartRect.height / 2)),
      };
      let top = '';
      let bottom = '';
      if (action.dotRect.y > chartMid.y) {
        bottom = action.chartRect.bottom - action.dotRect.bottom - offset;
        bottom += 'px';
      } else {
        top = (action.dotRect.top - action.chartRect.top - offset) + 'px';
      }

      let left = '';
      let right = '';
      if (action.dotRect.x > chartMid.x) {
        right = (action.chartRect.right - action.dotRect.left - offset) + 'px';
      } else {
        left = (action.dotRect.right - action.chartRect.left - offset) + 'px';
      }

      return {
        ...state,
        tooltip: {
          bottom,
          color: line.color,
          isVisible: true,
          left,
          right,
          rows: [],  // Embedder must dispatch actions.tooltip
          top,
        },
      };
    }),
  };

  cp.ElementBase.register(MultiChart);

  return {
    MultiChart,
  };
});
