/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import {CacheRequestBase} from './cache-request-base.js';

const STORE_SIDS = 'sids';
const TRANSACTION_MODE_READONLY = 'readonly';
const TRANSACTION_MODE_READWRITE = 'readwrite';

export default class SessionIdCacheRequest extends CacheRequestBase {
  get timingCategory() {
    return 'short_uri';
  }

  get databaseName() {
    return 'short_uri';
  }

  get databaseVersion() {
    return 1;
  }

  async upgradeDatabase(db) {
    if (db.oldVersion < 1) {
      db.createObjectStore(STORE_SIDS);
    }
  }

  get raceCacheAndNetwork_() {
    return async function* () {
      // This class does not race cache vs network. See respond().
    };
  }

  async respond() {
    let timing = this.time('sha');
    // TODO copy sha() to sw-utils
    // TODO pass sessionState from fetchEvent to sha()
    const sid = await sha();
    timing.end();

    // TODO Check if sid is in idb
    const database = await this.openIDB_(this.databaseName);
    const transaction = db.transaction([STORE_SIDS], TRANSACTION_MODE_READONLY);

    this.fetchEvent.respondWith(new Response(new Blob(
        [JSON.stringify({sid})], {type: 'application/json'})));

    timing = this.time('Network');
    const response = await fetch(this.fetchEvent.request);
    timing.end();

    timing = this.time('Parse JSON');
    const json = await response.json();
    timing.end();

    if (json.sid !== sid) {
      throw new Error(`short_uri expected ${sid} actual ${json.sid}`);
    }
  }
}
