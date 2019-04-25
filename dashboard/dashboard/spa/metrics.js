/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import '/@chopsui/tsmon-client/tsmon-client.js';

const tsMonClient = new window.chops.tsmon.TSMonClient();

const ANALYTICS_GROUPS = ['firstPaint', 'fetch', 'load'];
function filterAnalyticsEvent(category, value) {
  if (value > 100) return true;
  return ANALYTICS_GROUPS.includes(category);
}

function analyticsEvent(eventCategory, eventAction, eventValue) {
  if (!(window.ga instanceof Function)) return;
  if (!filterAnalyticsEvent(eventCategory, eventValue)) return;
  ga('send', {hitType: 'event', eventCategory, eventAction, eventValue});
}

const TSMON_METRICS = new Map();

function tsmonEvent(eventCategory, eventName, eventValue) {
  const name = `chromeperf2/${eventCategory}/${eventName}`;
  if (!TSMON_METRICS.has(name)) {
    const metadata = {};
    const fields = new Map([
    ]);
    TSMON_METRICS.set(name, tsMonClient.cumulativeDistribution(
        name, name, metadata, fields));
  }
  const metric = TSMON_METRICS.get(name);
  const fields = new Map();
  metric.add(eventValue, fields);
}

export class Mark {
  constructor(groupName, functionName, opt_timestamp) {
    this.groupName_ = groupName;
    this.functionName_ = functionName;
    const guid = cp.simpleGUID();
    this.measureName_ = `${groupName} ${functionName}`;
    if (opt_timestamp) {
      this.startMark_ = {startTime: opt_timestamp};
    } else {
      this.startMarkName_ = `${this.measureName} ${guid} start`;
    }
    this.endMark_ = undefined;
    this.endMarkName_ = `${this.measureName} ${guid} end`;

    window.performance.mark(this.startMarkName_);
  }

  get groupName() {
    return this.groupName_;
  }

  get functionName() {
    return this.functionName_;
  }

  get measureName() {
    return this.measureName_;
  }

  get startMark() {
    return this.startMark_ || window.performance.getEntriesByName(
        this.startMarkName_)[0];
  }

  get endMark() {
    return this.endMark_ || window.performance.getEntriesByName(
        this.endMarkName_)[0];
  }

  get durationMs() {
    // There may be many measures named `this.measureName`, but the start and
    // end mark names contain a GUID so they are unique.
    return this.endMark.startTime - this.startMark.startTime;
  }

  end(opt_timestamp) {
    if (opt_timestamp) {
      this.endMark_ = {startTime: opt_timestamp};
    } else {
      window.performance.mark(this.endMarkName_);
    }

    if (!this.startMark_ && !this.endMark_) {
      window.performance.measure(
          this.measureName_, this.startMarkName_, this.endMarkName_);
    } else if (Mark.logVoidMarks && !(window.ga instanceof Function)) {
      // eslint-disable-next-line no-console
      console.log('void mark',
          this.groupName, this.functionName, this.durationMs);
    }

    analyticsEvent(this.groupName, this.functionName, this.durationMs);
    tsmonEvent(this.groupName, this.functionName, this.durationMs);
  }
}

Mark.logVoidMarks = false;

export function instant(groupName, functionName, opt_value) {
  const valueString = opt_value === undefined ? '' : ' ' + opt_value;

  /* eslint-disable no-console */
  if (console && console.timeStamp) {
    console.timeStamp(`${groupName} ${functionName}${valueString}`);
  }
  /* eslint-enable no-console */

  analyticsEvent(groupName, functionName, opt_value);
  tsmonEvent(groupName, functionName, opt_value);
}
