/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import analytics from './google-analytics.js';

const VERSION_NUMBER = 1;
const DATA_SOURCE = 'web';
const HIT_TYPE = 'timing';

// Give Timing marks unique names through the use of a numeric counter. This
// only works for the first 2^54 marks. After that, this counter is always the
// same due to JavaScript's double-precision floating-point Number
// implementation (IEEE 754).
let counter = 0;

/**
 * Timing measures performance-related information for display on the Chrome
 * DevTools Performance tab and Google Analytics.
 */
export class Timing {
  constructor(category, action, label) {
    if (!category) throw new Error('No category specified');
    if (!action) throw new Error(`No action specified for ${category}`);
    if (!label) throw new Error(`No label specified for ${category} ${action}`);

    this.category = category;
    this.action = action;
    this.label = label;

    this.name = `${category} - ${action}`;
    this.uid = `${this.name}-${counter++}`;
    performance.mark(`${this.uid}-start`);
  }

  // Measure how long this Timing mark took from start to end.
  end() {
    performance.mark(`${this.uid}-end`);
    performance.measure(this.name, `${this.uid}-start`, `${this.uid}-end`);
    this.sendAnalyticsEvent();
  }

  // Send a timing hit to Google Analytics.
  async sendAnalyticsEvent() {
    const start = performance.getEntriesByName(`${this.uid}-start`)[0];
    const end = performance.getEntriesByName(`${this.uid}-end`)[0];
    const duration = end.startTime - start.startTime;

    analytics.sendTiming(this.category, this.action, duration, this.label);
  }

  // Cancel the Timing mark by removing the starting mark.
  remove() {
    performance.clearMarks(`${this.uid}-start`);
  }
}

export default Timing;
