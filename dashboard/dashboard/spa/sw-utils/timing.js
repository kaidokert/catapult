/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import analytics from './google-analytics.js';

// Constants used in sending Google Analytics timing events.
const VERSION_NUMBER = 1;
const DATA_SOURCE = 'web';
const HIT_TYPE = 'timing';

/**
 * Timing measures performance-related information for display on the Chrome
 * DevTools Performance tab and Google Analytics.
 */
export class Timing {
  constructor(category, action, label) {
    this.category = category;
    this.action = action;
    this.label = label;

    this.name = `${category} - ${action}`;
    this.uid = `${this.name}-${Timing.counter++}`;
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
    if (!this.label) {
      // eslint-disable-next-line no-console
      console.warn(`No label specified for ${this.name}`);
      return;
    }

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

// Give Timing marks unique names through the use of a numeric counter. This
// only works for the first 2^54 marks. After that, this counter is always the
// same.
Timing.counter = 0;

export default Timing;
