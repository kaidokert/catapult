/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import idb from 'idb';
import Range from './sw-utils/range';
import { startMark, endMark } from './sw-utils/timing';
import { raceIDB } from './sw-utils/idb';

// Note(Sam): No files are being cached, so I probably should remove all Cache
// API features from the service worker.
const CACHE_NAME = 'v1';
const ORIGIN = location.origin;
const FILES_TO_CACHE = [];

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
      // Wait for each contestant to finish the race, informing clients of their
      // results.
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

