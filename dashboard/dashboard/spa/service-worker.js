/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import DescribeCacheRequest from './describe-cache-request.js';
import ReportNamesCacheRequest from './report-names-cache-request.js';
import TestSuitesCacheRequest from './test-suites-cache-request.js';
import analytics from './google-analytics.js';

const channel = new BroadcastChannel('service-worker');

function handleMessage(messageEvent) {
  switch (messageEvent.data.type) {
    case 'GOOGLE_ANALYTICS': {
      const {trackingId, clientId} = messageEvent.data.payload;
      analytics.configure(trackingId, clientId);
      break;
    }
    default:
      throw new Error(`Unrecognized message ${messageEvent.data.type}`);
  }
}

self.addEventListener('install', () => {
  channel.addEventListener('message', handleMessage);
});

self.addEventListener('activate', activateEvent => {
  activateEvent.waitUntil(self.clients.claim());
});

const FETCH_HANDLERS = {
  '/api/describe': DescribeCacheRequest,
  '/api/report/names': ReportNamesCacheRequest,
  '/api/test_suites': TestSuitesCacheRequest,
};

self.addEventListener('fetch', fetchEvent => {
  const cls = FETCH_HANDLERS[new URL(fetchEvent.request.url).pathname];
  if (!cls) return;
  fetchEvent.waitUntil(new cls(fetchEvent).respond());
});
