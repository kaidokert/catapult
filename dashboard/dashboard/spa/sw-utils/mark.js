/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

// Constants used in sending Google Analytics timing events.
const VERSION_NUMBER = 1;
const DATA_SOURCE = 'web';
const HIT_TYPE = 'timing';

/**
 * Mark measures performance-related information for display on the Chrome
 * DevTools Performance tab and Google Analytics.
 */
export class Mark {
  constructor(category, action, label) {
    this.category = category;
    this.action = action;
    this.label = label;

    this.name = `${category}-${action}`;
    this.uid = `${this.name}-${Mark.counter++}`;
    performance.mark(`${this.uid}-start`);
  }

  // Measure how long this Mark took from start to end.
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
    if (!Mark.clientId || !Mark.trackingId) {
      // Google Analytics configuration variables not ready. Try again in a sec.
      setTimeout(() => this.sendAnalyticsEvent(), 1000);
      return;
    }

    const measures = performance.getEntriesByName(this.name);
    const { duration } = measures[measures.length - 1];
    const roundedDuration = Math.round(duration);

    const params = new URLSearchParams();
    params.set('v', VERSION_NUMBER);
    params.set('ds', DATA_SOURCE);
    params.set('cid', Mark.clientId);   // cliend ID
    params.set('tid', Mark.trackingId); // tracking ID
    params.set('t', HIT_TYPE);
    params.set('utc', this.category);   // user timing category
    params.set('utv', this.action);     // user timing variable name
    params.set('utt', roundedDuration); // user timing time
    params.set('utl', this.label);      // user timing label

    const response = await fetch('https://www.google-analytics.com/collect', {
      method: 'POST',
      body: params.toString(),
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`Bad response from Google Analytics:\n${text}`);
    }
  }

  // Cancel the Mark by removing the starting mark.
  remove() {
    performance.clearMarks(`${this.uid}-start`);
  }

  // Configure Google Analytics. Any Marks ended before this function is called
  // will be sent to Google Analytics within a second after.
  static configure(trackingId, clientId) {
    Mark.trackingId = trackingId;
    Mark.clientId = clientId;
  }
}

// Give Marks unique names through the use of a numeric counter. This only works
// for the first 2^54 Marks. After that, this counter is always the same.
Mark.counter = 0;

// Google Analytics configuration variables are sent from the application to
// the Service Worker shortly after being registered.
Mark.trackingId = undefined;
Mark.clientId = undefined;

export default Mark;
