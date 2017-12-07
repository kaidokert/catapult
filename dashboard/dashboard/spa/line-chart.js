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
     * @param {!tr.b.Unit} options.unit for formatting y-axis ticks
     * @param {!Function} options.xAxis for formatting x-axis ticks
     * @param {!Array.<!Sequence>} options.sequences
     * @param {!Array.<!Brush>} options.brushes
     * @param {Boolean} options.showYAxisTickLines
     * @param {Boolean} options.showXAxisTickLines
     * @param {number} options.dotRadius
     * @param {string} options.dotCursor
     * @param {number} options.brushHandlePx
     * @return {!Object}
     */
    static async layout(options) {
      const yRange = new tr.b.math.Range();
      const xRange = new tr.b.math.Range();
      for (const rawSequence of options.sequences) {
        for (const rawDatum of rawSequence) {
          yRange.addValue(rawDatum.y);
          xRange.addValue(rawDatum.x);
        }
      }

      const sequences = [];
      for (const rawSequence of options.sequences) {
        const sequence = {
          color: rawSequence.color,
          data: [],
        };
        sequences.push(sequence);

        for (const rawDatum of rawSequence) {
          const datum = {
            datum: rawDatum,
            x: 100 * xRange.normalize(rawDatum.x),
            y: 100 * yRange.normalize(rawDatum.y),
          };
          sequence.data.push(datum);
        }
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
