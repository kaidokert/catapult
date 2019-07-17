/* Copyright 2019 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import {ReportMerger} from './report-merger.js';
import {assert} from 'chai';

suite('ReportMerger', function() {
  test('merge', function() {
    const timeseriesesByLine = [
      {
        lineDescriptor: {
          suites: ['suite'],
          measurement: 'measure',
          bots: ['master:bot'],
          cases: ['case'],
        },
        timeseriesesByRange: [
          {
            range: 20,
            timeserieses: [
              {
                revision: 10,
                unit: tr.b.Unit.byName.count,
                statistics: tr.b.math.RunningStatistics.fromDict([
                  3, 5, undefined, 2, 1, 10, 4,
                ]),
                fetchDescriptor: {
                  fetchIndex: 0,
                  suite: 'suite',
                  measurement: 'measure',
                  bot: 'master:bot',
                  case: 'case',
                },
              },
            ],
          },
          {
            range: 40,
            timeserieses: [
              {
                revision: 30,
                unit: tr.b.Unit.byName.count,
                statistics: tr.b.math.RunningStatistics.fromDict([
                  3, 5, undefined, 2, 1, 10, 4,
                ]),
                fetchDescriptor: {
                  fetchIndex: 0,
                  suite: 'suite',
                  measurement: 'measure',
                  bot: 'master:bot',
                  case: 'case',
                },
              },
            ],
          },
        ],
      },
    ];
    const revisions = [20, 40];
    const merged = new ReportMerger(timeseriesesByLine, revisions).mergedRows;
    assert.lengthOf(merged, 1);
    assert.strictEqual(10, [...merged[0].data[20].revisions][0]);
    assert.strictEqual(30, [...merged[0].data[40].revisions][0]);
    assert.strictEqual(2, merged[0].data[20].statistics.mean);
    assert.strictEqual(2, merged[0].data[40].statistics.mean);
  });
});
