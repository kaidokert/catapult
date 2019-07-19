/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import {LEVEL_OF_DETAIL, TimeseriesRequest} from './timeseries-request.js';
import {ReportFetcher, RangeFinder} from './report-fetcher.js';
import {assert} from 'chai';
import {denormalize} from './utils.js';

suite('report-fetcher', function() {
  let originalFetch;
  let timeseriesBody;
  setup(() => {
    originalFetch = window.fetch;
    window.fetch = async(url, options) => {
      return {
        ok: true,
        async json() {
          if (url === TimeseriesRequest.URL) {
            timeseriesBody = new Map(options.body);
            const data = [
              {revision: 10, timestamp: 1000, avg: 1, count: 1, std: 0.5},
              {revision: 20, timestamp: 2000, avg: 2, count: 1, std: 0.5},
              {revision: 30, timestamp: 3000, avg: 3, count: 1, std: 0.5},
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
    window.fetch = originalFetch;
  });

  test('ReportFetcher', async function() {
    const reportInfo = {
      id: 42,
      name: 'test',
      modified: new Date(),
      owners: [],
      internal: false,
      template: {
        rows: [
          {
            label: 'test',
            testSuites: ['suite'],
            bots: ['master:bot'],
            measurement: 'ms',
            testCases: [],
          },
        ],
        statistics: ['avg', 'std'],
      },
    };
    const revisions = [10, 30];
    const fetcher = new ReportFetcher(reportInfo, revisions);
    let lastResult;
    for await (const result of fetcher) {
      lastResult = result;
    }
    assert.strictEqual(lastResult.id, reportInfo.id);
    assert.strictEqual(lastResult.name, reportInfo.name);
    assert.lengthOf(lastResult.errors, 0);
    assert.lengthOf(lastResult.timeseriesesByLine,
        reportInfo.template.rows.length);
    const tbr = lastResult.timeseriesesByLine[0].timeseriesesByRange;
    assert.strictEqual(tbr[0].range, revisions[0]);
    assert.strictEqual(tbr[1].range, revisions[1]);
    assert.lengthOf(tbr[0].timeserieses, 1);
    assert.lengthOf(tbr[1].timeserieses, 1);
    assert.strictEqual(tbr[0].timeserieses[0].statistics.mean, 1);
    assert.strictEqual(tbr[1].timeserieses[0].statistics.mean, 3);
  });

  test('RangeFinder', async function() {
    const finder = new RangeFinder();
    finder.addSource({
      suite: 'suite',
      measurement: 'measure',
      bot: 'master:bot',
      case: 'case',
      statistics: ['avg'],
      levelOfDetail: LEVEL_OF_DETAIL.XY,
    });
    const {minRevision, maxRevision} = await finder.findRange(20);
    assert.strictEqual(minRevision, 10);
    assert.strictEqual(maxRevision, 20);
  });
});
