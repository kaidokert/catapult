/* Copyright 2019 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import {measureText} from './utils.js';

const HEIGHT_PX = 200;
const ESTIMATED_WIDTH_PX = 1000;

const ICON_WIDTH_PX = 24;
const TEXT_HEIGHT_PX = 15;

export const MODE = {
  CENTER: 'CENTER',
  DELTA: 'DELTA',
  NORMALIZE_LINE: 'NORMALIZE_LINE',
  NORMALIZE_UNIT: 'NORMALIZE_UNIT',
};

function getXExtension(ticks) {
  // Extend xRange in both directions for chartLayout, not minimapLayout in
  // order to make room for icons.
  return ticks ? (ICON_WIDTH_PX / 2 / ESTIMATED_WIDTH_PX) : 0;
}

function getYExtension(ticks) {
  // Extend yRange in both directions to prevent clipping yAxis.ticks.
  return ticks ? (TEXT_HEIGHT_PX / 2 / HEIGHT_PX) : 0;
}

export function layoutTimeseries(state) {
  if (state.fixedXAxis) {
    fixLinesXInPlace(state.lines);
  }

  const {xRange, rangeForUnitName} = normalizeLinesInPlace(state.lines, {
    mode: state.mode,
    zeroYAxis: state.zeroYAxis,
    xExtension: getXExtension(state.xAxis.generateTicks),
    yExtension: getYExtension(state.yAxis.generateTicks),
  });
  const range = getRevisionRange(state.lines, 0);

  return {
    ...state,
    xAxis: {...state.xAxis, range, displayRange: xRange},
    yAxis: {...state.yAxis, rangeForUnitName},
  };
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
}

function getX(datum) {
  return (datum.xFixed !== undefined) ? datum.xFixed : datum.x;
}

const EPOCH_MS = new Date(2010, 0, 1).getTime();
const EPOCH_S = EPOCH_MS / 1000;

function revisionRangeAsDates(revisionRange, displayRange, rawXs) {
  const nowMs = new Date().getTime();
  if (revisionRange.min > EPOCH_MS && revisionRange.max < nowMs) {
    return {
      dateRange: {
        min: new Date(revisionRange.min),
        max: new Date(revisionRange.max),
      },
      displayMs: displayRange,
      rawMs: rawXs,
    };
  }

  const nowS = nowMs / 1000;
  if (revisionRange.min > EPOCH_S && revisionRange.max < nowS) {
    return {
      dateRange: {
        min: new Date(revisionRange.min * 1000),
        max: new Date(revisionRange.max * 1000),
      },
      displayMs: tr.b.math.Range.fromExplicitRange(
          displayRange.min * 1000,
          displayRange.max * 1000),
      rawMs: rawXs ? rawXs.map(x => x * 1000) : undefined,
    };
  }

  return {};
}

function getXPct(pct) {
  return tr.b.math.truncate(pct * 100, 1) + '%';
}

// Returns [{text, xPct, anchor}].
export async function generateXTicks(state) {
  // Input: isCalendrical, xAxisWidthPx, rawXs (if fixedXAxis)
  const rangePx = tr.b.math.Range.fromExplicitRange(0, widthPx);

  // format start/end ticks
  const ticks = [{anchor: 'start', xPct: '0%'}, {anchor: 'end', xPct: '100%'}];
  if (areTimestamps) {
    ticks[0].text = tr.b.formatDate(TODO);
    ticks[1].text = formatEndDate(TODO);
  } else {
    ticks[0].text = TODO;
    ticks[1].text = TODO;
  }

  // measure start/end ticks
  const rects = await Promise.all(ticks.map(tick => measureText(tick.text)));
  //  - compute new rangePx
  rangePx.min += rects[0].width;
  rangePx.max += rects[1].width;

  ticks.push(...await generateXTicksRecurse(rangePx));
  return ticks;
}

async function generateXTicksRecurse(rangePx) {
  // TODO generate tick candidates (calendrical or pow10muls)
  const candidates = generateTicks().map(tick => {
    if (areTimestamps) {
    }
  });

  // measure candidates
  const rects = await Promise.all(ticks.map(tick => measureText(tick.text)));

  // keep candidates that fit
  const ticks = candidates.filter();

  // generate new px ranges
  // recurse
  for (const rangePx of differences) {
    ticks.push(...await generateXTicksRecurse(rangePx));
  }

  return ticks;
}

function calendarTick(ms, text, xPct, anchor) {
  const width = Math.ceil(CHAR_SIZE_PX.width * text.length);
  let px = Math.round(ESTIMATED_WIDTH_PX * xPct);
  if (anchor === 'start') {
    px = tr.b.math.Range.fromExplicitRange(px, px + width);
  } else if (anchor === 'end') {
    px = tr.b.math.Range.fromExplicitRange(px - width, px);
  } else {
    const hw = Math.ceil(width / 2);
    px = tr.b.math.Range.fromExplicitRange(px - hw, px + hw);
  }
  return {ms, text, xPct: getXPct(xPct), anchor, px};
}

function formatEndDate(range) {
  let text = tr.b.formatDate(range.max);

  // strip year if same as start
  if (range.max.getFullYear() === range.min.getFullYear()) {
    text = text.slice(5);
    // strip month and date if same as start
    if (range.max.getMonth() === range.min.getMonth() &&
        range.max.getDate() === range.min.getDate()) {
      text = text.slice(6);
    }
  }
  return text;
}

function daysInMonth(y, m) {
  return new Date(y, m + 1, 0).getDate();
}

function getRevisionRange(lines, extension) {
  const range = new tr.b.math.Range();
  for (const line of lines) {
    if (line.data.length === 0) continue;
    range.addValue(line.data[0].x);
    range.addValue(line.data[line.data.length - 1].x);
  }
  range.min -= range.range * extension;
  range.max += range.range * extension;
  return range;
}

function normalizeLinesInPlace(lines, opt_options) {
  const options = opt_options || {};
  const mode = options.mode || MODE.NORMALIZE_UNIT;
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
      const x = getX(datum);
      if (typeof(x) === 'number') xRange.addValue(x);
      if (typeof(datum.y) === 'number') line.yRange.addValue(datum.y);
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

  if (mode === MODE.CENTER) {
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
    mode === MODE.NORMALIZE_LINE || mode === MODE.CENTER);
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

export function generateYTicks(state) {
  let yAxis = state.yAxis;
  let ticks = [];
  const yExtension = getYExtension(true);
  if (state.mode === MODE.NORMALIZE_LINE || state.mode === MODE.CENTER) {
    for (const line of state.lines) {
      line.ticks = generateYTicksInternal(line.yRange, line.unit, yExtension);
    }
    if (state.lines.length === 1) {
      ticks = state.lines[0].ticks;
    }
  } else {
    const ticksForUnitName = new Map();
    for (const [unitName, range] of state.yAxis.rangeForUnitName) {
      const unit = tr.b.Unit.byName[unitName];
      const ticks = generateYTicksInternal(range, unit, yExtension);
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

function generateYTicksInternal(displayRange, unit, yExtension) {
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

export function generateTicks(range, numTicks = 5) {
  const ticks = [];

  let tickPower = tr.b.math.lesserPower(range.range);
  if ((range.range / tickPower) < numTicks) tickPower /= 10;

  // Bump min up (and max down) to the next multiple of tickPower.
  const rounded = tr.b.math.Range.fromExplicitRange(
      range.min + tickPower - (range.min % tickPower),
      range.max - (range.max % tickPower));

  const delta = rounded.range / (numTicks - 1);
  if (range.min < 0 && range.max > 0) {
    for (let tick = 0; tick <= range.max; tick += delta) {
      ticks.push(tick);
    }
    for (let tick = -delta; tick >= range.min; tick -= delta) {
      ticks.unshift(tick);
    }
  } else {
    for (let tick = rounded.min; tick <= range.max; tick += delta) {
      ticks.push(tick);
    }
  }

  return ticks;
}
