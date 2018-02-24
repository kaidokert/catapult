/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

tr.exportTo('cp', () => {
  const SHERIFFS = [
    'ARC Perf Sheriff',
    'Angle Perf Sheriff',
    'Binary Size Sheriff',
    'Blink Memory Mobile Sheriff',
    'Chrome OS Graphics Perf Sheriff',
    'Chrome OS Installer Perf Sheriff',
    'Chrome OS Perf Sheriff',
    'Chrome Perf Accessibility Sheriff',
    'Chromium Perf AV Sheriff',
    'Chromium Perf Sheriff - Sub-series',
    'Chromium Perf Sheriff',
    'CloudView Perf Sheriff',
    'Cronet Perf Sheriff',
    'Histogram FYI',
    'Jochen',
    'Mojo Perf Sheriff',
    'NaCl Perf Sheriff',
    'Network Service Sheriff',
    'OWP Storage Perf Sheriff',
    'Oilpan Perf Sheriff',
    'Pica Sheriff',
    'Power Perf Sheriff',
    'Service Worker Perf Sheriff',
    'Tracing Perftests Sheriff',
    'V8 Memory Perf Sheriff',
    'V8 Perf Sheriff',
    'WebView Perf Sheriff',
  ];

  function dummyAlertsSources() {
    const options = [{
      isExpanded: true,
      label: 'Sheriff',
      options: SHERIFFS,
      disabled: true,
    }];

    const releasingSources = [];
    for (const source of cp.dummyReleasingSources()) {
      for (const mstone of [62, 63, 64]) {
        releasingSources.push(`Releasing:M${mstone}:${source}`);
      }
    }
    options.push(cp.OptionGroup.groupValues(releasingSources)[0]);
    options.push(cp.OptionGroup.groupValues([
      'Bug:543210',
      'Bug:654321',
      'Bug:765432',
      'Bug:876543',
      'Bug:987654',
    ])[0]);
    return options;
  }

  function dummyReleasingSources() {
    return [
      'Input',
      'Loading',
      'Memory',
      'Power',
      'Public',
    ];
  }

  function dummyReleasingSection() {
    return {
      isOwner: Math.random() < 0.5,
      milestone: 64,
      isPreviousMilestone: true,
      isNextMilestone: false,
      anyAlerts: true,
      tables: [
        {
          title: 'health-plan-clankium-phone',
          currentVersion: '517411-73a',
          referenceVersion: '508578-c23',
          rows: [
            {
              isFirstInCategory: true,
              rowCount: 4,
              category: 'Foreground',
              href: '#',
              name: 'Java Heap',
              currentValue: 2,
              unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
              testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
              referenceValue: 1,
              percentDeltaValue: 1,
              percentDeltaUnit:
                tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
              deltaValue: 1,
              deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
            },
            {
              isFirstInCategory: false,
              href: '#',
              name: 'Native Heap',
              currentValue: 2,
              unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
              testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
              referenceValue: 1,
              percentDeltaValue: 1,
              percentDeltaUnit:
                tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
              deltaValue: 1,
              deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
            },
            {
              isFirstInCategory: false,
              href: '#',
              name: 'Ashmem',
              currentValue: 2,
              unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
              testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
              referenceValue: 1,
              percentDeltaValue: 1,
              percentDeltaUnit:
                tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
              deltaValue: 1,
              deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
            },
            {
              isFirstInCategory: false,
              href: '#',
              name: 'Overall PSS',
              currentValue: 2,
              unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
              testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
              referenceValue: 1,
              percentDeltaValue: 1,
              percentDeltaUnit:
                tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
              deltaValue: 1,
              deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
            },
            {
              isFirstInCategory: true,
              rowCount: 4,
              category: 'Background',
              href: '#',
              name: 'Java Heap',
              currentValue: 2,
              unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
              testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
              referenceValue: 1,
              percentDeltaValue: 1,
              percentDeltaUnit:
                tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
              deltaValue: 1,
              deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
            },
            {
              isFirstInCategory: false,
              href: '#',
              name: 'Native Heap',
              currentValue: 2,
              unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
              testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
              referenceValue: 1,
              percentDeltaValue: 1,
              percentDeltaUnit:
                tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
              deltaValue: 1,
              deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
            },
            {
              isFirstInCategory: false,
              href: '#',
              name: 'Ashmem',
              currentValue: 2,
              unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
              testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
              referenceValue: 1,
              percentDeltaValue: 1,
              percentDeltaUnit:
                tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
              deltaValue: 1,
              deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
            },
            {
              isFirstInCategory: false,
              href: '#',
              name: 'Overall PSS',
              currentValue: 2,
              unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
              testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
              referenceValue: 1,
              percentDeltaValue: 1,
              percentDeltaUnit:
                tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
              deltaValue: 1,
              deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
            },
          ],
        },
        {
          title: 'health-plan-clankium-low-end-phone',
          currentVersion: '517411-73a',
          referenceVersion: '508578-c23',
          rows: [
            {
              isFirstInCategory: true,
              rowCount: 4,
              category: 'Foreground',
              href: '#',
              name: 'Java Heap',
              testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
              currentValue: 2,
              unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
              referenceValue: 1,
              percentDeltaValue: 1,
              percentDeltaUnit:
                tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
              deltaValue: 1,
              deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
            },
            {
              isFirstInCategory: false,
              href: '#',
              name: 'Native Heap',
              testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
              currentValue: 2,
              unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
              referenceValue: 1,
              percentDeltaValue: 1,
              percentDeltaUnit:
                tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
              deltaValue: 1,
              deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
            },
            {
              isFirstInCategory: false,
              href: '#',
              name: 'Ashmem',
              testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
              currentValue: 2,
              unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
              referenceValue: 1,
              percentDeltaValue: 1,
              percentDeltaUnit:
                tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
              deltaValue: 1,
              deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
            },
            {
              isFirstInCategory: false,
              href: '#',
              name: 'Overall PSS',
              testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
              currentValue: 2,
              unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
              referenceValue: 1,
              percentDeltaValue: 1,
              percentDeltaUnit:
                tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
              deltaValue: 1,
              deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
            },
            {
              isFirstInCategory: true,
              rowCount: 4,
              testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
              category: 'Background',
              href: '#',
              name: 'Java Heap',
              currentValue: 2,
              unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
              referenceValue: 1,
              percentDeltaValue: 1,
              percentDeltaUnit:
                tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
              deltaValue: 1,
              deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
            },
            {
              isFirstInCategory: false,
              href: '#',
              name: 'Native Heap',
              testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
              currentValue: 2,
              unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
              referenceValue: 1,
              percentDeltaValue: 1,
              percentDeltaUnit:
                tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
              deltaValue: 1,
              deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
            },
            {
              isFirstInCategory: false,
              href: '#',
              name: 'Ashmem',
              testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
              currentValue: 2,
              unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
              referenceValue: 1,
              percentDeltaValue: 1,
              percentDeltaUnit:
                tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
              deltaValue: 1,
              deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
            },
            {
              isFirstInCategory: false,
              href: '#',
              name: 'Overall PSS',
              testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
              currentValue: 2,
              unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
              referenceValue: 1,
              percentDeltaValue: 1,
              percentDeltaUnit:
                tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
              deltaValue: 1,
              deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
            },
          ],
        },
      ],
    };
  }

  function dummyAlerts(improvements, triaged) {
    const alerts = [];
    for (let i = 0; i < 10; ++i) {
      const revs = new tr.b.math.Range();
      revs.addValue(parseInt(1e6 * Math.random()));
      revs.addValue(parseInt(1e6 * Math.random()));
      let bugId = undefined;
      if (triaged && (Math.random() > 0.5)) {
        if (Math.random() > 0.5) {
          bugId = -1;
        } else {
          bugId = 123456;
        }
      }
      alerts.push({
        bot: 'android-nexus5',
        bug_id: bugId,
        bug_labels: [],
        bug_components: [],
        end_revision: revs.max,
        improvement: improvements && (Math.random() > 0.5),
        key: tr.b.GUID.allocateSimple(),
        master: 'ChromiumPerf',
        median_after_anomaly: 100 * Math.random(),
        median_before_anomaly: 100 * Math.random(),
        start_revision: revs.min,
        test: 'fake' + i + '/case' + parseInt(Math.random() * 10),
        testsuite: 'system_health.common_desktop',
        units: 'ms',
      });
    }
    alerts.sort((x, y) => x.start_revision - y.start_revision);
    return alerts;
  }

  function dummyRecentBugs() {
    const bugs = [
      {
        id: '12345',
        status: 'WontFix',
        owner: {name: 'owner'},
        summary: '0% regression in nothing at 1:9999999',
      },
    ];
    for (let i = 0; i < 50; ++i) {
      bugs.push({
        id: 'TODO',
        status: 'TODO',
        owner: {name: 'TODO'},
        summary: 'TODO '.repeat(30),
      });
    }
    return bugs;
  }

  function dummyTimeseries(columns) {
    const data = [];
    const sequenceLength = 100;
    const nowMs = new Date() - 0;
    for (let i = 0; i < sequenceLength; i += 1) {
      // r_commit_pos, timestamp, value, error, d_statistic
      data.push([
        i,
        nowMs - ((sequenceLength - i - 1) * (2592105834 / 50)),
        parseInt(100 * Math.random()),
        parseInt(100 * Math.random()),
        parseInt(100 * Math.random()),
      ]);
    }
    return data;
  }

  async function dummyHistograms(section) {
    const fetchMark = tr.b.Timing.mark('fetch', 'histograms');
    cp.todo('fetch Histograms via cache');
    await tr.b.timeout(100);
    fetchMark.end();

    const histograms = new tr.v.HistogramSet();
    const lines = section.chartLayout.lines;
    const columns = [];
    for (let bi = 0; bi < section.chartLayout.xAxis.brushes.length; bi += 2) {
      columns.push(tr.b.formatDate(new Date(1.5e9 * Math.random())));
    }
    for (let i = 0; i < lines.length; ++i) {
      const testPath = lines[i].testPath;
      function inArray(x) {
        return x instanceof Array ? x : [x];
      }
      let stories = inArray(testPath[3]);
      if (section.testCase.selectedOptions.length === 0) {
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

  const MEASUREMENTS_BY_TEST_SUITE = new Map();

  function dummyMeasurements(testSuites) {
    return [
      'memory:a_size',
      'memory:b_size',
      'memory:c_size',
      'cpu:a',
      'cpu:b',
      'cpu:c',
    ];
  }

  function dummyBots(testSuites) {
    return [
      'master:bot0',
      'master:bot1',
      'master:bot2',
    ];
  }

  function dummyTestCases(testSuites) {
    return [
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
  }

  function dummyStoryTags(testSuites) {
    return [
      'audio_only',
      'case:blank',
      'case:browse',
      'case:load',
      'case:search',
      'group:chrome',
      'group:games',
      'group:media',
    ];
  }

  function dummyTestSuites() {
    return [
      'system_health.common_desktop',
      'system_health.common_mobile',
      'system_health.memory_desktop',
      'system_health.memory_mobile',
    ];
  }

  function todo(msg) {
    // eslint-disable-next-line no-console
    console.log('TODO ' + msg);
  }

  return {
    dummyAlerts,
    dummyAlertsSources,
    dummyBots,
    dummyHistograms,
    dummyMeasurements,
    dummyRecentBugs,
    dummyReleasingSection,
    dummyReleasingSources,
    dummyStoryTags,
    dummyTestCases,
    dummyTestSuites,
    dummyTimeseries,
    todo,
  };
});
