/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

window.IS_DEBUG = location.hostname === 'localhost';
const PRODUCTION = 'v2spa-dot-chromeperf.appspot.com';
window.IS_PRODUCTION = location.hostname === PRODUCTION;

window.AUTH_CLIENT_ID = !IS_PRODUCTION ? '' :
  '62121018386-rhk28ad5lbqheinh05fgau3shotl2t6c.apps.googleusercontent.com';

if ('serviceWorker' in navigator && !IS_DEBUG) {
  document.addEventListener('DOMContentLoaded', async() => {
    await navigator.serviceWorker.register(
        'service-worker.js?' + VULCANIZED_TIMESTAMP.getTime());

    if (navigator.serviceWorker.controller === null) {
      // Technically, everything would work without the service worker, but it
      // would be unbearably slow. Reload so that the service worker can
      // finish installing.
      location.reload();
    }
  });
}

async function fakeFetch(url, options) {
  return {
    async json() {
      // console.log('FETCH', url, new Map(options.body));

      if (url === '/short_uri') {
        return {sid: ''};
      }

      if (url === cp.RecentBugsRequest.URL) {
        return {bugs: []};
      }

      if (url === cp.TestSuitesRequest.URL) {
        return [
          'system_health.common_desktop',
          'system_health.common_mobile',
          'system_health.memory_desktop',
          'system_health.memory_mobile',
        ];
      }

      if (url === cp.TimeseriesRequest.URL) {
        let units = 'unitlessNumber';
        const measurement = options.body.get('measurement');
        if (measurement.startsWith('memory:')) {
          units = 'sizeInBytes_smallerIsBetter';
        }
        if (measurement.startsWith('cpu:') ||
            measurement.startsWith('loading') ||
            measurement.startsWith('startup')) {
          units = 'ms_smallerIsBetter';
        }
        if (measurement.startsWith('power')) {
          units = 'W_smallerIsBetter';
        }
        const data = [];
        const sequenceLength = 100;
        const nowMs = new Date() - 0;
        const MS_PER_YEAR = tr.b.convertUnit(
            1, tr.b.UnitScale.TIME.YEAR, tr.b.UnitScale.TIME.MILLI_SEC);
        for (let i = 0; i < sequenceLength; i += 1) {
          const pct = (sequenceLength - i - 1) / sequenceLength;
          const timestamp = nowMs - pct * MS_PER_YEAR;
          data.push({
            // revision: i * 1000,
            revision: timestamp,
            timestamp,
            avg: parseInt(100 * Math.random()),
            count: 1,
            std: parseInt(50 * Math.random()),
            // TODO diagnostics, revisions, alert
          });
        }
        const columns = options.body.get('columns').split(',');
        return {data: cp.denormalize(data, columns), units};
      }

      if (url === cp.DescribeRequest.URL) {
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
          caseTags: {
            media: [
              'browse:media:facebook_photos',
              'browse:media:imgur',
              'browse:media:youtube',
              'load:media:google_images',
              'load:media:imgur',
              'load:media:youtube',
            ],
            firstParty: [
              'load:chrome:blank',
              'search:portal:google',
            ],
          }
        };
      }

      if (url === cp.ReportNamesRequest.URL) {
        return [
          {name: 'Chromium Performance Overview', id: 0, modified: 0},
        ];
      }

      if (url === cp.ReportTemplateRequest.URL) {
        return [
          {name: 'Chromium Performance Overview', id: 0, modified: 0},
        ];
      }

      if (url === cp.ReportRequest.URL) {
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
          url: 'http://example.com/',
          report: {rows, statistics: ['avg', 'std']},
        };
      }

      if (url === cp.ExistingBugRequest.URL) {
        return {};
      }

      if (url === cp.SheriffsRequest.URL) {
        return ['Chromium Perf Sheriff'];
      }

      if (url === cp.AlertsRequest.URL) {
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
            units: measurements[i].startsWith('memory') ? 'sizeInBytes' :
              'ms',
          });
        }
        alerts.sort((x, y) => x.start_revision - y.start_revision);
        return {anomalies: alerts};
      }
    }
  };
}
fakeFetch.original = fetch;
if (IS_DEBUG) window.fetch = fakeFetch;

// These packages use base imports so they can be webpacked but not dynamically
// loaded in tests.
import '/@polymer/app-route/app-location.js';
import '/@polymer/app-route/app-route.js';
import '/@polymer/iron-collapse/iron-collapse.js';
import '/@polymer/iron-icon/iron-icon.js';
import '/@polymer/iron-iconset-svg/iron-iconset-svg.js';

import './chromeperf-app.js';
