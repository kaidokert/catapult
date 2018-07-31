/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import idb from '/idb/idb.js';
import Mark from './mark.js';


// IDBRace handles all operations for starting a data race between IndexedDB the
// network. This is currently being used to retrieve/cache results from the API.
export class IDBRace {
  constructor(request) {
    this.request = request;

    // Start the race right away!
    this._racer = this._race();
  }

  //
  // Public methods (feel free to use or overwrite)
  //

  get markCategory() {
    // e.g. 'Timeseries', 'Reports', 'FullHistograms'
    throw new Error(`${this.constructor.name} didn't overwrite markCategory`);
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
  mark(action) {
    return new Mark(this.markCategory, action, this.request.url);
  }

  //
  // Private methods (please do not overwrite)
  //

  [Symbol.asyncIterator]() {
    return this._racer;
  }

  next() {
    return this._racer.next();
  }

  // Start a race between IndexedDB and the network. The winner yields their
  // result first. The loser's promise will be yielded as well, in case the
  // caller wants it. After a short period of time, results from the network
  // will be written back to IndexedDB.
  get _race() {
    return async function* () {
      const cache = (async() => {
        const mark = this.mark('Cache');
        const response = await this._read();

        if (response) {
          // If the cache hits, measure how long it took.
          mark.end();
        } else {
          // Otherwise, remove the mark from the browser.
          mark.remove();
        }

        return {
          name: 'IndexedDB',
          result: response,
        };
      })();

      const network = (async() => {
        let mark = this.mark('Network');
        const response = await fetch(this.url, { signal: this.request.signal });
        mark.end();

        mark = this.mark('Network - Parse JSON');
        const json = await response.json();
        mark.end();

        return {
          name: 'Network',
          result: json,
        };
      })();

      // Start the race
      const winner = await Promise.race([cache, network]);

      // Yield an empty Response to signal that data is coming in object form
      // (rather than in Response format).
      const blob = new Blob([JSON.stringify({}, null, 2)], {
        type: 'application/json',
      });
      yield {
        name: 'Fake',
        result: new Response(blob)
      };

      let loser;
      switch (winner.name) {
        case 'IndexedDB':
          if (winner.result) yield winner;
          loser = await network;
          yield loser;
          IDBRace.writer.enqueue(this._write.bind(this), loser.result);
          break;

        case 'Network':
          yield winner;
          // TODO(Sam): Return cache response once network requests are tuned to
          // avoid over-fetching the data we already have in cache.
          IDBRace.writer.enqueue(this._write.bind(this), winner.result);
          break;

        default:
          throw new Error(`${winner.name} should not be in the race`);
      }
    };
  }

  // Open a connection to an IndexedDB database. If it does not exist,
  // create it.
  async _openDatabase(name) {
    const mark = this.mark('Open');
    if (!IDBRace.connectionPool[name]) {
      IDBRace.connectionPool[name] = await idb.open(name, this.databaseVersion,
          this.upgradeDatabase);
    }
    mark.end();
    return IDBRace.connectionPool[name];
  }

  // Read any existing data from IndexedDB.
  async _read() {
    const database = await this._openDatabase(this.databaseName);
    const mark = this.mark('Read');
    const results = await this.read(database);
    return results;
  }

  // Write results back to IndexedDB
  async _write(networkResults) {
    const database = await this._openDatabase(this.databaseName);
    const mark = this.mark('Write');
    const results = await this.write(database, networkResults);
    mark.end();
    return results;
  }
}

// Keep a pool of open connections to reduce the latency of reoccuring opens.
// TODO(Sam): Consider using a priority queue with LRU eviction.
IDBRace.connectionPool = {};

// DebouncedWriter queues inputs for a write function, which is called in batch
// after no more inputs are added after a given timeout period.
class DebouncedWriter {
  constructor() {
    this.delay = 3000;
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

    this.timeoutId = setTimeout(() => {
      for (const [writeFunc, args] of this.queue) {
        writeFunc(...args);
      }
      this.queue = [];
    }, this.delay);
  }
}

// Delay writes for increased read performance.
IDBRace.writer = new DebouncedWriter();


//
// Utility functions for testing
//


// Delete the database corresponding to the specified request.
export async function deleteDatabaseForTest(databaseName) {
  if (databaseName in IDBRace.connectionPool) {
    await IDBRace.connectionPool[databaseName].close();
    delete IDBRace.connectionPool[databaseName];
  }

  await idb.delete(databaseName);
}

// Disable the timeout-based writing mechanism for the DebouncedWriter.
export function disableAutomaticWritingForTest() {
  IDBRace.writer.timeoutEnabled = false;
}

// Flush the IndexedDB DebouncedWriter by executing everything on queue.
export function flushWriterForTest() {
  if (IDBRace.writer.timeoutId) {
    clearTimeout(IDBRace.writer.timeoutId);
  }

  const promises = IDBRace.writer.queue.map(
      ([writeFunc, args]) => writeFunc(...args)
  );
  IDBRace.writer.queue = [];

  return Promise.all(promises);
}


export default {
  deleteDatabaseForTest,
  disableAutomaticWritingForTest,
  flushWriterForTest,
  IDBRace,
};
