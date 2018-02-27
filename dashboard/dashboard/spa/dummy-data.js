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

  function todo(msg) {
    // eslint-disable-next-line no-console
    console.log('TODO ' + msg);
  }

  return {
    dummyAlertsSources,
    dummyHistograms,
    dummyRecentBugs,
    dummyReleasingSection,
    dummyReleasingSources,
    dummyStoryTags,
    todo,
  };
});
