/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import Mark from './sw-utils/mark.js';
import cache from './sw-utils/cache.js';

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
    const race = cache.race(event.request, channel);

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
