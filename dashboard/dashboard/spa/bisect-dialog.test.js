/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import {assert} from 'chai';
import BisectDialog from './bisect-dialog.js';
import {timeout} from './utils.js';

suite('bisect-dialog', function() {
  async function fixture() {
    const dt = document.createElement('bisect-dialog');
    dt.statePath = 'test';
    dt.dispatch(CHAIN(
        ENSURE('test'),
        UPDATE('test', DetailsTable.buildState({}))));
    document.body.appendChild(dt);
    await afterRender();
  }

  let originalFetch;
  setup(() => {
    window.IS_DEBUG = true;

    originalFetch = window.fetch;
    window.fetch = async(url, options) => {
      return {
        ok: true,
        async json() {
        },
      };
    };
  });

  teardown(() => {
    for (const child of document.body.children) {
      if (!child.matches('bisect-dialog')) continue;
      document.body.removeChild(child);
    }
    window.fetch = originalFetch;
  });

  test('submit', async function() {
    const bd = await fixture();
    this.timeout(1e6); await timeout(9e5);
  });
});
