/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  PolymerSvgTemplate('line-chart');
  class LineChart extends Polymer.Element {
    static get is() { return 'line-chart'; }

    static get properties() {
      return {
        layout: {
          type: Object,
          value: {
            width: 100,
            height: 100,
            left: 0,
            right: 100,
            top: 0,
            bottom: 100,
            dotRadius: 6,
            brushHandleTop: 50,
            sequences: [],
            yAxisLabel: '',
            yAxisTicks: [],
            xAxisTicks: [],
            showYAxisTickLines: true,
            showXAxisTickLines: true,
            antiBrushes: [],
          },
        },
      };
    }

    path_(sequence) {
      let path = '';
      for (const datum of sequence.data) {
        const prefix = path ? ' L' : 'M';
        path += `${prefix}${datum.x},${datum.y}`;
      }
      return path;
    }

    pct_(x) {
      return x + '%';
    }

    /**
     * @typedef {Object} Sequence
     * @property {string} name
     * @property {string} color
     * @property {!tr.b.Unit} unit
     * @property {!Array.<!Datum} data
     */

    /**
     * @typedef {Object} Datum
     * @property {number} x
     * @property {number} y
     * @property {!Array.<String>} icons
     */

    /**
     * @typedef {Object} Brush
     * @property {!tr.b.math.Range} range
     */

    /**
     * This function transforms a high-level description of the components of a
     * complex line-chart to a lower-level description or "layout".
     *
     * Non-Polymer-Redux Usage:
     *   this.$.line_chart.layout = await LineChart.layout(options);
     * Polymer-Redux usage:
     *   - await layout() in an action creator,
     *   - copy the layout object to your state in a reducer,
     *   - data-bind the layout object to a <line-chart> element.
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
     * @return {!Object}
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
          data: LineChart.normalize(rawSequence, xRange, yRange),
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
      this.dispatchEvent(new CustomEvent('dot-click', {
        detail: event.model,
      }));
    }

    onDotMouseOver_(event) {
      this.dispatchEvent(new CustomEvent('dot-mouseover', {
        detail: event.model,
      }));
    }

    onDotMouseOut_(event) {
      this.dispatchEvent(new CustomEvent('dot-mouseout', {
        detail: event.model,
      }));
    }

    onBrushHandleMouseDown_(event) {
      this.dispatchEvent(new CustomEvent('brush-handle-down', {
        detail: event.model,
      }));
    }

    onBrushHandleMouseMove_(event) {
      this.dispatchEvent(new CustomEvent('brush-handle-move', {
        detail: event.model,
      }));
    }

    onBrushHandleMouseUp_(event) {
      this.dispatchEvent(new CustomEvent('brush-handle-up', {
        detail: event.model,
      }));
    }
  }
  customElements.define(LineChart.is, LineChart);

  return {
    LineChart,
  };
});
