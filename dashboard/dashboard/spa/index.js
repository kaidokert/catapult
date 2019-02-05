/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

window.AUTH_CLIENT_ID =
  '62121018386-rhk28ad5lbqheinh05fgau3shotl2t6c.apps.googleusercontent.com';

// When true, state is recursively frozen so that improper property setting
// causes an error to be thrown. Freezing significantly impacts performance,
// so set to false in order to measure performance on localhost.
window.IS_DEBUG = location.hostname === 'localhost';

// When in production, tell Redux Dev Tools to disable automatic recording.
const PRODUCTION_ORIGIN = 'v2spa-dot-chromeperf.appspot.com';
window.PRODUCTION_URL = `https://${PRODUCTION_ORIGIN}`;
window.IS_PRODUCTION = location.hostname === PRODUCTION_ORIGIN;

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
if ('serviceWorker' in navigator && !window.IS_DEBUG) {
  const swChannel = new BroadcastChannel('service-worker');
  const analyticsClientIdPromise = new Promise(resolve => ga(tracker => resolve(
      tracker.get('clientId'))));

  document.addEventListener('DOMContentLoaded', async() => {
    const [clientId] = await Promise.all([
      analyticsClientIdPromise,
      navigator.serviceWorker.register(
          'service-worker.js?' + VULCANIZED_TIMESTAMP.getTime()),
    ]);
    if (navigator.serviceWorker.controller === null) {
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

window.addEventListener('load', () => {
  tr.b.Timing.ANALYTICS_FILTERS.push(mark =>
    ['firstPaint', 'fetch', 'load'].includes(mark.groupName) ||
    (mark.durationMs > 100));
  const loadTimes = Object.entries(performance.timing.toJSON()).filter(p =>
    p[1] > 0);
  loadTimes.sort((a, b) => a[1] - b[1]);
  const start = loadTimes.shift()[1];
  for (const [name, timeStamp] of loadTimes) {
    tr.b.Timing.mark('load', name, start).end(timeStamp);
  }
});

window.fetch = async(url, options) => {
  return {
    async json() {
      if (url === '/short_uri') {
        return {sid: ''};
      }

      if (url === '/api/test_suites') {
        return [
          'system_health.common_desktop',
          'system_health.common_mobile',
          'system_health.memory_desktop',
          'system_health.memory_mobile',
        ];
      }

      if (url === '/api/timeseries2') {
        let units = 'unitlessNumber';
        if (this.measurement_.startsWith('memory:')) {
          units = 'sizeInBytes_smallerIsBetter';
        }
        if (this.measurement_.startsWith('cpu:') ||
            this.measurement_.startsWith('loading') ||
            this.measurement_.startsWith('startup')) {
          units = 'ms_smallerIsBetter';
        }
        if (this.measurement_.startsWith('power')) {
          units = 'W_smallerIsBetter';
        }
        const data = [];
        const sequenceLength = 100;
        const nowMs = new Date() - 0;
        for (let i = 0; i < sequenceLength; i += 1) {
          data.push({
            revision: i * 100,
            timestamp: nowMs - ((sequenceLength - i - 1) * (2592105834 / 50)),
            avg: parseInt(100 * Math.random()),
            count: 1,
            std: parseInt(50 * Math.random()),
            // TODO diagnostics, revisions, alert
          });
        }
        return {data: cp.denormalize(data, this.columns_), units};
      }

      if (url === '/api/describe') {
        return {
          measurements: [
            'memory:a_size',
            'memory:b_size',
            'memory:c_size',
            'cpu:a',
            'cpu:b',
            'cpu:c',
            'power',
            'loading',
            'startup',
            'size',
          ],
          bots: ['master:bot0', 'master:bot1', 'master:bot2'],
          cases: [
            'browse:media:facebook_photos',
            'browse:media:imgur',
            'browse:media:youtube',
            'browse:news:flipboard',
            'browse:news:hackernews',
            'browse:news:nytimes',
            'browse:social:facebook',
            'browse:social:twitter',
            'load:chrome:blank',
            'load:games:bubbles',
            'load:games:lazors',
            'load:games:spychase',
            'load:media:google_images',
            'load:media:imgur',
            'load:media:youtube',
            'search:portal:google',
          ],
        };
      }

      if (url === '/api/report/names') {
        return [
          {name: 'Chromium Performance Overview', id: 0, modified: 0},
        ];
      }

      if (url === '/api/report/generate') {
        const rows = [];
        const dummyRow = measurement => {
          const row = {
            testSuites: ['system_health.common_mobile'],
            bots: ['master:bot0', 'master:bot1', 'master:bot2'],
            testCases: [],
            data: {},
            measurement,
          };
          for (const revision of options.body.get('revisions').split(',')) {
            row.data[revision] = {
              descriptors: [
                {
                  testSuite: 'system_health.common_mobile',
                  measurement,
                  bot: 'master:bot0',
                  testCase: 'search:portal:google',
                },
                {
                  testSuite: 'system_health.common_mobile',
                  measurement,
                  bot: 'master:bot1',
                  testCase: 'search:portal:google',
                },
              ],
              statistics: [
                10, 0, 0, Math.random() * 1000, 0, 0, Math.random() * 1000],
              revision,
            };
          }
          return row;
        };

        for (const group of ['Pixel', 'Android Go']) {
          rows.push({
            ...dummyRow('memory:a_size'),
            label: group + ':Memory',
            units: 'sizeInBytes_smallerIsBetter',
          });
          rows.push({
            ...dummyRow('loading'),
            label: group + ':Loading',
            units: 'ms_smallerIsBetter',
          });
          rows.push({
            ...dummyRow('startup'),
            label: group + ':Startup',
            units: 'ms_smallerIsBetter',
          });
          rows.push({
            ...dummyRow('cpu:a'),
            label: group + ':CPU',
            units: 'ms_smallerIsBetter',
          });
          rows.push({
            ...dummyRow('power'),
            label: group + ':Power',
            units: 'W_smallerIsBetter',
          });
        }

        return {
          name: 'Chromium Performance Overview',
          owners: ['benjhayden@chromium.org', 'benjhayden@google.com'],
          url: window.PRODUCTION_URL,
          report: {rows, statistics: ['avg', 'std']},
        };
      }

      if (url === '/api/existing_bug') {
        return {};
      }

      if (url === '/api/sheriffs') {
        return ['Chromium Perf Sheriff'];
      }

      if (url === '/api/alerts') {
        const improvements = Boolean(options.body.get('is_improvement'));
        const alerts = [];
        const measurements = [
          'memory:a_size',
          'memory:b_size',
          'memory:c_size',
          'cpu:a',
          'cpu:b',
          'cpu:c',
          'power',
          'loading',
          'startup',
          'size',
        ];
        const testCases = [
          'browse:media:facebook_photos',
          'browse:media:imgur',
          'browse:media:youtube',
          'browse:news:flipboard',
          'browse:news:hackernews',
          'browse:news:nytimes',
          'browse:social:facebook',
          'browse:social:twitter',
          'load:chrome:blank',
          'load:games:bubbles',
          'load:games:lazors',
          'load:games:spychase',
          'load:media:google_images',
          'load:media:imgur',
          'load:media:youtube',
          'search:portal:google',
        ];
        for (let i = 0; i < 10; ++i) {
          const revs = new tr.b.math.Range();
          revs.addValue(parseInt(1e6 * Math.random()));
          revs.addValue(parseInt(1e6 * Math.random()));
          let bugId = undefined;
          if (options.body.get('bug_id') !== '' && (Math.random() > 0.5)) {
            if (Math.random() > 0.5) {
              bugId = -1;
            } else {
              bugId = 123456;
            }
          }
          alerts.push({
            bot: 'bot' + (i % 3),
            bug_components: [],
            bug_id: bugId,
            bug_labels: [],
            descriptor: {
              bot: 'master:bot' + (i * 3),
              measurement: measurements[i],
              statistic: 'avg',
              testCase: testCases[i % testCases.length],
              testSuite: 'system_health.common_desktop',
            },
            end_revision: revs.max,
            improvement: improvements && (Math.random() > 0.5),
            key: tr.b.GUID.allocateSimple(),
            master: 'master',
            median_after_anomaly: 100 * Math.random(),
            median_before_anomaly: 100 * Math.random(),
            start_revision: revs.min,
            test: measurements[i] + '/' + testCases[i % testCases.length],
            units: measurements[i].startsWith('memory') ? 'sizeInBytes' : 'ms',
          });
        }
        alerts.sort((x, y) => x.start_revision - y.start_revision);
        return {anomalies: alerts};
      }
    }
  };
};
