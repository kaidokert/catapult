/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import {LEVEL_OF_DETAIL, TimeseriesRequest} from './timeseries-request.js';
import {RangeFinder} from './report-fetcher.js';
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
              {revision: 10, timestamp: 1000, avg: 1, count: 1},
              {revision: 20, timestamp: 2000, avg: 2, count: 1},
              {revision: 30, timestamp: 3000, avg: 3, count: 1},
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
