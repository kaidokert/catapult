/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
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

    collectIcons_(lines) {
      const icons = [];
      for (const line of lines) {
        for (const datum of line.data) {
          if (!datum.icons) continue;
          for (const icon of datum.icons) {
            icons.push({
              x: datum.x,
              y: datum.y,
              icon,
            });
          }
        }
      }
      return icons;
    }

    antiBrushes_(brushes) {
      return MultiChart.antiBrushes(brushes);
    }

    static antiBrushes(brushes) {
      if (!brushes || brushes.length === 0) return [];
      if (brushes.length % 2 === 1) throw new Error('Odd number of brushes');
      brushes = brushes.map(brush => parseInt(brush.x)).sort((a, b) => a - b);
      let previous = {start: 0, length: undefined};
      const antiBrushes = [previous];
      for (let i = 0; i < brushes.length; i += 2) {
        previous.length = (brushes[i] - previous.start) + '%';
        previous.start += '%';
        if (brushes[i + 1] === 100) return antiBrushes;
        previous = {start: brushes[i + 1], length: undefined};
        antiBrushes.push(previous);
      }
      previous.length = (100 - previous.start) + '%';
      previous.start += '%';
      return antiBrushes;
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
        line.path = '';
        for (const datum of line.data) {
          // Round to tenth of a percent.
          datum.x = Math.round(xRange.normalize(datum.x) * 1000) / 10;
          // Y coordinates increase downwards.
          datum.y = Math.round((1 - line.yRange.normalize(datum.y)) * 1000) /
            10;

          const prefix = line.path ? ' L' : 'M';
          line.path += prefix + datum.x + ',' + datum.y;

          // Convert to strings for <circle>
          datum.x += '%';
          datum.y += '%';
        }
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
      const chartRect = await cp.measureElement(this.$.main);
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

  // Dots are circles. |dotRect| is the square that contains the dot.
  // Offset the tooltip from |dotRect| such that its corner is tangent to the
  // circle. Do not allow the tooltip to overlap the dot, which can cause
  // flickering via rapid mouseover/mouseout events.
  // The offset is computed as the length of a side of a right isosceles
  // triangle whose hypotenuse is the exsecant between the circle and the corner
  // of the |dotRect|. That hypotenuse is |dotRadius * sqrt(2) - dotRadius|.
  // sin(45) = offset / hypotenuse
  const SQRT2_1 = Math.sqrt(2) - 1;
  const SIN_45 = Math.sin(Math.PI / 4);
  const CIRCLE_TANGENT = SIN_45 * SQRT2_1;

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

      const offset = state.dotRadius * CIRCLE_TANGENT;

      const chartMid = {
        x: (action.chartRect.x + (action.chartRect.width / 2)),
        y: (action.chartRect.y + (action.chartRect.height / 2)),
      };
      let top = '';
      let bottom = '';
      if (action.dotRect.y > chartMid.y) {
        bottom = action.chartRect.bottom - action.dotRect.top - offset;
        bottom += 'px';
      } else {
        top = (action.dotRect.bottom - action.chartRect.top - offset) + 'px';
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
