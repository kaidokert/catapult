/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  PolymerSvgTemplate('chart-base');

  class ChartBase extends Polymer.GestureEventListeners(cp.ElementBase) {
    collectIcons_(line) {
      return line.data.filter(datum => datum.icon);
    }

    antiBrushes_(brushes) {
      return ChartBase.antiBrushes(brushes);
    }

    onDotClick_(event) {
      event.cancelBubble = true;
      this.dispatchEvent(new CustomEvent('dot-click', {
        bubbles: true,
        composed: true,
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
      this.dispatchEvent(new CustomEvent('chart-click', {
        bubbles: true,
        composed: true,
      }));
    }

    async onDotMouseOver_(event) {
      const chartRect = await cp.measureElement(this.$.main);
      this.dispatch('dotMouseOver', this.statePath,
          chartRect,
          event.model.parentModel.lineIndex,
          event.model.datum,
          event.path[0].tagName === 'IRON-ICON');
      this.dispatchEvent(new CustomEvent('dot-mouseover', {
        bubbles: true,
        composed: true,
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
        bubbles: true,
        composed: true,
        detail: {
          datum: event.model.datum,
          datumIndex: event.model.datumIndex,
          line: event.model.parentModel.line,
          lineIndex: event.model.parentModel.lineIndex,
          sourceEvent: event,
        },
      }));
    }

    async onTrackBrushHandle_(event) {
      this.dispatchEvent(new CustomEvent('brush', {
        bubbles: true,
        composed: true,
        detail: {
          brushIndex: event.model.brushIndex,
          value: ChartBase.computeBrush(
              event.detail.x, await cp.measureElement(this.$.main)),
          sourceEvent: event,
        },
      }));
    }
  }

  ChartBase.properties = cp.ElementBase.statePathProperties('statePath', {
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

  ChartBase.actions = {
    dotMouseOver: (statePath, chartRect, lineIndex, datum) =>
      async (dispatch, getState) => {
        dispatch({
          reducer: ChartBase.reducers.dotMouseOver,
          statePath,
          chartRect,
          lineIndex,
          datum,
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

  const COS_45 = Math.cos(Math.PI / 4);
  const ERROR_ICON_RADIUS_PX = 10.8;

  ChartBase.reducers = {
    dotMouseOver: cp.ElementBase.statePathReducer((state, action) => {
      const lines = Array.from(state.lines);
      // Set its strokeWidth:2
      const line = lines[action.lineIndex];
      lines.splice(action.lineIndex, 1, {
        ...line,
        strokeWidth: 2,
      });
      if (action.lineIndex !== (lines.length - 1)) {
        // Move action.lineIndex to the end so it is drawn over top of any other
        // lines.
        [lines[action.lineIndex], lines[lines.length - 1]] =
          [lines[lines.length - 1], lines[action.lineIndex]];
      }

      let dotRadius = state.dotRadius;
      if (action.datum.icon === 'error') dotRadius = ERROR_ICON_RADIUS_PX;
      const offset = COS_45 * dotRadius;

      // All these coordinates are pixels relative to the top left corner of
      // #main.
      const dotCenter = {
        x: action.chartRect.width * parseFloat(action.datum.xPct) / 100,
        y: action.chartRect.height * parseFloat(action.datum.yPct) / 100,
      };
      const chartCenter = {
        x: action.chartRect.width / 2,
        y: action.chartRect.height / 2,
      };

      const roundPx = x => (Math.round(10 * (x + offset)) / 10) + 'px';

      let top = '';
      let bottom = '';
      if (dotCenter.y > chartCenter.y) {
        bottom = roundPx(action.chartRect.height - dotCenter.y);
      } else {
        top = roundPx(dotCenter.y);
      }

      let left = '';
      let right = '';
      if (dotCenter.x > chartCenter.x) {
        right = roundPx(action.chartRect.width - dotCenter.x);
      } else {
        left = roundPx(dotCenter.x);
      }

      return {
        ...state,
        lines,
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

  ChartBase.antiBrushes = brushes => {
    if (!brushes || brushes.length === 0) return [];
    if (brushes.length % 2 === 1) throw new Error('Odd number of brushes');
    brushes = brushes.map(brush => parseFloat(brush.x)).sort((a, b) => a - b);
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
  };

  ChartBase.fixLinesXInPlace = lines => {
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
        datum.xFixed = rawXs.indexOf(datum.x);
      }
    }
  };

  ChartBase.normalizeLinesInPlace = lines => {
    const xRange = new tr.b.math.Range();
    let maxLineLength = 0;
    for (const line of lines) {
      maxLineLength = Math.max(maxLineLength, line.data.length);
      line.yRange = new tr.b.math.Range();
      for (const datum of line.data) {
        xRange.addValue(datum.xFixed || datum.x);
        line.yRange.addValue(datum.y);
      }
    }

    // Extend xRange by half the average distance between x values in both
    // directions.
    /* TODO keep this from breaking xAxisTicks
    const xDatumRange = xRange.range / maxLineLength;
    const extension = (xRange.range / maxLineLength) / 2;
    xRange.min -= extension;
    xRange.max += extension;
    */

    for (const line of lines) {
      line.path = '';
      for (const datum of line.data) {
        // Round to tenth of a percent.
        datum.xPct = Math.round(
            xRange.normalize(datum.xFixed || datum.x) * 1000) / 10;

        // Y coordinates increase downwards.
        datum.yPct = Math.round(
            (1 - line.yRange.normalize(datum.y)) * 1000) / 10;

        const prefix = line.path ? ' L' : 'M';
        line.path += prefix + datum.xPct + ',' + datum.yPct;

        // Convert to strings for <circle>
        datum.xPct += '%';
        datum.yPct += '%';
      }
    }
  };

  ChartBase.computeBrush = (x, containerRect) => {
    const value = tr.b.math.normalize(
        x, containerRect.left, containerRect.right);
    return tr.b.math.clamp(100 * value, 0, 100);
  };

  cp.ElementBase.register(ChartBase);

  return {
    ChartBase,
  };
});
