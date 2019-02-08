/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  function layoutTimeseries(state) {
    let rawXs;
    if (state.fixedXAxis) {
      rawXs = fixLinesXInPlace(state.lines);
    }

    // Extend xRange by 1% in both directions in order to make it easier to
    // click on the endpoint dots. Without this, only half of the endpoint
    // dots would be drawn and clickable. Chart width can vary widely, but
    // 600px is is a good enough approximation.
    const xExtension = 0;

    // Extend yRange by 3.75% in both directions in order to make it easier to
    // click on extreme dots. Without this, only half of the extreme dots
    // would be drawn and clickable. The main chart is 200
    // px tall and has dots with radius=6px, which is 3% of 200. This will
    // also reduce clipping yAxis.ticks, which are 15px tall and so can extend
    // 7.5px (3.75% of 200px) above/below extreme points if they happen to be
    // a round number.
    const yExtension = 0;

    const {xRange, yRangeForUnitName} = normalizeLinesInPlace(
        state.lines, {
          mode: state.mode,
          zeroYAxis: state.zeroYAxis,
          xExtension,
          yExtension,
        });

    if (state.xAxis.generateTicks) {
      state = generateXTicksReducer(state, xRange, rawXs);
    }

    if (state.yAxis.generateTicks) {
      state = generateYTicksReducer(state, yRangeForUnitName, yExtension);
    }

    return state;
  }

  function fixLinesXInPlace(lines) {
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
  }

  function getX(datum) {
    return (datum.xFixed !== undefined) ? datum.xFixed : datum.x;
  }

  function generateXTicksReducer(state, xRange, rawXs) {
    const xTickRange = new tr.b.math.Range();
    for (const line of state.lines) {
      if (line.data.length === 0) continue;
      xTickRange.addValue(line.data[0].x);
      xTickRange.addValue(line.data[line.data.length - 1].x);
    }

    const ticks = generateTicks(xTickRange).map(text => {
      let x = text;
      if (rawXs) {
        x = tr.b.findLowIndexInSortedArray(rawXs, x => x, text);
      }
      return {
        text,
        xPct: tr.b.math.truncate(xRange.normalize(x) * 100, 1) + '%',
      };
    });
    return {...state, xAxis: {...state.xAxis, ticks}};
  }

  function normalizeLinesInPlace(lines, opt_options) {
    const options = opt_options || {};
    const mode = options.mode || 'normalizeUnit';
    const zeroYAxis = options.zeroYAxis || false;
    const yExtension = options.yExtension || 0;
    const xExtension = options.xExtension || 0;

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

      // normalize count_biggerIsBetter together with count_smallerIsBetter for
      // pinpoint.success, for example.
      const unitName = line.unit.baseUnit.unitName;

      if (!yRangeForUnitName.has(unitName)) {
        yRangeForUnitName.set(unitName, new tr.b.math.Range());
      }

      line.yRange.min -= line.yRange.range * yExtension;
      line.yRange.max += line.yRange.range * yExtension;

      yRangeForUnitName.get(unitName).addRange(line.yRange);

      if (line.yRange.range > (maxLineRangeForUnitName.get(
          unitName) || 0)) {
        maxLineRangeForUnitName.set(unitName, line.yRange.range);
      }
    }

    if (mode === 'center') {
      for (const line of lines) {
        const halfMaxLineRange = maxLineRangeForUnitName.get(
            line.unit.baseUnit.unitName) / 2;
        // Extend line.yRange to be as large as the largest range.
        line.yRange = tr.b.math.Range.fromExplicitRange(
            line.yRange.center - halfMaxLineRange,
            line.yRange.center + halfMaxLineRange);
      }
    }

    xRange.min -= xRange.range * xExtension;
    xRange.max += xRange.range * xExtension;

    // Round to tenth of a percent.
    const round = x => tr.b.math.truncate(x * 100, 1);

    const isNormalizeLine = (
      mode === 'normalizeLine' || mode === 'center');
    for (const line of lines) {
      line.path = '';
      line.shadePoints = '';
      const yRange = isNormalizeLine ? line.yRange :
        yRangeForUnitName.get(line.unit.baseUnit.unitName);
      for (const datum of line.data) {
        datum.xPct = round(xRange.normalize(getX(datum)));
        // Y coordinates increase downwards.
        datum.yPct = round(1 - yRange.normalize(datum.y));
        if (isNaN(datum.xPct)) datum.xPct = 50;
        if (isNaN(datum.yPct)) datum.yPct = 50;
        const command = line.path ? ' L' : 'M';
        line.path += command + datum.xPct + ',' + datum.yPct;
        if (datum.shadeRange) {
          const shadeMax = round(1 - yRange.normalize(datum.shadeRange.max));
          line.shadePoints += ' ' + datum.xPct + ',' + shadeMax;
        }
      }
      for (let i = line.data.length - 1; i >= 0; --i) {
        const datum = line.data[i];
        if (datum.shadeRange) {
          const shadeMin = round(1 - yRange.normalize(datum.shadeRange.min));
          line.shadePoints += ' ' + datum.xPct + ',' + shadeMin;
        }
      }
    }
    return {xRange, yRangeForUnitName};
  }

  function generateYTicksReducer(state, yRangeForUnitName, yExtension) {
    let yAxis = state.yAxis;
    let ticks = [];
    if (state.mode === 'normalizeLine' || state.mode === 'center') {
      for (const line of state.lines) {
        line.ticks = generateYTicks(line.yRange, line.unit, yExtension);
      }
      if (state.lines.length === 1) {
        ticks = state.lines[0].ticks;
      }
    } else {
      const ticksForUnitName = new Map();
      for (const [unitName, range] of yRangeForUnitName) {
        const unit = tr.b.Unit.byName[unitName];
        const ticks = generateYTicks(range, unit, yExtension);
        ticksForUnitName.set(unitName, ticks);
      }
      yAxis = {...yAxis, ticksForUnitName};
      if (ticksForUnitName.size === 1) {
        ticks = [...ticksForUnitName.values()][0];
      }
    }
    yAxis = {...yAxis, ticks};
    return {...state, yAxis};
  }

  function generateYTicks(displayRange, unit, yExtension) {
    // Use the extended range to compute yPct, but the unextended range
    // to compute the ticks. TODO store both in normalizeLinesInPlace
    const dataRange = tr.b.math.Range.fromExplicitRange(
        displayRange.min + (displayRange.range * yExtension),
        displayRange.max - (displayRange.range * yExtension));
    return generateTicks(dataRange).map(y => {
      return {
        text: unit.format(y),
        yPct: tr.b.math.truncate(
            100 * (1 - displayRange.normalize(y)), 1) + '%',
      };
    });
  }

  function generateTicks(range) {
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
      for (const tick of generateTicks(negRange)) {
        ticks.push(-tick);
      }
    } else {
      const negTicks = generateTicks(
          tr.b.math.Range.fromExplicitRange(range.min, 0));
      const posTicks = generateTicks(
          tr.b.math.Range.fromExplicitRange(0, range.max)).slice(1);
      ticks.push(negTicks[0]);
      ticks.push(negTicks[2]);
      ticks.push(0);
      ticks.push(posTicks[2]);
      ticks.push(posTicks[4]);
    }
    ticks.sort((x, y) => x - y);
    return ticks;
  }

  return {layoutTimeseries};
});
