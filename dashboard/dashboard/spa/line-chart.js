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

    /**
     * Non-Polymer-Redux Usage:
     *   this.$.line_chart.layout = await LineChart.layout(options);
     * Polymer-Redux usage:
     *   - call layout() in an action creator,
     *   - then() dispatch an action containing the layout object,
     *   - data-bind the layout object to a <line-chart> element.
     */
    static async layout(options) {
      // TODO Promise.all(ticks.map(tick => cp.measureText(tick, {})))
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
