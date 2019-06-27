/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import ConfigCacheRequest from './config-cache-request.js';
import DescribeCacheRequest from './describe-cache-request.js';
import ReportCacheRequest from './report-cache-request.js';
import ReportNamesCacheRequest from './report-names-cache-request.js';
import SessionIdCacheRequest from './session-id-cache-request.js';
import SheriffsCacheRequest from './sheriffs-cache-request.js';
import TestSuitesCacheRequest from './test-suites-cache-request.js';
import TimeseriesCacheRequest from './timeseries-cache-request.js';

self.addEventListener('activate', activateEvent => {
  activateEvent.waitUntil(self.clients.claim());
});

const FETCH_HANDLERS = {
  '/api/config': ConfigCacheRequest,
  '/api/describe': DescribeCacheRequest,
  '/api/report/generate': ReportCacheRequest,
  '/api/report/names': ReportNamesCacheRequest,
  '/api/sheriffs': SheriffsCacheRequest,
  '/api/test_suites': TestSuitesCacheRequest,
  '/api/timeseries2': TimeseriesCacheRequest,
  '/short_uri': SessionIdCacheRequest,
};

self.addEventListener('fetch', fetchEvent => {
  const cls = FETCH_HANDLERS[new URL(fetchEvent.request.url).pathname];
  if (!cls) return;
  new cls(fetchEvent).respond();
});

// TODO When a user generates a report more than some frequency, subscribe to
// it.
// TODO When a user fetches alerts for a sheriff more than some frequency,
// subscribe to it.

async function handlePush(event) {
  const subscription = self.registration.pushManager.getSubscription();
  console.log(subscription);
  // TODO fetch timeseries data described by subscription
}

self.addEventListener('push', event => {
  event.waitUntil(handlePush(event));
});
