/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import idb from 'idb';
import Range from './sw-utils/range';
import { startMark, endMark } from './sw-utils/timing';

// Note(Sam): No files are being cached, so I probably should remove all Cache
// API features from the service worker.
const CACHE_NAME = 'v1';
const ORIGIN = location.origin;
const FILES_TO_CACHE = [];

const connectionPool = {};

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

// Setup worker-specific resources such as offline caches.
self.addEventListener('install', event => {
  // Open a cache and use `addAll()` with an array of assets to add all of them
  // to the cache. Ask the sevice worker to keep installed until the returning
  // promise resolves.
  event.waitUntil((async() => {
    const cache = await caches.open(CACHE_NAME);
    await cache.addAll(FILES_TO_CACHE);
  })());
});

// Allow the worker to finish the setup and clean other worker's related
// resources like removing old caches.
self.addEventListener('activate', event => {
  event.waitUntil((async() => {
    // Take control of uncontrolled clients. This will register the fetch event
    // listener after install. Note that this is a time sensitive operation.
    // Fetches called before claiming will not be intercepted.
    await self.clients.claim();

    // Delete all other cache stores that might be left over from old versions.
    const cacheNames = await caches.keys();
    await Promise.all(cacheNames.map(cacheName => {
      if (cacheName !== CACHE_NAME) {
        return caches.delete(cacheName);
      }
    }));
  })());
});

// On fetch, use cache but update the entry with the latest contents from the
// server.
self.addEventListener('fetch', event => {
  if (FILES_TO_CACHE.indexOf(event.request.url) !== -1) {
    event.respondWith(fromCache(event.request));
    event.waitUntil(updateCache(event.request));
    return;
  }

  if (event.request.url.startsWith(`${ORIGIN}/api/timeseries2`)) {
    const requestParams = getRequestParams(event.request);
    const race = raceIDB(requestParams);

    const winner = (async() => {
      const { value } = await race.next();
      return value.result;
    })();

    event.respondWith(winner);
    event.waitUntil((async() => {
      // Wait for all contestants to finish the race.
      for await (const contestant of race) {
        if (contestant) {
          const clients = await self.clients.matchAll();
          for (const client of clients) {
            client.postMessage({
              type: 'TIMESERIES_RESULT',
              key: requestParams.key,
              payload: contestant.result,
            });
          }
        }
      }

      // Tell clients that we're finished
      const clients = await self.clients.matchAll();
      for (const client of clients) {
        client.postMessage({
          type: 'TIMESERIES_FINISHED',
          key: requestParams.key,
        });
      }
    })());
  }
});

// Retrieve a cached resource using the Cache API
async function fromCache(request) {
  const cache = await caches.open(CACHE_NAME);
  const cachedResponse = await cache.match(request);
  return cachedResponse;
}

// Store a resource using the Cache API
async function updateCache(request) {
  const [response, cache] = await Promise.all([
    fetch(request),
    caches.open(CACHE_NAME),
  ]);

  if (response.status === 200) {
    cache.put(request.url, response.clone());
  }

  return response;
}

const LEVEL_OF_DETAIL = {
  // Minimaps only need the (x, y) coordinates to draw the line.
  // FastHistograms contain only r_commit_pos and the needed statistic.
  // Fetches /api/timeseries2/testpath&columns=r_commit_pos,value
  XY: 'xy',

  // chart-pair.chartLayout can draw its lines using XY FastHistograms
  // while asynchronously fetching annotations (e.g.  alerts)
  // for a given revision range for tooltips and icons.
  // If an extant request overlaps a new request, then the new request can
  // fetch the difference and await the extant request.
  // Fetches /api/timeseries2/testpath&min_rev&max_rev&columns=revision,alert
  ANNOTATIONS: 'annotations',

  // pivot-table in chart-section and pivot-section need the full real
  // Histogram with all its statistics and diagnostics and samples.
  // chart-section will also request the full Histogram for the last point in
  // each timeseries in order to get its RelatedNameMaps.
  // Real Histograms contain full RunningStatistics, all diagnostics, all
  // samples. Request single Histograms at a time, even if the user brushes a
  // large range.
  // Fetches /api/histogram/testpath?rev
  HISTOGRAM: 'histogram',
};

function columnsByLevelOfDetail(level) {
  switch (level) {
    case LEVEL_OF_DETAIL.XY:
      // TODO(Sam): Remove r_commit_pos everywhere
      // Question(Sam): Specifying columns to the API doesn't seem to work.
      // It always returns revision, r_commit_pos, timestamp, and value.
      // return ['revision', 'value'];
      return ['revision', 'r_commit_pos', 'timestamp', 'value'];
    case LEVEL_OF_DETAIL.ANNOTATIONS:
      return ['revision', 'alert', 'diagnostics', 'revisions'];
    default:
      throw new Error(`${level} is not a valid Level Of Detail`);
  }
}

// Parse a HTTP request for information needed in IndexedDB operations.
function getRequestParams(request) {
  const url = new URL(request.url);

  const testSuite = url.searchParams.get('testSuite') || '';
  const measurement = url.searchParams.get('measurement') || '';
  const bot = url.searchParams.get('bot') || '';
  const testCase = url.searchParams.get('testCase') || '';
  const buildType = url.searchParams.get('buildType') || '';
  const key = `${testSuite}/${measurement}/${bot}/${testCase}/${buildType}`;

  const statistic = url.searchParams.get('statistic');
  if (!statistic) {
    throw new Error('Statistic is not specified for this timeseries request!');
  }

  const levelOfDetail = url.searchParams.get('levelOfDetail') || undefined;
  const columns = columnsByLevelOfDetail(levelOfDetail);

  // Replace "value" column with the statistic requested since IndexedDB stores
  // multiple statistics in the same database.
  const valueIndex = columns.indexOf('value');
  if (valueIndex !== -1) {
    columns[valueIndex] = statistic;
  } else {
    throw new Error('Value within a timeseries was not queried for!');
  }

  return {
    columns,
    key: key.replace(/\./g, '_'),
    levelOfDetail,
    maxRevision: parseInt(url.searchParams.get('maxRevision')) || undefined,
    minRevision: parseInt(url.searchParams.get('minRevision')) || undefined,
    signal: request.signal,
    statistic,
    url: request.url,
  };
}

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

async function* raceIDB(requestParams) {
  // Start a race between IndexedDB and the network. The winner gets to return
  // their result first. The loser's promise will be returned in case the caller
  // wants it.
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
    const levelOfDetail = url.searchParams.get('levelOfDetail');
    url.searchParams.delete('levelOfDetail');
    const columns = columnsByLevelOfDetail(levelOfDetail);
    url.searchParams.set('columns', columns);

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

  async function getMetadata(key) {
    startMark(`IndexedDB-read-load-metadata-${key}`);
    const metadataStore = transaction.objectStore('metadata');
    const result = await metadataStore.get(key);
    endMark(`IndexedDB-read-load-metadata-${key}`);
    return result;
  }

  async function getRanges(levelOfDetail) {
    startMark('IndexedDB-read-load-ranges');
    const rangeStore = transaction.objectStore('ranges');
    const ranges = await rangeStore.get(levelOfDetail);
    endMark('IndexedDB-read-load-ranges');
    return ranges;
  }

  async function getDataPoints() {
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

  const dataPointsPromise = getDataPoints();
  const [
    cachedColumns,
    improvementDirection,
    units,
    ranges,
  ] = await Promise.all([
    getMetadata('columns'),
    getMetadata('improvement_direction'),
    getMetadata('units'),
    getRanges(levelOfDetail),
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
    const prevRanges = prevRangesRaw.map(range =>
      Range.fromDict({ ...range, isEmpty: false })
    );

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
