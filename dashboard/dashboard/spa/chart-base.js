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
          event.model.datum);
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
      const xPct = ChartBase.computeBrush(
          event.detail.x, await cp.measureElement(this.$.main));
      this.dispatch('brushX', this.statePath, event.model.brushIndex, xPct);
      this.dispatchEvent(new CustomEvent('brush', {
        bubbles: true,
        composed: true,
        detail: {
          brushIndex: event.model.brushIndex,
          sourceEvent: event,
        },
      }));
    }

    brushPointSize_(brushSize) {
      if (isNaN(brushSize)) return 0;
      return brushSize * 1.5;
    }

    brushPointPx_(brushSize) {
      return this.brushPointSize_(brushSize) + 'px';
    }

    totalHeight_(graphHeight, brushSize, xAxisHeight) {
      return graphHeight + this.brushPointSize_(brushSize) + xAxisHeight;
    }
  }

  ChartBase.properties = cp.ElementBase.statePathProperties('statePath', {
    bars: {type: Array, value: []},
    brushSize: {type: Number, value: 10},
    columns: {type: Array, value: []},
    dotCursor: {type: String},
    dotRadius: {type: Number, value: 6},
    graphHeight: {type: Number, value: 200},
    lines: {type: Array, value: []},
    tooltip: {type: Object},
    xAxis: {type: Object, value: {height: 0}},
    yAxis: {type: Object, value: {width: 0}},
  });

  ChartBase.newState = () => {
    return {
      bars: [],
      brushSize: 10,
      columns: [],
      dotCursor: 'pointer',
      dotRadius: 6,
      graphHeight: 200,
      lines: [],
      tooltip: {
        isVisible: false,
        left: '',
        right: '',
        top: '',
        bottom: '',
        color: '',
        rows: [],
      },
      xAxis: {
        brushes: [],
        height: 0,
        range: new tr.b.math.Range(),
        showTickLines: false,
        ticks: [],
      },
      yAxis: {
        brushes: [],
        range: new tr.b.math.Range(),
        showTickLines: false,
        ticks: [],
        width: 0,
      },
    };
  };

  ChartBase.actions = {
    brushX: (statePath, brushIndex, xPct) => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(
          `${statePath}.xAxis.brushes.${brushIndex}`,
          {xPct}));
    },

    boldLine: (statePath, lineIndex) => async (dispatch, getState) => {
      dispatch({
        type: ChartBase.reducers.boldLine.typeName,
        statePath,
        lineIndex,
      });
    },

    dotMouseOver: (statePath, chartRect, lineIndex, datum) =>
      async (dispatch, getState) => {
        dispatch(ChartBase.actions.boldLine(statePath, lineIndex));
        dispatch({
          type: ChartBase.reducers.dotMouseOver.typeName,
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

    unboldLines: statePath => async (dispatch, getState) => {
      dispatch({
        type: ChartBase.reducers.unboldLines.typeName,
        statePath,
      });
    },

    dotMouseOut: (statePath, lineIndex) => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(
          `${statePath}.tooltip`, {isVisible: false}));
      dispatch({
        type: ChartBase.reducers.unboldLines.typeName,
        statePath,
      });
    },
  };

  const COS_45 = Math.cos(Math.PI / 4);
  const ERROR_ICON_RADIUS_PX = 10.8;

  ChartBase.reducers = {
    unboldLines: cp.ElementBase.statePathReducer((state, action) => {
      const lines = state.lines.map(line => {
        return {...line, strokeWidth: 1};
      });
      return {...state, lines};
    }),

    boldLine: cp.ElementBase.statePathReducer((state, action) => {
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
      return {...state, lines};
    }),

    dotMouseOver: cp.ElementBase.statePathReducer((state, action) => {
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
        tooltip: {
          bottom,
          color: state.lines[action.lineIndex].color,
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
    brushes = brushes.map(brush =>
      parseFloat(brush.xPct)).sort((a, b) => a - b);
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
    return rawXs;
  };

  function getX(datum) {
    return (datum.xFixed !== undefined) ? datum.xFixed : datum.x;
  }

  ChartBase.normalizeLinesInPlace = (lines, opt_options) => {
    const options = opt_options || {};
    const normalize = options.normalize || false;
    const zeroYAxis = options.zeroYAxis || false;
    const yExtension = options.yExtension || 0;
    const xExtension = options.xExtension || 0;

    const xRange = new tr.b.math.Range();
    const yRangeForUnitName = new Map();
    let maxLineLength = 0;
    for (const line of lines) {
      maxLineLength = Math.max(maxLineLength, line.data.length);
      line.yRange = new tr.b.math.Range();
      if (zeroYAxis) line.yRange.addValue(0);
      for (const datum of line.data) {
        xRange.addValue(getX(datum));
        line.yRange.addValue(datum.y);
      }
      if (!yRangeForUnitName.has(line.unit.unitName)) {
        yRangeForUnitName.set(line.unit.unitName, new tr.b.math.Range());
      }
      line.yRange.min -= line.yRange.range * yExtension;
      line.yRange.max += line.yRange.range * yExtension;
      yRangeForUnitName.get(line.unit.unitName).addRange(line.yRange);
    }

    xRange.min -= xRange.range * xExtension;
    xRange.max += xRange.range * xExtension;

    // Round to tenth of a percent.
    const round = x => roundDigits(x * 100, 1);

    for (const line of lines) {
      line.path = '';
      const yRange = normalize ? line.yRange :
        yRangeForUnitName.get(line.unit.unitName);
      for (const datum of line.data) {
        datum.xPct = round(xRange.normalize(getX(datum)));
        // Y coordinates increase downwards.
        datum.yPct = round(1 - yRange.normalize(datum.y));
        if (isNaN(datum.xPct)) datum.xPct = '50';
        if (isNaN(datum.yPct)) datum.yPct = '50';
        const command = line.path ? ' L' : 'M';
        line.path += command + datum.xPct + ',' + datum.yPct;
        // Convert to strings for <circle>
        datum.xPct += '%';
        datum.yPct += '%';
      }
    }
    return {xRange, yRangeForUnitName};
  };

  ChartBase.computeBrush = (x, containerRect) => {
    const value = tr.b.math.normalize(
        x, containerRect.left, containerRect.right);
    return tr.b.math.clamp(100 * value, 0, 100) + '%';
  };

  cp.ElementBase.register(ChartBase);

  function roundDigits(value, digits) {
    const power = Math.pow(10, digits);
    return Math.round(value * power) / power;
  }

  return {
    ChartBase,
    roundDigits,
  };
});
