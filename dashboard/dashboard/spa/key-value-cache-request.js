/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import {CacheRequestBase, READONLY, READWRITE} from './cache-request-base.js';

const STORE_DATA = 'data';
const EXPIRATION_KEY = '_expiresTime';

export default class KeyValueCacheRequest extends CacheRequestBase {
  constructor(fetchEvent) {
    super(fetchEvent);
    this.databaseKeyPromise_ = this.getDatabaseKey();
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

  get expirationMs() {
    return 20 * 60 * 60 * 1000;
  }

  async getDatabaseKey() {
    throw new Error(`${this.constructor.name} must override getDatabaseKey`);
  }

  async writeDatabase({key, value}) {
    const db = await this.databasePromise;
    const transaction = db.transaction([STORE_DATA], READWRITE);
    const dataStore = transaction.objectStore(STORE_DATA);
    const expiration = new Date(new Date().getTime() + this.expirationMs);
    dataStore.put({value, [EXPIRATION_KEY]: expiration.toISOString()}, key);
    await transaction.complete;
  }

  async readDatabase_(key) {
    const db = await this.databasePromise;
    const transaction = db.transaction([STORE_DATA], READONLY);
    const dataStore = transaction.objectStore(STORE_DATA);
    return await dataStore.get(key);
  }

  async getResponse() {
    const key = await this.databaseKeyPromise_;
    const entry = await this.readDatabase_(key);
    if (entry && (new Date(entry[EXPIRATION_KEY]) > new Date())) {
      return entry.value;
    }

    const otherRequest = await this.findInProgressRequest(async other =>
      ((await other.databaseKeyPromise_) === key));
    if (otherRequest) {
      return await otherRequest.responsePromise;
    }

    const response = await this.time('fetch').wait(
        fetch(this.fetchEvent.request));
    const value = await response.json();
    this.scheduleWrite({key, value});
    return value;
  }
}
