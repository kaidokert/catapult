/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import AlertDetail from './alert-detail.js';
import ExistingBugRequest from './existing-bug-request.js';
import NewBugRequest from './new-bug-request.js';
import findElements from './find-elements.js';
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

  let existingBugPromise;
  let newBugPromise;
  let originalFetch;
  let existingBugBody;
  let newBugBody;
  setup(() => {
    window.IS_DEBUG = true;
    originalFetch = window.fetch;
    window.fetch = async(url, options) => {
      return {
        ok: true,
        async json() {
          if (url === NewBugRequest.URL) {
            await newBugPromise;
            newBugBody = new Map(options.body);
            return {bug_id: 57};
          }
          if (url === ExistingBugRequest.URL) {
            await existingBugPromise;
            existingBugBody = new Map(options.body);
            return {};
          }
        },
      };
    };
  });
  teardown(() => {
    for (const child of document.body.children) {
      if (!child.matches('alert-detail')) continue;
      document.body.removeChild(child);
    }
    window.fetch = originalFetch;
  });

  test('unassign', async function() {
    const ad = await fixture();
    ad.dispatch(UPDATE(ad.statePath, {
      key: 'test unassign',
      bugId: 1,
    }));
    await afterRender();
    const unassign = findElements(ad, e =>
      e.matches('raised-button') && /Unassign/.test(e.textContent))[0];
    unassign.click();
    await afterRender();
    assert.strictEqual(0, ad.bugId);
    assert.strictEqual('0', existingBugBody.get('bug'));
  });

  test('ignore', async function() {
    const ad = await fixture();
    ad.dispatch(UPDATE(ad.statePath, {
      key: 'test ignore',
      bugId: 0,
    }));
    await afterRender();
    const ignore = findElements(ad, e =>
      e.matches('raised-button') && /Ignore/.test(e.textContent))[0];
    ignore.click();
    await afterRender();
    assert.strictEqual(-2, ad.bugId);
    assert.strictEqual('-2', existingBugBody.get('bug'));
  });

  test('new bug', async function() {
    const ad = await fixture();
    ad.dispatch(UPDATE(ad.statePath, {
      key: 'test new bug',
      bugId: 0,
      bugComponents: [],
      bugLabels: [],
    }));
    await afterRender();
    const newBug = findElements(ad, e =>
      e.matches('raised-button') && /New Bug/.test(e.textContent))[0];
    newBug.click();
    await afterRender();
    let resolveNewBug;
    newBugPromise = new Promise(resolve => {
      resolveNewBug = resolve;
    });
    const submit = findElements(ad, e =>
      e.matches('raised-button') && /Submit/.test(e.textContent))[0];
    submit.click();
    await afterRender();
    assert.strictEqual('[creating]', ad.bugId);
    resolveNewBug();
    await afterRender();
    assert.strictEqual(57, ad.bugId);
    assert.strictEqual(ad.key, newBugBody.get('key'));
  });

  test('existing bug', async function() {
    const ad = await fixture();
    ad.dispatch(UPDATE(ad.statePath, {
      key: 'test existing bug',
      bugId: 0,
      bugComponents: [],
      bugLabels: [],
    }));
    await afterRender();
    const existingBug = findElements(ad, e =>
      e.matches('raised-button') && /Existing Bug/.test(e.textContent))[0];
    existingBug.click();
    await afterRender();
    ad.dispatch(UPDATE('test.existingBug', {bugId: '123456'}));
    await afterRender();
    assert.strictEqual(0, ad.bugId);
    let resolveExistingBug;
    existingBugPromise = new Promise(resolve => {
      resolveExistingBug = resolve;
    });
    const menu = findElements(ad, e => e.matches('triage-existing'))[0];
    const submit = findElements(menu, e =>
      e.matches('raised-button') && /Submit/.test(e.textContent))[0];
    submit.click();
    await afterRender();
    assert.strictEqual('123456', ad.bugId);
    resolveExistingBug();
    await afterRender();
    assert.strictEqual(ad.key, existingBugBody.get('key'));
  });
});
