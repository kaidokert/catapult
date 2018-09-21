/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import {CacheRequestBase} from './cache-request-base.js';

const STORE_SIDS = 'sids';
const TRANSACTION_MODE_READONLY = 'readonly';
const TRANSACTION_MODE_READWRITE = 'readwrite';

// TODO share with utils.js when vulcanize is replaced with webpack
async function sha(s) {
  s = new TextEncoder('utf-8').encode(s);
  const hash = await crypto.subtle.digest('SHA-256', s);
  const view = new DataView(hash);
  let hex = '';
  for (let i = 0; i < view.byteLength; i += 4) {
    hex += ('00000000' + view.getUint32(i).toString(16)).slice(-8);
  }
  return hex;
}

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

  async isKnown_(sid) {
    const database = await this.openIDB_(this.databaseName);
    const transaction = db.transaction([STORE_SIDS], TRANSACTION_MODE_READONLY);
    const sidsStore = transaction.objectStore(STORE_SIDS);
    return sidsStore.get(sid);
  }

  async validate_(sid) {
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

  async write_(sid) {
    const database = await this.openIDB_(this.databaseName);
    const timing = this.time('Write');
    const transaction = db.transaction(
        [STORE_SIDS], TRANSACTION_MODE_READWRITE);
    const sidsStore = transaction.objectStore(STORE_SIDS);
    await sidsStore.put(new Date(), sid);
    timing.end();
  }

  async respond() {
    const body = await this.fetchEvent.request.clone().formData();
    const sid = await sha(decodeURIComponent(body.get('page_state')));
    this.fetchEvent.respondWith(new Response(new Blob(
        [JSON.stringify({sid})], {type: 'application/json'})));
    if (!this.isKnown_(sid)) {
      await this.validate_(sid);
    }
    CacheRequestBase.writer.enqueue(() => this.write_(sid));
  }
}
