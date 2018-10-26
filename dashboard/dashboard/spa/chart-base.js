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

    tooltipHidden_(tooltip) {
      return !tooltip || !tooltip.isVisible || this.isEmpty_(tooltip.rows);
    }

    brushPointSize_(brushSize) {
      if (isNaN(brushSize)) return 0;
      return brushSize * 1.5;
    }

    async onMainClick_(event) {
      this.dispatchEvent(new CustomEvent('chart-click', {
        bubbles: true,
        composed: true,
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
  }

  ChartBase.State = {
    brushSize: options => 10,
    graphHeight: options => 200,
    lines: options => [],
    tooltip: options => {
      return {
        isVisible: false,
        left: '',
        right: '',
        top: '',
        bottom: '',
        color: '',
        rows: [],
      };
    },
    xAxis: options => {
      return {
        brushes: [],
        height: 0,
        range: new tr.b.math.Range(),
        showTickLines: false,
        ticks: [],
      };
    },
    yAxis: options => {
      return {
        brushes: [],
        range: new tr.b.math.Range(),
        showTickLines: false,
        ticks: [],
        width: 0,
      };
    },
  };

  ChartBase.properties = cp.buildProperties('state', ChartBase.State);
  ChartBase.buildState = options => cp.buildState(ChartBase.State, options);

  ChartBase.actions = {
    brushX: (statePath, brushIndex, xPct) => async(dispatch, getState) => {
      const path = `${statePath}.xAxis.brushes.${brushIndex}`;
      dispatch(Redux.UPDATE(path, {xPct}));
    },

    boldLine: (statePath, lineIndex) => async(dispatch, getState) => {
      dispatch({
        type: ChartBase.reducers.boldLine.name,
        statePath,
        lineIndex,
      });
    },

    tooltip: (statePath, rows) => async(dispatch, getState) => {
      dispatch(Redux.UPDATE(statePath + '.tooltip', {rows}));
    },

    unboldLines: statePath => async(dispatch, getState) => {
      dispatch({
        type: ChartBase.reducers.unboldLines.name,
        statePath,
      });
    },
  };

  const COS_45 = Math.cos(Math.PI / 4);
  const ERROR_ICON_RADIUS_PX = 12;

  ChartBase.reducers = {
    unboldLines: (state, action, rootState) => {
      const lines = state.lines.map(line => {
        return {...line, strokeWidth: 1};
      });
      return {...state, lines};
    },

    boldLine: (state, action, rootState) => {
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
    },
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

  ChartBase.layoutLinesInPlace = state => {
    let rawXs;
    if (state.fixedXAxis) {
      rawXs = cp.ChartBase.fixLinesXInPlace(state.lines);
    }

    const {xRange, yRangeForUnitName} = cp.ChartBase.normalizeLinesInPlace(
        state.lines, {
          mode: state.mode,
          zeroYAxis: state.zeroYAxis,
        });

    if (state.xAxis.generateTicks) {
      state = ChartBase.generateXTicksReducer(state, xRange, rawXs);
    }

    if (state.yAxis.generateTicks) {
      state = ChartBase.generateYTicksReducer(
          state, yRangeForUnitName);
    }

    return state;
  };

  ChartBase.generateXTicksReducer = (state, xRange, rawXs) => {
    const xTickRange = new tr.b.math.Range();
    for (const line of state.lines) {
      if (line.data.length === 0) continue;
      xTickRange.addValue(line.data[0].x);
      xTickRange.addValue(line.data[line.data.length - 1].x);
    }

    const ticks = ChartBase.generateTicks(xTickRange).map(text => {
      let x = text;
      if (rawXs) {
        x = tr.b.findLowIndexInSortedArray(rawXs, x => x, text);
      }
      return {
        text,
        xPct: cp.roundDigits(xRange.normalize(x) * 100, 1) + '%',
      };
    });
    return {...state, xAxis: {...state.xAxis, ticks}};
  };

  ChartBase.normalizeLinesInPlace = (lines, opt_options) => {
    const options = opt_options || {};
    const mode = options.mode || 'normalizeUnit';
    const zeroYAxis = options.zeroYAxis || false;

    const xRange = new tr.b.math.Range();
    const yRangeForUnitName = new Map();
    let maxLineLength = 0;
    const maxLineRangeForUnitName = new Map();
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

      yRangeForUnitName.get(line.unit.unitName).addRange(line.yRange);

      if (line.yRange.range > (maxLineRangeForUnitName.get(
          line.unit.unitName) || 0)) {
        maxLineRangeForUnitName.set(line.unit.unitName, line.yRange.range);
      }
    }

    if (mode === 'center') {
      for (const line of lines) {
        const halfMaxLineRange = maxLineRangeForUnitName.get(
            line.unit.unitName) / 2;
        // Extend line.yRange to be as large as the largest range.
        line.yRange = tr.b.math.Range.fromExplicitRange(
            line.yRange.center - halfMaxLineRange,
            line.yRange.center + halfMaxLineRange);
      }
    }

    // Round to tenth of a percent.
    const round = x => roundDigits(x * 100, 1);

    const isNormalizeLine = (
      mode === 'normalizeLine' || mode === 'center');
    for (const line of lines) {
      line.path = '';
      line.shadePoints = '';
      const yRange = isNormalizeLine ? line.yRange :
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
        if (datum.shadeRange) {
          const shadeMax = round(1 - yRange.normalize(datum.shadeRange.max));
          line.shadePoints += ' ' + datum.xPct.slice(0, -1) + ',' + shadeMax;
        }
      }
      for (let i = line.data.length - 1; i >= 0; --i) {
        const datum = line.data[i];
        if (datum.shadeRange) {
          const shadeMin = round(1 - yRange.normalize(datum.shadeRange.min));
          line.shadePoints += ' ' + datum.xPct.slice(0, -1) + ',' + shadeMin;
        }
      }
    }
    return {xRange, yRangeForUnitName};
  };

  ChartBase.generateYTicksReducer = (state, yRangeForUnitName) => {
    let yAxis = state.yAxis;
    let ticks = [];
    if (state.mode === 'normalizeLine' || state.mode === 'center') {
      for (const line of state.lines) {
        line.ticks = ChartBase.generateYTicks(line.yRange, line.unit);
      }
      if (state.lines.length === 1) {
        ticks = state.lines[0].ticks;
      }
    } else {
      const ticksForUnitName = new Map();
      for (const [unitName, range] of yRangeForUnitName) {
        const unit = tr.b.Unit.byName[unitName];
        const ticks = ChartBase.generateYTicks(range, unit);
        ticksForUnitName.set(unitName, ticks);
      }
      yAxis = {...yAxis, ticksForUnitName};
      if (ticksForUnitName.size === 1) {
        ticks = [...ticksForUnitName.values()][0];
      }
    }
    yAxis = {...yAxis, ticks};
    return {...state, yAxis};
  };

  ChartBase.generateYTicks = (displayRange, unit) => {
    // Use the extended range to compute yPct, but the unextended range
    // to compute the ticks. TODO store both in normalizeLinesInPlace
    const dataRange = tr.b.math.Range.fromExplicitRange(
        displayRange.min + (displayRange.range),
        displayRange.max - (displayRange.range));
    return ChartBase.generateTicks(dataRange).map(y => {
      return {
        text: unit.format(y),
        yPct: cp.roundDigits(100 * (1 - displayRange.normalize(y)), 1) + '%',
      };
    });
  };

  ChartBase.generateTicks = range => {
    const ticks = [];
    if (range.min >= 0) {
      let tickDelta = tr.b.math.lesserPower(range.range);
      if ((range.range / tickDelta) < 5) tickDelta /= 10;
      if (range.min > 0) {
        range = tr.b.math.Range.fromExplicitRange(
            (range.min + tickDelta), range.max);
      }
      range = tr.b.math.Range.fromExplicitRange(
          (range.min - (range.min % tickDelta)),
          (range.max - (range.max % tickDelta)));
      tickDelta = range.range / 5;
      for (let x = range.min; x <= range.max; x += tickDelta) {
        ticks.push(x);
      }
    } else if (range.max <= 0) {
      const negRange = tr.b.math.Range.fromExplicitRange(
          -range.max, -range.min);
      for (const tick of ChartBase.generateTicks(negRange)) {
        ticks.push(-tick);
      }
    } else {
      const negTicks = ChartBase.generateTicks(
          tr.b.math.Range.fromExplicitRange(range.min, 0));
      const posTicks = ChartBase.generateTicks(
          tr.b.math.Range.fromExplicitRange(0, range.max)).slice(1);
      ticks.push(negTicks[0]);
      ticks.push(negTicks[2]);
      ticks.push(0);
      ticks.push(posTicks[2]);
      ticks.push(posTicks[4]);
    }
    ticks.sort((x, y) => x - y);
    return ticks;
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
