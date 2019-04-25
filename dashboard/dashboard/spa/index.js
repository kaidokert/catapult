/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

tr.exportTo('window', () => {
  const IS_DEBUG = location.hostname === 'localhost';
  const PRODUCTION = 'v2spa-dot-chromeperf.appspot.com';
  const IS_PRODUCTION = location.hostname === PRODUCTION;

  let AUTH_CLIENT_ID =
    '62121018386-rhk28ad5lbqheinh05fgau3shotl2t6c.apps.googleusercontent.com';
  if (!IS_PRODUCTION) AUTH_CLIENT_ID = '';

  // Google Analytics
  const trackingId = IS_PRODUCTION ? 'UA-98760012-3' : 'UA-98760012-4';

  window.ga = window.ga || function() {
    ga.q = ga.q || [];
    ga.q.push(arguments);
  };
  ga.l = new Date();
  ga('create', trackingId, 'auto');
  ga('send', 'pageview');
  (function() {
    // Write this script tag at runtime instead of in HTML in order to prevent
    // vulcanizer from inlining a remote script.
    const script = document.createElement('script');
    script.src = 'https://www.google-analytics.com/analytics.js';
    script.type = 'text/javascript';
    script.async = true;
    document.head.appendChild(script);
  })();

  // Register the Service Worker when in production. Service Workers are not
  // helpful in development mode because all backend responses are being mocked.
  if ('serviceWorker' in navigator && !IS_DEBUG) {
    const swChannel = new BroadcastChannel('service-worker');
    const analyticsClientIdPromise = new Promise(resolve => ga(tracker =>
      resolve(tracker.get('clientId'))));

    document.addEventListener('DOMContentLoaded', async() => {
      const [clientId] = await Promise.all([
        analyticsClientIdPromise,
        navigator.serviceWorker.register(
            'service-worker.js?' + VULCANIZED_TIMESTAMP.getTime()),
      ]);

      if (navigator.serviceWorker.controller === null) {
        // Technically, everything would work without the service worker, but it
        // would be unbearably slow. Reload so that the service worker can
        // finish installing.
        location.reload();
      }

      swChannel.postMessage({
        type: 'GOOGLE_ANALYTICS',
        payload: {
          trackingId,
          clientId,
        },
      });
    });
  }

  return {
    AUTH_CLIENT_ID,
    IS_DEBUG,
    IS_PRODUCTION,
  };
});

import './chromeperf-app.js';

import {Mark} from './metrics.js';

// TODO remove when all users are es6.
tr.exportTo('cp', () => {
  return {Mark};
});

window.addEventListener('load', () => {
  const loadTimes = Object.entries(performance.timing.toJSON()).filter(p =>
    p[1] > 0);
  loadTimes.sort((a, b) => a[1] - b[1]);
  const start = loadTimes.shift()[1];
  for (const [name, timeStamp] of loadTimes) {
    new Mark('load', name, start).end(timeStamp);
  }
});
