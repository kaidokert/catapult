/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import {CHAIN, ENSURE, UPDATE} from './simple-redux.js';
import {ReportControls} from './report-controls.js';
import {ReportNamesRequest} from './report-names-request.js';
import {ReportSection} from './report-section.js';
import {STORE} from './element-base.js';
import {TimeseriesRequest} from './timeseries-request.js';
import {afterRender, denormalize} from './utils.js';
import {assert} from 'chai';

suite('report-section', function() {
  let originalFetch;
  setup(async() => {
    originalFetch = window.fetch;
    window.fetch = async(url, options) => {
      return {
        ok: true,
        async json() {
          if (url === ReportNamesRequest.URL) {
            return [{
              name: ReportControls.DEFAULT_NAME,
              id: 42,
              modified: new Date(),
              template: {
                statistics: ['avg'],
                rows: [
                  {
                    label: 'group:label',
                    testSuites: ['suite'],
                    measurement: 'ms',
                    bots: ['master:bot'],
                    testCases: ['case'],
                  },
                ],
              },
            }];
          }
          if (url === TimeseriesRequest.URL) {
            const data = [
              {
                revision: ReportControls.CHROMIUM_MILESTONES[
                    ReportControls.CURRENT_MILESTONE] - 1,
                timestamp: 1000, avg: 100, count: 1,
              },
              {
                revision: ReportControls.CHROMIUM_MILESTONES[
                    ReportControls.CURRENT_MILESTONE] + 1,
                timestamp: 2000, avg: 100, count: 1,
              },
            ];
            return {
              units: options.body.get('measurement'),
              data: denormalize(
                  data, options.body.get('columns').split(',')),
            };
          }
        },
      };
    };
  });

  teardown(() => {
    for (const child of document.body.children) {
      if (!child.matches('report-section')) continue;
      document.body.removeChild(child);
    }
    window.fetch = originalFetch;
  });

  test('loadReports', async function() {
    const section = document.createElement('report-section');
    section.statePath = 'test';
    await STORE.dispatch(CHAIN(
        ENSURE('test'),
        ENSURE('test.source'),
        UPDATE('test', ReportSection.buildState({}))));
    document.body.appendChild(section);
    await afterRender();
    assert.isTrue(section.tables[0].isPlaceholder);
    while (section.tables[0].isPlaceholder) {
      await afterRender();
    }
    assert.lengthOf(section.tables[0].rows, 1);
    assert.strictEqual('group', section.tables[0].rows[0].labelParts[0].label);
    assert.strictEqual('label', section.tables[0].rows[0].labelParts[1].label);
    assert.strictEqual(100, section.tables[0].rows[0].scalars[0].value);
    assert.strictEqual(100, section.tables[0].rows[0].scalars[1].value);
  });
});
