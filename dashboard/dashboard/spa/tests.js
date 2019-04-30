/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import 'bower_components/webcomponentsjs/webcomponents-loader.js';
import ElementBase from './element-base.js';

Mocha.before(async function() {
  const deps = document.createElement('link');
  deps.rel = 'import';
  deps.href = '/dashboard/spa/dependencies.html';
  document.head.appendChild(deps);
});

Mocha.beforeEach(async function() {
  ElementBase.resetStoreForTest();
});

const testsContext = require.context('.', true, /\.test\.js$/);
testsContext.keys().forEach(testsContext);
