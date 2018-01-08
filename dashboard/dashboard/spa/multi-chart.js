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

    /**
     * @param {!Sequence} sequence
     * @return {string}
     */
    static path(line) {
      let path = '';
      for (const datum of line.data) {
        const prefix = path ? ' L' : 'M';
        path += `${prefix}${datum.x},${datum.y}`;
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

    onDotMouseOver_(event) {
      this.dispatchEvent(new CustomEvent('dot-mouseover', {
        detail: {
          datum: event.model.datum,
          datumIndex: event.model.datumIndex,
          line: event.model.parentModel.line,
          lineIndex: event.model.parentModel.lineIndex,
        },
      }));
    }

    onDotMouseOut_(event) {
      this.dispatchEvent(new CustomEvent('dot-mouseout', {
        detail: {
          datum: event.model.datum,
          datumIndex: event.model.datumIndex,
          line: event.model.parentModel.line,
          lineIndex: event.model.parentModel.lineIndex,
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
        },
      }));
    }
  }

  MultiChart.NEW_STATE = {
  };

  cp.ElementBase.register(MultiChart);

  return {
    MultiChart,
  };
});
