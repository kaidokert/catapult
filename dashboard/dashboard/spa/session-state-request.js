/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import RequestBase from './request-base.js';

export default class SessionStateRequest extends RequestBase {
  constructor(options) {
    super(options);
    this.sessionId_ = options.sessionId;
  }

  fetchErrorMessage_(response) {
    return `Error loading session state: ` +
      `${response.status} ${response.statusText}`;
  }

  get url_() {
    return `${SessionStateRequest.URL}?v2=true&sid=${this.sessionId_}`;
  }
}
SessionStateRequest.URL = '/short_uri';
