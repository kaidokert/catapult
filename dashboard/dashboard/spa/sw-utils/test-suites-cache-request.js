/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import {KeyValueCacheRequest} from './key-value-cache-request.js';

export default class TestSuitesCacheRequest extends KeyValueCacheRequest {
  async databaseKey() {
    const headers = this.fetchEvent.request.headers;
    const maybeInternal = headers.has('Authorization') ? '_internal' : '';
    return `test_suites${maybeInternal}`;
  }
}
