/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

tr.exportTo('cp', () => {
  // Collect all dummy data in this file in order to make it easier to see what
  // code is intended to be deleted when the backend is wired up.

  function dummyReleasingTable() {
  }

  function dummyAlerts() {
    return [
      {
        isExpanded: false,
        alerts: [
          {
            isSelected: true,
            guid: tr.b.GUID.allocateSimple(),
            isSelected: false,
            revisions: '543210 - 543221',
            bot: 'nexus5X',
            testSuite: 'system_health.common_mobile',
            measurement: 'story:power_avg',
            story: 'load:chrome:blank',
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
            percentDeltaValue: 1,
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
          },
        ],
      },
      {
        isExpanded: false,
        alerts: [
          {
            guid: tr.b.GUID.allocateSimple(),
            isSelected: false,
            revisions: '543222 - 543230',
            bot: 'nexus5X',
            testSuite: 'system_health.common_mobile',
            measurement: 'story:power_avg',
            story: 'load:chrome:blank',
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
            percentDeltaValue: 1,
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
          },
        ],
      },
      {
        isExpanded: false,
        alerts: [
          {
            guid: tr.b.GUID.allocateSimple(),
            isSelected: false,
            revisions: '543210 - 543221',
            bot: 'nexus5X',
            testSuite: 'system_health.common_mobile',
            measurement: 'story:power_avg',
            story: 'load:chrome:blank',
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
            percentDeltaValue: 1,
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
          },
          {
            guid: tr.b.GUID.allocateSimple(),
            isSelected: false,
            revisions: '543210 - 543221',
            bot: 'nexus5X',
            testSuite: 'system_health.common_mobile',
            measurement: 'story:power_avg',
            story: 'load:chrome:blank',
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
            percentDeltaValue: 1,
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
          },
          {
            guid: tr.b.GUID.allocateSimple(),
            isSelected: false,
            revisions: '543210 - 543221',
            bot: 'nexus5X',
            testSuite: 'system_health.common_mobile',
            measurement: 'story:power_avg',
            story: 'load:chrome:blank',
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
            percentDeltaValue: 1,
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
          },
          {
            guid: tr.b.GUID.allocateSimple(),
            isSelected: false,
            revisions: '543240 - 543250',
            bot: 'nexus5X',
            testSuite: 'system_health.common_mobile',
            measurement: 'story:power_avg',
            story: 'load:chrome:blank',
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
            percentDeltaValue: 1,
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
          },
        ],
      },
    ];
  }

  function dummyTimeseries() {
  }

  async function dummyHistograms(section) {
    const fetchMark = tr.b.Timing.mark('fetch', 'histograms');
    // eslint-disable-next-line no-console
    console.log('TODO fetch Histograms via cache');
    await tr.b.timeout(100);
    fetchMark.end();

    const histograms = new tr.v.HistogramSet();
    const lines = section.chartLayout.lines;
    const columns = [];
    for (let bi = 0; bi < section.chartLayout.brushes.length; bi += 2) {
      columns.push(tr.b.formatDate(new Date(1.5e9 * Math.random())));
    }
    for (let i = 0; i < lines.length; ++i) {
      const testPath = lines[i].testPath;
      function inArray(x) {
        return x instanceof Array ? x : [x];
      }
      let stories = inArray(testPath[3]);
      if (section.testPathComponents[3].selectedOptions.length === 0) {
        stories = [
          'load:news:cnn',
          'load:news:nytimes',
          'load:news:qq',
        ];
      }
      for (const col of columns) {
        histograms.createHistogram(
            testPath[2],
            tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            [Math.random() * 1e9], {
              diagnostics: new Map([
                [
                  tr.v.d.RESERVED_NAMES.BENCHMARKS,
                  new tr.v.d.GenericSet(inArray(testPath[0])),
                ],
                [
                  tr.v.d.RESERVED_NAMES.BOTS,
                  new tr.v.d.GenericSet(inArray(testPath[1])),
                ],
                [
                  tr.v.d.RESERVED_NAMES.STORIES,
                  new tr.v.d.GenericSet(stories),
                ],
                [
                  tr.v.d.RESERVED_NAMES.LABELS,
                  new tr.v.d.GenericSet([col]),
                ],
                [
                  tr.v.d.RESERVED_NAMES.NAME_COLORS,
                  new tr.v.d.GenericSet([lines[i].color.toString()]),
                ],
              ]),
            });
      }
    }
    return histograms;
  }

  return {
    dummyAlerts,
    dummyHistograms,
    dummyReleasingTable,
    dummyTimeseries,
  };
});
