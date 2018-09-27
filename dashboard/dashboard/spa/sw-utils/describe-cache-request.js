/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import KeyValueCacheRequest from './key-value-cache-request.js';

// TODO fetch fresh descriptors after 20 hours

export default class DescribeCacheRequest extends KeyValueCacheRequest {
  async databaseKey() {
    const headers = this.fetchEvent.request.headers;
    const maybeInternal = headers.has('Authorization') ? '_internal' : '';
    const body = await this.fetchEvent.request.clone().formData();
    const testSuite = body.get('test_suite');
    return `describe_${testSuite}${maybeInternal}`;
  }
}
