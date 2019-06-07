/* Copyright 2019 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import {html} from 'lit-element';
import {plural} from './utils.js';

function analyzeTriaged(triagedAlerts) {
  const alertCountByBugId = new Map();
  for (const alert of triagedAlerts) {
    alertCountByBugId.set(alert.bugId,
        1 + (alertCountByBugId.get(alert.bugId) || 0));
  }
  let bugId = 0;
  let maxAlertCount = 0;
  for (const [triagedBugId, alertCount] of alertCountByBugId) {
    if (alertCount > maxAlertCount) {
      maxAlertCount = alertCount;
      bugId = triagedBugId;
    }
  }

  return {bugId, maxAlertCount};
}

function analyzeAlerts(alerts) {
  let maxPctDelta = 0;
  for (const alert of alerts) {
    maxPctDelta = Math.max(maxPctDelta, alert.percentDeltaValue);
  }
  return {maxPctDelta};
}

export function autotriage(alerts, triagedAlerts) {
  const {maxPctDelta} = analyzeAlerts(alerts);
  const {bugId, maxAlertCount} = analyzeTriaged(triagedAlerts);

  if (maxPctDelta < MIN_PCT_DELTA) {
    const explanation = html`
      The largest regression is < 2%.
    `;
    return {bugId: -2, explanation};
  }

  if (bugId < 0) {
    const explanation = html`
      ${maxAlertCount} similar alert${plural(maxAlertCount)} were ignored.
    `;
    return {bugId, explanation};
  }

  if (bugId) {
    const explanation = html`
      ${maxAlertCount} similar alert${plural(maxAlertCount)} were assigned to
      ${bugId}.
    `;
    return {bugId, explanation};
  }

  const explanation = html`
    A ${maxPctDelta * 100}% regression is significant with no similar triaged
    alerts.
  `;
  return {bugId, explanation};
}
