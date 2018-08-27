/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

// Constants used for sending Google Analytics events/exceptions.
const VERSION_NUMBER = 1;
const DATA_SOURCE = 'web';
const HIT_TYPE_EVENT = 'event';
const HIT_TYPE_TIMING = 'timing';
const HIT_TYPE_EXCEPTION = 'exception';

/**
 * GoogleAnalytics provides an interface to Google Analytic (GA) services from
 * within a Service Worker. This is necessary since all GA client libraries take
 * advantage of the DOM, which is non-accessable within the context of a Service
 * Worker.
 *
 * See https://developers.google.com/web/ilt/pwa/integrating-analytics
 */
class GoogleAnalytics {
  constructor() {
    // GA configuration variables are sent from the application to the Service
    // Worker shortly after being registered.
    this.trackingId = undefined;
    this.clientId = undefined;

    // Used for queueing requests until GA is initialized.
    this.formQueue = [];
  }

  // Configure Google Analytics. Any events sent before this function is called
  // will be immediately sent to Google Analytics.
  configure(trackingId, clientId) {
    this.trackingId = trackingId;
    this.clientId = clientId;

    // Send out all pending beacons.
    for (const form of this.formQueue) {
      this.sendBeacon_(form);
    }
    this.formQueue = [];
  }

  sendEvent(category, action, label, value) {
    const form = this.createForm_();
    form.set('t', HIT_TYPE_EVENT);
    form.set('ec', category);
    form.set('ea', action);
    form.set('ev', value);
    if (label) {
      form.set('el', label);
    }
    this.send_(form);
  }

  sendTiming(category, action, duration, label) {
    const form = this.createForm_();
    const roundedDuration = Math.round(duration);
    form.set('t', HIT_TYPE_TIMING);
    form.set('utc', category);
    form.set('utv', action);
    form.set('utt', roundedDuration);
    if (label) {
      form.set('utl', label);
    }
    this.send_(form);
  }

  sendException(description, fatal = true) {
    const form = this.createForm_();
    form.set('t', HIT_TYPE_EXCEPTION);
    form.set('exd', description);
    form.set('exf', fatal);
    this.send_(form);
  }

  createForm_() {
    const form = new FormData();
    form.set('v', VERSION_NUMBER);
    form.set('ds', DATA_SOURCE);
    form.set('cid', GoogleAnalytics.clientId);
    form.set('tid', GoogleAnalytics.trackingId);
    return form;
  }

  send_(form) {
    if (!this.clientId || !this.trackingId) {
      // Google Analytics configuration variables not setup. Try again later.
      this.formQueue.push(form);
    } else {
      this.sendBeacon_(form);
    }
  }

  async sendBeacon_(form) {
    self.navigator.sendBeacon('https://www.google-analytics.com/collect', form);
  }
}

const ga = new GoogleAnalytics();
export default ga;
