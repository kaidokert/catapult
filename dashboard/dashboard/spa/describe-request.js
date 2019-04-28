/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import RequestBase from './request-base.js';

export default class DescribeRequest extends RequestBase {
  constructor(options) {
    super(options);
    this.method_ = 'POST';
    this.body_ = new FormData();
    this.body_.set('test_suite', options.suite);
  }

  get url_() {
    return DescribeRequest.URL;
  }

  fetchErrorMessage_(response) {
    const suite = this.body_.get('test_suite');
    return `Error describing suite "${suite}": ` +
      `${response.status} ${response.statusText}`;
  }

  postProcess_(response, isFromChannel = false) {
    if (!response) throw new Error('null descriptor');
    if (response.error) throw new Error(response.error);
    if (!descriptor.bots) throw new Error('missing bots');
    if (!descriptor.bots.length) throw new Error('empty bots');
    if (!descriptor.measurements) throw new Error('missing measurements');
    if (!descriptor.measurements.length) throw new Error('empty measurements');
    return response;
  }

  jsonErrorMessage_(err) {
    const suite = this.body_.get('test_suite');
    return `Error describing suite "${suite}": ` +
      `${err.message}`;
  }

  static mergeDescriptor(merged, descriptor) {
    for (const bot of (descriptor.bots || [])) merged.bots.add(bot);
    for (const measurement of (descriptor.measurements || [])) {
      merged.measurements.add(measurement);
    }
    for (const c of (descriptor.cases || [])) {
      merged.cases.add(c);
    }
    for (const [tag, cases] of Object.entries(descriptor.caseTags || {})) {
      if (!merged.caseTags.has(tag)) {
        merged.caseTags.set(tag, new Set());
      }
      for (const c of cases) {
        merged.caseTags.get(tag).add(c);
      }
    }
  }
}
DescribeRequest.URL = '/api/describe';
