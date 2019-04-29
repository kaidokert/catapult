/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import RequestBase from './request-base.js';

export default class ReportNamesRequest extends RequestBase {
  constructor(options = {}) {
    super(options);
    this.method_ = 'POST';
  }

  get url_() {
    return ReportNamesRequest.URL;
  }

  fetchErrorMessage_(response) {
    return `Error loading report names: ` +
      `${response.status} ${response.statusText}`;
  }

  jsonErrorMessage_(err) {
    return `Error loading report names: ` +
      `${err.message}`;
  }

  postProcess_(json) {
    if (json.error) throw new Error(json.error);
    return json.map(info => {
      return {...info, modified: new Date(info.modified)};
    });
  }
}
ReportNamesRequest.URL = '/api/report/names';
