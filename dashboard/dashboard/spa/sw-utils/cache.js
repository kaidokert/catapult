/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import idb from '/idb/idb.js';
import Mark from './mark.js';
import Range from './range.js';
import { getColumnsByLevelOfDetail } from './level-of-detail.js';


//
// Race
//


// Start a race between IndexedDB and the network. The winner returns their
// result first. The loser's promise will be returned in case the caller wants
// it. After a short period of time, results from the network will be written
// back to IndexedDB.
export async function* race(request) {
  const requestParams = parseRequest(request);

  const cache = (async() => {
    const mark = new Mark('Service Worker', 'Load - IDB', requestParams.url);
    const response = await read(requestParams);

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
    const url = new URL(requestParams.url);

    // Transform the `levelOfDetail` header to `columns`
    url.searchParams.delete('levelOfDetail');
    url.searchParams.delete('columns');
    url.searchParams.set('columns', requestParams.columns);

    // TODO(Sam): Remove this once CL 1146066 is merged
    // https://chromium-review.googlesource.com/c/catapult/+/1146066
    url.searchParams.set('columns', requestParams.columns);

    let mark = new Mark('Service Worker', 'Load - Network', requestParams.url);
    const response = await fetch(url, { signal: requestParams.signal });
    mark.end();

    mark = new Mark('Service Worker', 'Parse - JSON', requestParams.url);
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
      writer.enqueue(requestParams, loser.result);
      break;

    case 'Network':
      yield winner;
      // TODO(Sam): Return cache response once network requests are tuned to
      // avoid over-fetching the data we already have in cache.
      writer.enqueue(requestParams, winner.result);
      break;

    default:
      throw new Error(`${winner.name} should not be in the race`);
  }
}


//
// Open
//


// Keep a pool of open connections to reduce the latency of reoccuring opens.
// TODO(Sam): Consider using a priority queue with LRU eviction.
const connectionPool = {};

// Open a connection to an IndexedDB database. If it does not exist, create it.
async function openDatabase(key) {
  const mark = new Mark('IndexedDB', 'Open', key);
  if (!connectionPool[key]) {
    connectionPool[key] = await idb.open(key, 1, upgradeDB => {
      if (upgradeDB.oldVersion === 0) {
        upgradeDB.createObjectStore('dataPoints');
        upgradeDB.createObjectStore('metadata');
        upgradeDB.createObjectStore('ranges');
      }
    });
  }

  const connection = connectionPool[key];
  mark.end();
  return connection;
}


//
// Read
//

// Read any existing data from IndexedDB.
async function read(requestParams) {
  const {
    columns,
    key,
    levelOfDetail,
    maxRevision,
    minRevision,
  } = requestParams;

  const db = await openDatabase(key);
  const transaction = db.transaction(
      ['ranges', 'dataPoints', 'metadata'],
      'readonly'
  );

  const dataPointsPromise = getDataPoints(
      transaction, minRevision, maxRevision, key);
  const [
    improvementDirection,
    units,
    ranges,
  ] = await Promise.all([
    getMetadata(transaction, 'improvement_direction', key),
    getMetadata(transaction, 'units', key),
    getRanges(transaction, levelOfDetail, key),
  ]);

  //
  // Ranges
  //

  let mark = new Mark('IndexedDB', 'Read - Range check', key);

  if (!ranges) {
    // Nothing has been cached for this level-of-detail yet.
    return;
  }

  const requestedRange = Range.fromExplicitRange(minRevision, maxRevision);

  if (!requestedRange.isEmpty) {
    // Determine if any cached data ranges intersect with the requested range.
    const rangeIndex = ranges
        .map(range => Range.fromDict(range))
        .findIndex(range => {
          const intersection = range.findIntersection(requestedRange);
          return !intersection.isEmpty;
        });

    if (rangeIndex === -1) {
      // IndexedDB does not contain any relevant data for the requested range.
      return;
    }
  }

  mark.end();

  //
  // Datapoints
  //

  const dataPoints = await dataPointsPromise;

  // Denormalize requested columns to an array with the same order as
  // requested.
  mark = new Mark('IndexedDB', 'Read - Denormalize', key);
  const denormalizedDatapoints = [];
  for (const dataPoint of dataPoints) {
    const result = [];
    for (const column of columns) {
      result.push(dataPoint[column]);
    }
    denormalizedDatapoints.push(result);
  }
  mark.end();

  return {
    improvement_direction: improvementDirection,
    units,
    data: denormalizedDatapoints,
  };
}

async function getMetadata(transaction, key) {
  const mark = new Mark('IndexedDB', 'Read - Metadata', key);
  const metadataStore = transaction.objectStore('metadata');
  const result = await metadataStore.get(key);
  mark.end();
  return result;
}

async function getRanges(transaction, levelOfDetail, key) {
  const mark = new Mark('IndexedDB', 'Read - Ranges', key);
  const rangeStore = transaction.objectStore('ranges');
  const ranges = await rangeStore.get(levelOfDetail);
  mark.end();
  return ranges;
}

async function getDataPoints(transaction, minRevision, maxRevision, key) {
  const mark = new Mark('IndexedDB', 'Read - Datapoints', key);
  const dataStore = transaction.objectStore('dataPoints');
  if (!minRevision || !maxRevision) {
    const dataPoints = await dataStore.getAll();
    return dataPoints;
  }

  const dataPoints = [];
  const range = IDBKeyRange.bound(minRevision, maxRevision);
  dataStore.iterateCursor(range, cursor => {
    if (!cursor) return;
    dataPoints.push(cursor.value);
    cursor.continue();
  });

  await transaction.complete;
  mark.end();
  return dataPoints;
}


//
// Write
//


// DebouncedWriter queues inputs for a write function, which is called in batch
// after no more inputs are added after a given timeout period.
class DebouncedWriter {
  constructor({ writeFunc, delay }) {
    this.writeFunc = writeFunc;
    this.delay = delay;

    this.queue = [];
    this.timeoutId = undefined; // result of setTimeout
  }
  enqueue(...writeFuncArgs) {
    this.queue.push(writeFuncArgs);

    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
    }

    this.timeoutId = setTimeout(() => {
      for (const args of this.queue) {
        this.writeFunc(...args);
      }
      this.queue = [];
    }, this.delay);
  }
}

// Queue results for write-back to IndexedDB. Hopefully this addresses the read
// latency experienced after the first read.
const writer = new DebouncedWriter({
  writeFunc: write,
  delay: 1000,
});

async function write(requestParams, { data, ...metadata }) {
  // Check for error in response
  if (metadata.error) {
    return;
  }

  const {
    columns,
    key,
    levelOfDetail,
    maxRevision,
    minRevision,
  } = requestParams;

  const totalMark = new Mark('IndexedDB', 'Write', key);

  // Store the result in IndexedDB
  const db = await openDatabase(key);

  // Store information about the timeseries
  const transaction = db.transaction(
      ['dataPoints', 'metadata', 'ranges'],
      'readwrite'
  );

  const dataStore = transaction.objectStore('dataPoints');
  const metadataStore = transaction.objectStore('metadata');
  const rangeStore = transaction.objectStore('ranges');

  // Map each unnamed column to its cooresponding name in the QueryParams.
  // Results in an object with key/value pairs representing column/value
  // pairs. Each datapoint will have a structure similar to the following:
  //   {
  //     revision: 12345,
  //     r_commit_pos: "12345",
  //     value: 42
  //   }
  let mark = new Mark('IndexedDB', 'Normalize', key);

  const namedDatapoints = (data || []).map(datapoint =>
    columns.reduce(
        (prev, name, index) =>
          Object.assign(prev, { [name]: datapoint[index] }),
        {}
    )
  );

  mark.end();

  // Store timeseries as objects indexed by r_commit_pos (preferred) or
  // revision.
  // Question(Sam): It is possible to do faster updates by opening a cursor at
  // the beginning revision and keep iterating until reaching the end revision?
  // Missing datapoints will be added to a queue and be added after without
  // having to merge.
  mark = new Mark('IndexedDB', 'Write - Datapoints', key);

  for (const datapoint of namedDatapoints) {
    const key = datapoint.revision || parseInt(datapoint.r_commit_pos);

    // Merge with existing data
    const prev = await dataStore.get(key);
    const next = Object.assign({}, prev, datapoint);

    // IndexedDB should be fast enough to "get" for every key. A notable
    // experiment might be to "getAll" and find by key. We can then compare
    // performance between "get" and "getAll".

    dataStore.put(next, key);
  }

  mark.end();

  if (namedDatapoints.length === 0) {
    // No timeseries data to write.
    return;
  }

  // Update the range of data we contain in the "ranges" object store.
  mark = new Mark('IndexedDB', 'Write - Ranges', key);

  const first = namedDatapoints[0] || {};
  const last = namedDatapoints[namedDatapoints.length - 1] || {};

  const min = minRevision ||
    first.revision ||
    parseInt(first.r_commit_pos) ||
    undefined;

  const max = maxRevision ||
    last.revision ||
    parseInt(last.r_commit_pos) ||
    undefined;

  if (min || max) {
    const currRange = Range.fromExplicitRange(min, max);
    const prevRangesRaw = await rangeStore.get(levelOfDetail) || [];
    const prevRanges = prevRangesRaw.map(Range.fromDict);

    const nextRanges = currRange
        .mergeIntoArray(prevRanges)
        .map(range => range.toJSON());

    rangeStore.put(nextRanges, levelOfDetail);
  } else {
    new Error('Min/max cannot be found; unable to update ranges');
  }

  mark.end();

  // Store metadata separately in the "metadata" object store.
  mark = new Mark('IndexedDB', 'Write - Metadata', key);
  for (const key of Object.keys(metadata)) {
    metadataStore.put(metadata[key], key);
  }
  mark.end();

  // Finish the transaction
  mark = new Mark('IndexedDB', 'Write - Queued Tasks', key);
  await transaction.complete;
  mark.end();

  totalMark.end();
}

//
// Utility functions
//


// Parse a HTTP request for information needed in IndexedDB operations.
export function parseRequest(request) {
  const url = new URL(request.url);

  const testSuite = url.searchParams.get('testSuite') || '';
  const measurement = url.searchParams.get('measurement') || '';
  const bot = url.searchParams.get('bot') || '';
  const testCase = url.searchParams.get('testCase') || '';
  const buildType = url.searchParams.get('buildType') || '';

  const statistic = url.searchParams.get('statistic');
  if (!statistic) {
    throw new Error('Statistic is not specified for this timeseries request!');
  }

  const levelOfDetail = url.searchParams.get('levelOfDetail') || undefined;

  return {
    columns: getColumnsByLevelOfDetail(levelOfDetail, statistic),
    key: `${testSuite}/${measurement}/${bot}/${testCase}/${buildType}`,
    levelOfDetail,
    maxRevision: parseInt(url.searchParams.get('maxRevision')) || undefined,
    minRevision: parseInt(url.searchParams.get('minRevision')) || undefined,
    signal: request.signal,
    statistic,
    url: request.url,
  };
}


//
// Testing utilities
//


// Delete the database corresponding to the specified request.
export async function deleteDatabaseForTest(request) {
  const { key } = parseRequest(request);
  const mark = new Mark('IndexedDB', 'Clear', key);

  if (key in connectionPool) {
    await connectionPool[key].close();
    delete connectionPool[key];
  }

  await idb.delete(key);
  mark.end();
}

// Disable the timeout-based writing mechanism for the DebouncedWriter.
export function disableAutomaticWritingForTest() {
  // Set the delay to a little over 285,420 years.
  // I'm really hoping our tests don't take that long!
  writer.delay = Number.MAX_SAFE_INTEGER;
}

// Flush the IndexedDB DebouncedWriter by executing everything on queue.
export function flushWriterForTest() {
  if (writer.timeoutId) {
    clearTimeout(writer.timeoutId);
  }

  const promises = writer.queue.map(args => writer.writeFunc(...args));
  writer.queue = [];

  return Promise.all(promises);
}


export default {
  parseRequest,
  race,
  deleteDatabaseForTest,
  disableAutomaticWritingForTest,
  flushWriterForTest,
};
