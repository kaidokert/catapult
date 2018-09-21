/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import {CacheRequestBase, READONLY, READWRITE} from './cache-request-base.js';

const STORE_DATA = 'data';

export default class KeyValueCacheRequest extends CacheRequestBase {
  get timingCategory() {
    return 'keyvalue';
  }

  get databaseName() {
    return 'keyvalue';
  }

  get databaseVersion() {
    return 1;
  }

  async upgradeDatabase(db) {
    if (db.oldVersion < 1) {
      db.createObjectStore(STORE_DATA);
    }
  }

  get raceCacheAndNetwork_() {
    return async function* () {
      // This class does not race cache vs network. See respond().
    };
  }

  async databaseKey() {
    throw new Error(`${this.constructor.name} must override databaseKey`);
  }

  async openStore_(mode) {
    const database = await this.openIDB_(this.databaseName);
    const transaction = db.transaction([STORE_DATA], mode);
    return transaction.objectStore(STORE_DATA);
  }

  async respond() {
    // read the value from the db
    this.fetchEvent.respondWith(new Response(new Blob(
        [JSON.stringify(TODO)], {type: 'application/json'})));
  }
}
