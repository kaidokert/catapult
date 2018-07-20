/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import idb from 'idb';
import Range from './range';
import { startMark, endMark } from './timing';

//
// Race
//


// Start a race between IndexedDB and the network. The winner returns their
// result first. The loser's promise will be returned in case the caller wants
// it. After a short period of time, results from the network will be written
// back to IndexedDB.
export async function* raceIDB(requestParams) {
  const cache = (async() => {
    startMark('IndexedDB-load-cache');
    const response = await readIDB(requestParams);
    endMark('IndexedDB-load-cache');
    return {
      name: 'IndexedDB',
      result: response,
    };
  })();

  const network = (async() => {
    const url = new URL(requestParams.url);

    // Transform the `levelOfDetail` header to `columns`
    url.searchParams.delete('levelOfDetail');
    url.searchParams.set('columns', requestParams.columns);

    startMark('IndexedDB-load-network');
    const response = await fetch(url, { signal: requestParams.signal });
    endMark('IndexedDB-load-network');

    startMark('IndexedDB-load-network-parseJSON');
    const json = await response.json();
    endMark('IndexedDB-load-network-parseJSON');

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
async function openIDB(key) {
  if (!connectionPool[key]) {
    connectionPool[key] = await idb.open(key, 1, upgradeDB => {
      if (upgradeDB.oldVersion === 0) {
        upgradeDB.createObjectStore('dataPoints');
        upgradeDB.createObjectStore('metadata');
        upgradeDB.createObjectStore('ranges');
      }
    });
  }

  return connectionPool[key];
}


//
// Read
//

// Read any existing data from IndexedDB.
async function readIDB(requestParams) {
  const {
    columns,
    key,
    levelOfDetail,
    maxRevision,
    minRevision,
  } = requestParams;

  startMark('IndexedDB-read-open');
  const db = await openIDB(key);
  endMark('IndexedDB-read-open');

  const transaction = db.transaction(
      ['ranges', 'dataPoints', 'metadata'],
      'readonly'
  );

  const dataPointsPromise = getDataPoints(
      transaction, minRevision, maxRevision);
  const [
    cachedColumns,
    improvementDirection,
    units,
    ranges,
  ] = await Promise.all([
    getMetadata(transaction, 'columns'),
    getMetadata(transaction, 'improvement_direction'),
    getMetadata(transaction, 'units'),
    getRanges(transaction, levelOfDetail),
  ]);

  //
  // Metadata
  //

  startMark('IndexedDB-read-checks');
  if (!cachedColumns) {
    // Timeseries does not exist in cache.
    return;
  }

  // Check that the cached version contains all the columns we need for
  // the requested level-of-detail (LOD).
  for (const column of columns) {
    if (!cachedColumns.includes(column)) {
      // We need to fetch more data from the network. The cache is no help in
      // this scenario.
      return;
    }
  }

  //
  // Ranges
  //

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

  endMark('IndexedDB-read-checks');

  //
  // Datapoints
  //

  const dataPoints = await dataPointsPromise;

  // Denormalize requested columns to an array with the same order as
  // requested.
  startMark('IndexedDB-read-denormalize');
  const timeseries = [];
  for (const dataPoint of dataPoints) {
    const result = [];
    for (const column of columns) {
      result.push(dataPoint[column]);
    }
    timeseries.push(result);
  }
  endMark('IndexedDB-read-denormalize');

  return {
    improvement_direction: improvementDirection,
    units,
    timeseries,
  };
}

async function getMetadata(transaction, key) {
  startMark(`IndexedDB-read-load-metadata-${key}`);
  const metadataStore = transaction.objectStore('metadata');
  const result = await metadataStore.get(key);
  endMark(`IndexedDB-read-load-metadata-${key}`);
  return result;
}

async function getRanges(transaction, levelOfDetail) {
  startMark('IndexedDB-read-load-ranges');
  const rangeStore = transaction.objectStore('ranges');
  const ranges = await rangeStore.get(levelOfDetail);
  endMark('IndexedDB-read-load-ranges');
  return ranges;
}

async function getDataPoints(transaction, minRevision, maxRevision) {
  startMark('IndexedDB-read-load-dataPoints');
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
  endMark('IndexedDB-read-load-dataPoints');

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
  writeFunc: writeIDB,
  delay: 1000,
});

async function writeIDB(requestParams, { timeseries, ...metadata }) {
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

  // Store the result in IndexedDB
  startMark('IndexedDB-write-open');
  const db = await openIDB(key);
  endMark('IndexedDB-write-open');

  startMark('IndexedDB-write-processing');

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
  const namedDatapoints = (timeseries || []).map(datapoint =>
    columns.reduce(
        (prev, name, index) =>
          Object.assign(prev, { [name]: datapoint[index] }),
        {}
    )
  );

  // Store timeseries as objects indexed by r_commit_pos (preferred) or
  // revision.
  // Note(Sam): It is possible to do faster updates by opening a cursor at
  // the beginning revision and keep iterating until reaching the end
  // revision. Missing datapoints will be added to a queue and be added
  // after without having to merge.
  startMark('IndexedDB-write-bulkPut');
  for (const datapoint of namedDatapoints) {
    const key = datapoint.revision || parseInt(datapoint.r_commit_pos);

    // Merge with existing data
    // Note(Sam): IndexedDB should be fast enough to "get" for every key.
    // A notable experiment might be to "getAll" and find by key. We can
    // then compare performance between "get" and "getAll".
    const prev = await dataStore.get(key);
    const next = Object.assign({}, prev, datapoint);

    dataStore.put(next, key);
  }
  endMark('IndexedDB-write-bulkPut');

  // Update the range of data we contain in the "ranges" object store.
  if (namedDatapoints.length === 0) {
    throw new Error('No timeseries data to write');
  }

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
    startMark('IndexedDB-write-range');
    const prevRangesRaw = await rangeStore.get(levelOfDetail) || [];
    endMark('IndexedDB-write-range');
    const prevRanges = prevRangesRaw.map(Range.fromDict);

    const nextRanges = currRange
        .mergeIntoArray(prevRanges)
        .map(range => range.toJSON());

    rangeStore.put(nextRanges, levelOfDetail);
  } else {
    // Timeseries is empty
    new Error('Min/max cannot be found; unable to update ranges');
  }

  // Store metadata separately in the "metadata" object store.
  for (const key of Object.keys(metadata)) {
    metadataStore.put(metadata[key], key);
  }

  // Store the columns available for data points in the "metadata" object
  // store. This is helpful to keep track of LOD.
  // TODO(sbalana): Test when LOD is implemented
  // TODO(sbalana): Push for the spread operator. Greatly needed here.
  startMark('IndexedDB-write-columns');
  const prevColumns = await metadataStore.get('columns') || [];
  endMark('IndexedDB-write-columns');
  const nextColumns = [...new Set([
    ...prevColumns,
    ...columns,
  ])];

  metadataStore.put(nextColumns, 'columns');
  endMark('IndexedDB-write-processing');

  // Finish the transaction
  startMark('IndexedDB-write-complete');
  await transaction.complete;
  endMark('IndexedDB-write-complete');
}
