/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import * as testUtils from './cache-request-base.js';
import idb from 'idb';
import {NotesCacheRequest} from './notes-cache-request.js';
import {assert} from 'chai';

suite('NotesCacheRequest', function() {
  class MockFetchEvent {
    constructor(parameters) {
      this.request = {
        url: 'http://example.com/api/notes',
        clone() {
          return this;
        },
        async formData() {
          return new Map([
            ['suite', ''],
            ['measurement', ''],
            ['bot', ''],
            ['case', ''],
          ]);
        }
      };
    }

    waitUntil() {
    }
  }

  test('cached then network', async function() {
    const db = await idb.open('notes////', 1, db => {
      db.createObjectStore('notes');
    });
    const transaction = db.transaction(['notes'], 'readwrite');
    const dataStore = transaction.objectStore('notes');
    const note = {
      key: 'key',
      min_revision: 10,
      max_revision: 20,
      suite: '',
      measurement: '',
      bot: '',
      case: '',
      text: 'cached',
      author: 'you@here.com',
      modified: new Date(),
    };
    dataStore.put(note, 'key');
    await transaction.complete;

    note.modified = new Date(1 + note.modified);
    note.text = 'network';
    window.fetch = async() => testUtils.jsonResponse([note]);

    const request = new NotesCacheRequest(new MockFetchEvent());
    const results = [];
    for await (const result of request.generateResults()) {
      results.push(result);
    }
    assert.lengthOf(results, 2);
    assert.lengthOf(results[0], 1);
    assert.lengthOf(results[1], 1);
    assert.strictEqual('cached', results[0][0].text);
    assert.strictEqual('network', results[1][0].text);
  });
});
