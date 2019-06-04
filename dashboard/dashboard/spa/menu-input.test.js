/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import MenuInput from './menu-input.js';
import {STORE} from './element-base.js';
import {UPDATE} from './simple-redux.js';
import {assert} from 'chai';
import {afterRender} from './utils.js';

suite('menu-input', function() {
  teardown(() => {
    for (const child of document.body.querySelectorAll('menu-input')) {
      document.body.removeChild(child);
    }
  });

  test('focus', async function() {
    const xxxInput = document.createElement('menu-input');
    xxxInput.statePath = 'xxx';
    const yyyInput = document.createElement('menu-input');
    yyyInput.statePath = 'yyy';
    await STORE.dispatch(UPDATE('', {
      xxx: MenuInput.buildState({
        label: 'XXX',
        options: new Set([
          'aaa',
          'bbb:ccc',
          'bbb:ddd',
          'bbb:ddd:eee',
          'bbb:ddd:fff',
        ]),
      }),
      yyy: MenuInput.buildState({
        label: 'YYY',
        options: new Set([
          'aaa',
          'bbb:ccc',
          'bbb:ddd',
          'bbb:ddd:eee',
          'bbb:ddd:fff',
        ]),
      }),
    }));
    document.body.appendChild(xxxInput);
    document.body.appendChild(yyyInput);
    await afterRender();
    xxxInput.nativeInput.click();
    assert.isTrue(xxxInput.isFocused);
    assert.isFalse(yyyInput.isFocused);

    yyyInput.nativeInput.click();
    assert.isFalse(xxxInput.isFocused);
    assert.isTrue(yyyInput.isFocused);
  });

  test('inputValue', async function() {
    assert.strictEqual('q', MenuInput.inputValue(true, 'q', undefined));
    assert.strictEqual('', MenuInput.inputValue(false, 'q', undefined));
    assert.strictEqual('', MenuInput.inputValue(false, 'q', []));
    assert.strictEqual('o', MenuInput.inputValue(false, 'q', ['o']));
    assert.strictEqual('[2 selected]', MenuInput.inputValue(
        false, 'q', ['o', 'p']));
  });

  const OPTIONS_3_3_3 = new Set([
    'a0:a1:a2',
    'a0:a1:b2',
    'a0:a1:c2',
    'a0:b1:a2',
    'a0:b1:b2',
    'a0:b1:c2',
    'a0:c1:a2',
    'a0:c1:b2',
    'a0:c1:c2',
    'b0:a1:a2',
    'b0:a1:b2',
    'b0:a1:c2',
    'b0:b1:a2',
    'b0:b1:b2',
    'b0:b1:c2',
    'b0:c1:a2',
    'b0:c1:b2',
    'b0:c1:c2',
    'c0:a1:a2',
    'c0:a1:b2',
    'c0:a1:c2',
    'c0:b1:a2',
    'c0:b1:b2',
    'c0:b1:c2',
    'c0:c1:a2',
    'c0:c1:b2',
    'c0:c1:c2',
  ]);

  function press(key) {
    STORE.dispatch({
      type: MenuInput.reducers.arrowCursor.name,
      statePath: 'test',
      key,
    });
  }

  test('arrowCursor', async function() {
    STORE.dispatch(UPDATE('', {
      test: MenuInput.buildState({options: OPTIONS_3_3_3}),
    }));

    press('ArrowUp');
    assert.strictEqual('', STORE.getState().test.cursor);

    press('ArrowUp');
    assert.strictEqual('', STORE.getState().test.cursor);

    press('ArrowDown');
    assert.strictEqual('', STORE.getState().test.cursor);

    press('ArrowLeft');
    assert.isFalse(STORE.getState().options[1].isExpanded);

    press('ArrowRight');
    assert.isTrue(STORE.getState().options[1].isExpanded);

    press('ArrowRight');
    assert.isTrue(STORE.getState().options[1].isExpanded);

    press('ArrowLeft');
    assert.isFalse(STORE.getState().options[1].isExpanded);
  });
});
