/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

// import ElementBase from './element-base.js';

export class BatchIterator {
  async* foo() {
  }
}

Mocha.beforeEach(() => {
  console.log(BatchIterator);
  // ElementBase.resetStoreForTest();
});

const testsContext = require.context('.', true, /\.test\.js$/);
testsContext.keys().forEach(testsContext);
