/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import {CacheRequestBase, READONLY, READWRITE} from './cache-request-base.js';

const STORE_DATA = 'data';
const EXPIRATION_MS = 20 * 60 * 60 * 1000;

export default class NotesCacheRequest extends CacheRequestBase {
  get isAuthorized() {
    return this.fetchEvent.request.headers.has('Authorization');
  }

  get databaseName() {
    return this.databaseName_;
  }

  get databaseVersion() {
    return 1;
  }

  async upgradeDatabase(db) {
    if (db.oldVersion < 1) {
      db.createObjectStore(STORE_DATA);
    }
  }

  async writeDatabase({key, value}) {
    const transaction = await this.transaction([STORE_DATA], READWRITE);
    const dataStore = transaction.objectStore(STORE_DATA);
    const expiration = new Date(new Date().getTime() + EXPIRATION_MS);
    dataStore.put({value, expiration: expiration.toISOString()}, key);
    await transaction.complete;
  }

  async readDatabase_(key) {
    const transaction = await this.transaction([STORE_DATA], READONLY);
    const dataStore = transaction.objectStore(STORE_DATA);
    return await dataStore.get(key);
  }

  async getResponse() {
    const body = await this.fetchEvent.request.clone().formData();
    const text = body.get('text');
    if (text) {
      // This request is creating or editing a note, so forward it to the server
      // as-is.
      return await fetch(this.fetchEvent.request);
    }

    this.databaseName_ = NotesCacheRequest.databaseName({
      suite: body.get('suite'),
      measurement: body.get('measurement'),
      bot: body.get('bot'),
      case: body.get('case'),
    });
    // read all notes in the revision range.

    const range = IDBKeyRange.bound(
        this.revisionRange_.min, this.revisionRange_.max);
    dataStore.iterateCursor(range, cursor => {
      if (!cursor) return;
      dataPoints.push(cursor.value);
      cursor.continue();
    });
  }

  static databaseName({suite, measurement, bot, case: cas}) {
    return `notes/${suite}/${measurement}/${bot}/${cas}`;
  }
}
