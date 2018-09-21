/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import analytics from './sw-utils/google-analytics.js';
import TimeseriesCacheRequest from './sw-utils/timeseries-cache-request.js';
import ReportCacheRequest from './sw-utils/report-cache-request.js';
import ReportNamesCacheRequest from './sw-utils/report-names-cache-request.js';
import SessionIdCacheRequest from './sw-utils/session-id-cache-request.js';

const channel = new BroadcastChannel('service-worker');

function handleMessage(messageEvent) {
  switch (messageEvent.type) {
    case 'GOOGLE_ANALYTICS': {
      const {trackingId, clientId} = messageEvent.data;
      analytics.configure(trackingId, clientId);
      break;
    }
    default:
      throw new Error(`Unknown service-worker message ${messageEvent.type}`);
  }
}

self.addEventListener('install', () => {
  channel.addEventListener('message', handleMessage);
});

self.addEventListener('activate', activateEvent => {
  activateEvent.waitUntil(self.clients.claim());
});

function getFetchHandler(fetchEvent) {
  switch (new URL(fetchEvent.request.url).pathname) {
    case '/api/report/generate':
      return new ReportCacheRequest(fetchEvent);
    case '/api/report/names':
      return new ReportNamesCacheRequest(fetchEvent);
    case '/api/timeseries2':
      return new TimeseriesCacheRequest(fetchEvent);
    case '/short_uri':
      return new SessionIdCacheRequest(fetchEvent);
  }
}

self.addEventListener('fetch', fetchEvent => {
  const handler = getFetchHandler(fetchEvent);
  if (!handler) return;
  fetchEvent.waitUntil(handler.respond());
});
