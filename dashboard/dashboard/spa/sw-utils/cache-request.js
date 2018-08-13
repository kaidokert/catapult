/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import idb from '/idb/idb.js';
import Timing from './timing.js';


// CacheRequestBase handles all operations for starting a data race between
// IndexedDB the network. This is currently being used to retrieve/cache results
// from the API.
export class CacheRequestBase {
  constructor(request) {
    this.request = request;

    // Start the race right away!
    this._racer = this._race();
  }

  //
  // Public methods (feel free to use or overwrite)
  //

  get timingCategory() {
    // e.g. 'Timeseries', 'Reports', 'FullHistograms'
    throw new Error(`${this.constructor.name} didn't overwrite timingCategory`);
  }

  get url() {
    const url = new URL(this.request.url);
    // Perform any modifications to the URL here.
    return url;
  }

  get databaseName() {
    // e.g. `reports/${this.uniqueIdentifier}`
    throw new Error(`${this.constructor.name} didn't overwrite databaseName`);
  }

  get databaseVersion() {
    // e.g. 1, 2, 3
    throw new Error(
        `${this.constructor.name} didn't overwrite databaseVersion`
    );
  }

  async upgradeDatabase(database) {
    // See https://github.com/jakearchibald/idb#upgrading-existing-db
    throw new Error(
        `${this.constructor.name} didn't overwrite upgradeDatabase`
    );
  }

  async read(database) {
    throw new Error(`${this.constructor.name} didn't overwrite read`);
  }

  async write(database, networkResults) {
    throw new Error(`${this.constructor.name} didn't overwrite write`);
  }

  // Allow child classes to record performance measures to the Chrome DevTools
  // and, if available, to Google Analytics.
  time(action) {
    return new Timing(this.timingCategory, action, this.request.url);
  }

  //
  // Final methods (please do not override)
  //

  [Symbol.asyncIterator]() {
    return this._racer;
  }

  next() {
    return this._racer.next();
  }

  //
  // Private methods
  //

  // Start a race between IndexedDB and the network. The winner yields their
  // result first. The loser's promise will be yielded as well, in case the
  // caller wants it. After a short period of time, results from the network
  // will be written back to IndexedDB.
  get _race() {
    return async function* () {
      // Start the race
      const cache = this._readCache();
      const network = this._readNetwork();

      const winner = await Promise.race([cache, network]);

      // Yield a cached response when the cache hits before the network reponds
      if (winner.name === 'IndexedDB' && winner.result) {
        yield winner;
      }

      // Always yield the network response and write back to cache.
      const res = await network;
      yield res;
      CacheRequestBase.writer.enqueue(this._writeIDB.bind(this), res.result);
    };
  }

  async _readCache() {
    const timing = this.time('Cache');
    const response = await this._readIDB();

    if (response) {
      // If the cache hits, measure how long it took.
      timing.end();
    } else {
      // Otherwise, remove the mark from the browser.
      timing.remove();
    }

    return {
      name: 'IndexedDB',
      result: response,
    };
  }

  async _readNetwork() {
    let timing = this.time('Network');
    const response = await fetch(this.url, { signal: this.request.signal });
    timing.end();

    timing = this.time('Network - Parse JSON');
    const json = await response.json();
    timing.end();

    return {
      name: 'Network',
      result: json,
    };
  }

  // Open a connection to an IndexedDB database. If non-existent, create it.
  async _openIDB(name) {
    const timing = this.time('Open');
    if (!CacheRequestBase.connectionPool[name]) {
      CacheRequestBase.connectionPool[name] = await idb.open(name,
          this.databaseVersion, this.upgradeDatabase);
    }
    timing.end();
    return CacheRequestBase.connectionPool[name];
  }

  // Read any existing data from IndexedDB.
  async _readIDB() {
    const database = await this._openIDB(this.databaseName);
    const timing = this.time('Read');
    const results = await this.read(database);
    timing.end();
    return results;
  }

  // Write results back to IndexedDB
  async _writeIDB(networkResults) {
    const database = await this._openIDB(this.databaseName);
    const timing = this.time('Write');
    const results = await this.write(database, networkResults);
    timing.end();
    return results;
  }
}

// Keep a pool of open connections to reduce the latency of reoccuring opens.
// TODO(Sam): Consider using a priority queue with LRU eviction.
CacheRequestBase.connectionPool = {};

// WritingQueue queues inputs for a write function, which is called in batch
// after no more inputs are added after a given timeout period.
class WritingQueue {
  constructor() {
    this.delayMs = 3000;
    this.timeoutEnabled = true;

    this.queue = [];
    this.timeoutId = undefined; // result of setTimeout
  }

  enqueue(writeFunc, ...writeFuncArgs) {
    this.queue.push([writeFunc, writeFuncArgs]);

    if (!this.timeoutEnabled) return;

    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
    }

    this.timeoutId = setTimeout(this.flush.bind(this), this.delayMs);
  }

  flush() {
    const promises = this.queue.map(([writeFunc, args]) => writeFunc(...args));
    this.queue = [];
    return promises;
  }
}

// Delay writes for increased read performance.
CacheRequestBase.writer = new WritingQueue();


//
// Utility functions for testing
//


// Delete the database corresponding to the specified request.
export async function deleteDatabaseForTest(databaseName) {
  if (databaseName in CacheRequestBase.connectionPool) {
    await CacheRequestBase.connectionPool[databaseName].close();
    delete CacheRequestBase.connectionPool[databaseName];
  }

  await idb.delete(databaseName);
}

// Disable the timeout-based writing mechanism for the WritingQueue.
export function disableAutomaticWritingForTest() {
  CacheRequestBase.writer.timeoutEnabled = false;
}

// Flush the IndexedDB WritingQueue by executing everything on queue.
export function flushWriterForTest() {
  if (CacheRequestBase.writer.timeoutId) {
    clearTimeout(CacheRequestBase.writer.timeoutId);
  }

  const tasks = CacheRequestBase.writer.flush();
  return Promise.all(tasks);
}


export default {
  deleteDatabaseForTest,
  disableAutomaticWritingForTest,
  flushWriterForTest,
  CacheRequestBase,
};
