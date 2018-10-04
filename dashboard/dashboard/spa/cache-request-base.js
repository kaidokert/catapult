/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import idb from '/idb/idb.js';
import analytics from './google-analytics.js';
import Timing from './timing.js';

// Transaction modes
export const READONLY = 'readonly';
export const READWRITE = 'readwrite';

// Wrap an object in a JSON Blob Response to pass to fetchEvent.respondWith().
export const jsonResponse = response => new Response(new Blob(
    [JSON.stringify(response)], {type: 'application/json'}));

const IN_PROGRESS_REQUESTS = [];

export class CacheRequestBase {
  constructor(fetchEvent) {
    IN_PROGRESS_REQUESTS.push(this);
    this.fetchEvent = fetchEvent;
    this.url = new URL(this.fetchEvent.request.url);
    this.databasePromise_ = undefined;
    this.responsePromise_ = undefined;
    this.writing_ = false;
  }

  get databasePromise() {
    if (!this.databasePromise_) this.databasePromise_ = this.openDatabase_();
    return this.databasePromise_;
  }

  get responsePromise() {
    if (!this.responsePromise_) this.responsePromise_ = this.getResponse();
    return this.responsePromise_;
  }

  time(action) {
    return new Timing(this.constructor.name, action, this.url);
  }

  // The page may send multiple requests for the same data without waiting for
  // completion, or requests may overlap in complex ways. Subclasses can avoid
  // forwarding identical/overlapping requests to the backend using this method
  // to find other in-progress requests and wait for their responses.
  async findInProgressRequest(filter) {
    for (const other of IN_PROGRESS_REQUESTS) {
      if ((other !== this) &&
          (other.url.pathname === this.url.pathname) &&
          (await filter(other))) {
        return other;
      }
    }
  }

  // Subclasses may override this to read a database and/or fetch() from the
  // backend.
  async getResponse() {
    return null;
  }

  respond() {
    this.fetchEvent.respondWith(this.responsePromise.then(response => {
      if (!this.writing_) {
        IN_PROGRESS_REQUESTS.splice(IN_PROGRESS_REQUESTS.indexOf(this), 1);
      }
      return jsonResponse(response);
    }));
  }

  async writeDatabase(options) {
    throw new Error(`${this.constructor.name} must override writeDatabase`);
  }

  // getResponse() should call this method.
  scheduleWrite(options) {
    this.writing_ = true;
    let complete;
    this.fetchEvent.waitUntil(new Promise(resolve => {
      complete = resolve;
    }));

    const queueTiming = this.time('scheduleWrite');
    DELAYED_TASK_QUEUE.schedule(async() => {
      queueTiming.end();
      const writeTiming = this.time('writeDatabase');
      try {
        await this.writeDatabase(options);
      } finally {
        writeTiming.end();
        IN_PROGRESS_REQUESTS.splice(IN_PROGRESS_REQUESTS.indexOf(this), 1);
        complete();
        this.writing_ = false;
        this.databasePromise_ = undefined;
      }
    });
  }

  get databaseName() {
    // e.g. `reports/${this.uniqueIdentifier}`
    throw new Error(`${this.constructor.name} must override databaseName`);
  }

  get databaseVersion() {
    // e.g. 1, 2, 3
    throw new Error(
        `${this.constructor.name} must override databaseVersion`);
  }

  async upgradeDatabase(database) {
    // See https://github.com/jakearchibald/idb#upgrading-existing-db
    throw new Error(
        `${this.constructor.name} must override upgradeDatabase`);
  }

  async openDatabase_() {
    if (!CONNECTION_POOL.has(this.databaseName)) {
      const connection = await idb.open(
          this.databaseName, this.databaseVersion,
          db => this.upgradeDatabase(db));
      CONNECTION_POOL.set(this.databaseName, connection);
    }
    return CONNECTION_POOL.get(this.databaseName);
  }
}

const CONNECTION_POOL = new Map();

const DELAYED_TASK_QUEUE = {
  queue_: [],
  flushing_: false,
  timeoutId_: undefined,

  schedule(task, delayMs = 3000) {
    this.queue_.push(task);
    if (!this.timeoutEnabled) return;
    if (this.timeoutId_) clearTimeout(this.timeoutId_);
    this.timeoutId_ = setTimeout(this.flush.bind(this), delayMs);
  },

  async flush() {
    if (this.timeoutId_) clearTimeout(this.timeoutId_);
    if (this.flushing_) return;
    this.flushing_ = true;

    while (this.queue_.length) {
      const task = this.queue_.shift();
      try {
        await task();
      } catch (err) {
        // eslint-disable-next-line no-console
        console.error(err);
        analytics.sendException(err);
      }
    }

    this.flushing_ = false;

    // Record the size of the connection pool to see if LRU eviction would be
    // necessary for the future.
    analytics.sendEvent(
        'IndexedDB', 'Connection Pool Size', CONNECTION_POOL.size);
  },
};

export async function flushWriterForTest() {
  await DELAYED_TASK_QUEUE.flush();
}

export default {
  CacheRequestBase,
  READONLY,
  READWRITE,
  flushWriterForTest,
  jsonResponse,
};
