/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import ElementBase from 'element-base.js';

Mocha.beforeEach(() => {
  ElementBase.resetStoreForTest();
});

const testsContext = require.context('.', true, /\.test\.js$/);
testsContext.keys().forEach(testsContext);
