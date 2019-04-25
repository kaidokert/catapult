/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import '/@chopsui/tsmon-client/tsmon-client.js';
import {simpleGUID} from './utils.js';

const TSMonClient = window.chops.tsmon.TSMonClient;
const TS_MON_JS_PATH = '/_/jstsmon.do';
const TS_MON_CLIENT_GLOBAL_NAME = '__tsMonClient';

class Mark {
  constructor(groupName, functionName, opt_timestamp) {
    this.groupName_ = groupName;
    this.functionName_ = functionName;
    const guid = simpleGUID();
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
    } else if (Metrics.logVoidMarks && !(window.ga instanceof Function)) {
      // eslint-disable-next-line no-console
      console.log('void mark',
          this.groupName, this.functionName, this.durationMs);
    }

    if (!(window.ga instanceof Function)) return;
    // Google Analytics
    ga('send', {
      hitType: 'event',
      eventCategory: this.groupName,
      eventAction: this.functionName,
      eventValue: this.durationMs,
    });
  }
}

function rand32() {
  const randomvalues = new Uint32Array(1);
  window.crypto.getRandomValues(randomvalues);
  return randomvalues[0].toString(32);
}

export class Metrics extends TSMonClient {
  constructor() {
    super(TS_MON_JS_PATH);
    this.clientId = rand32();
  }

  static mark(groupName, functionName, opt_timestamp) {
    return new Mark(groupName, functionName, opt_timestamp);
  }

  static instant(groupName, functionName, opt_value) {
    const valueString = opt_value === undefined ? '' : ' ' + opt_value;

    /* eslint-disable no-console */
    if (console && console.timeStamp) {
      console.timeStamp(`${groupName} ${functionName}${valueString}`);
    }
    /* eslint-enable no-console */

    // Google Analytics
    if (window && window.ga instanceof Function) {
      ga('send', {
        hitType: 'event',
        eventCategory: groupName,
        eventAction: functionName,
        eventValue: opt_value,
      });
    }
  }

  static getCurrentTimeMs() {
    try {
      return performance.now();
    } catch (error) {}
    return 0;
  }
}

Metrics.logVoidMarks = false;
