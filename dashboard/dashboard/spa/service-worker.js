/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import Mark from './sw-utils/mark';
import { raceIDB } from './sw-utils/idb';
import { columnsByLevelOfDetail } from './sw-utils/level-of-detail';

// Create a communication channel between clients and the service worker to
// allow for post-installation configuration. This is curretly used for
// retrieving Google Analytics tracking and client ids.
const channel = new BroadcastChannel('service-worker');

// Setup worker-specific resources such as offline caches.
self.addEventListener('install', event => {
  // Start listening for a message to configure Google Analytics.
  const gaHandler = messageEvent => {
    const { type, payload } = messageEvent.data;

    if (type === 'GOOGLE_ANALYTICS') {
      const { trackingId, clientId } = payload;
      Mark.configure(trackingId, clientId);
      channel.removeEventListener('message', gaHandler);
    } else {
      throw new Error(`Unknown Service Worker message type: ${type}`);
    }
  };

  channel.addEventListener('message', gaHandler);
});

// Allow the worker to finish the setup and clean other worker's related
// resources like removing old caches.
self.addEventListener('activate', event => {
  // Take control of uncontrolled clients. This will register the fetch event
  // listener after install. Note that this is a time sensitive operation.
  // Fetches called before claiming will not be intercepted.
  event.waitUntil(self.clients.claim());
});

// On fetch, use cache but update the entry with the latest contents from the
// server.
self.addEventListener('fetch', event => {
  if (event.request.url.startsWith(`${location.origin}/api/timeseries2`)) {
    const requestParams = getRequestParams(event.request);
    const race = raceIDB(requestParams, channel);

    const winner = (async() => {
      const { value } = await race.next();
      return value.result;
    })();

    event.respondWith(winner);
    event.waitUntil((async() => {
      // Open a channel for communication between clients.
      const channel = new BroadcastChannel(event.request.url);

      // Wait for each contestant to finish the race, informing clients of their
      // results.
      for await (const contestant of race) {
        if (contestant) {
          channel.postMessage({
            type: 'TIMESERIES_RESULT',
            payload: contestant.result,
          });
        }
      }

      // Tell clients that we're finished
      channel.postMessage({
        type: 'TIMESERIES_FINISHED',
      });
    })());
  }
});

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

  return {
    columns: columnsByLevelOfDetail(levelOfDetail, statistic),
    key: key.replace(/\./g, '_'),
    levelOfDetail,
    maxRevision: parseInt(url.searchParams.get('maxRevision')) || undefined,
    minRevision: parseInt(url.searchParams.get('minRevision')) || undefined,
    signal: request.signal,
    statistic,
    url: request.url,

    // TODO(Sam): Remove this once CL 1146066 is merged
    // https://chromium-review.googlesource.com/c/catapult/+/1146066
    oldColumns: columnsByLevelOfDetail(levelOfDetail, 'value'),
  };
}

