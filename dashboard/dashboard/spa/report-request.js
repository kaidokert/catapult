/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import RequestBase from './request-base.js';

export default class ReportRequest extends RequestBase {
  constructor(options) {
    super(options);
    this.name_ = options.name;
    this.method_ = 'POST';
    this.body_ = new FormData();
    this.body_.set('id', options.id);
    this.body_.set('modified', options.modified.getTime());
    this.body_.set('revisions', options.revisions);
  }

  channelErrorMessage_(err) {
    return `Error loading report: ${err.message}`;
  }

  get url_() {
    return ReportRequest.URL;
  }
}

ReportRequest.URL = '/api/report/generate';
