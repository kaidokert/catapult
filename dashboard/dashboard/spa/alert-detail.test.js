/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import AlertDetail from './alert-detail.js';
import {UPDATE} from './simple-redux.js';
import {afterRender, animationFrame, timeout} from './utils.js';
import {assert} from 'chai';

suite('alert-detail', function() {
  async function fixture() {
    const ad = document.createElement('alert-detail');
    ad.statePath = 'test';
    await ad.dispatch(UPDATE('test', {}));
    document.body.appendChild(ad);
    await afterRender();
    return ad;
  }

  test('', async function() {
    const ad = await fixture();
    this.timeout(1e6); await timeout(9e5);
  });
});
