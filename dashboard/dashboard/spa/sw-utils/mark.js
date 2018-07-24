/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

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
    performance.mark(`${this.name}-start`);
  }

  end() {
    performance.mark(`${this.name}-end`);
    performance.measure(this.name, `${this.name}-start`, `${this.name}-end`);
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
      // eslint-disable-next-line no-console
      console.warn('Google Analytics configuration variables not ready');
      return;
    }

    const measures = performance.getEntriesByName(this.name);
    const { duration } = measures[measures.length - 1];
    const roundedDuration = Math.round(duration);

    const params = new URLSearchParams();
    params.set('v', 1);                 // version Number
    params.set('ds', 'web');            // data source
    params.set('cid', Mark.clientId);   // cliend ID
    params.set('tid', Mark.trackingId); // tracking ID
    params.set('t', 'timing');          // hit type
    params.set('utc', this.category);   // user timing category
    params.set('utv', this.action);     // user timing variable name
    params.set('utt', roundedDuration); // user timing time
    params.set('utl', this.label);      // user timing label

    const response = await fetch('https://www.google-analytics.com/debug/collect', {
      method: 'POST',
      body: params.toString(),
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(`Bad response from Google Analytics:\n${text}`);
    }
  }

  static configure(trackingId, clientId) {
    Mark.trackingId = trackingId;
    Mark.clientId = clientId;
  }
}

// Google Analytics configuration variables are sent from the application to
// the Service Worker shortly after being registered.
Mark.trackingId = undefined;
Mark.clientId = undefined;

export default Mark;
