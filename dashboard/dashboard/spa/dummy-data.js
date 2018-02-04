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
    'Chromium Perf Sheriff',
    'Chromium Perf Sheriff - Sub-series',
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
    const sheriffOptions = SHERIFFS.map(value => {
      return {
        value,
        label: value.replace(/ Perf Sheriff$/, '').replace(/ Sheriff$/, ''),
      };
    });
    sheriffOptions.sort((x, y) => x.label.localeCompare(y.label));

    const options = [{
      isExpanded: true,
      label: 'Sheriff',
      options: sheriffOptions,
      disabled: true,
    }];

    const releasingSources = [];
    for (const source of cp.dummyReleasingSources()) {
      for (const mstone of [62, 63, 64]) {
        releasingSources.push(`Releasing:M${mstone}:${source}`);
      }
    }
    options.push.apply(options, cp.OptionGroup.groupValues(releasingSources));
    options.push.apply(options, cp.OptionGroup.groupValues([
      'Bug:543210',
      'Bug:654321',
      'Bug:765432',
      'Bug:876543',
      'Bug:987654',
    ]));
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

  function dummyTimeseries() {
    const data = [];
    const sequenceLength = 100;
    for (let i = 0; i < sequenceLength; i += 1) {
      const value = parseInt(100 * Math.random());
      data.push({
        revision: i,
        value,
      });
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
    for (let bi = 0; bi < section.chartLayout.xBrushes.length; bi += 2) {
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
    const measurements = new Set();
    for (const testSuite of testSuites) {
      if (!MEASUREMENTS_BY_TEST_SUITE.has(testSuite)) continue;
      for (const measurement of MEASUREMENTS_BY_TEST_SUITE.get(testSuite)) {
        measurements.add(measurement);
      }
    }
    return measurements;
  }

  const BOTS_BY_TEST_SUITE = new Map();

  function dummyBots(testSuites) {
    const bots = new Set();
    for (const testSuite of testSuites) {
      if (!BOTS_BY_TEST_SUITE.has(testSuite)) continue;
      for (const bot of BOTS_BY_TEST_SUITE.get(testSuite)) {
        bots.add(bot);
      }
    }
    return bots;
  }

  const TEST_CASES_BY_TEST_SUITE = new Map();

  function dummyTestCases(testSuites) {
    const testCases = new Set();
    for (const testSuite of testSuites) {
      if (!TEST_CASES_BY_TEST_SUITE.has(testSuite)) continue;
      for (const testCase of TEST_CASES_BY_TEST_SUITE.get(testSuite)) {
        testCases.add(testCase);
      }
    }
    return testCases;
  }

  function dummyStoryTags(testSuites) {
    if (testSuites.filter(s => s.startsWith('system_health')).length === 0) {
      return [];
    }
    return [
      'audio_only',
      'case:blank',
      'case:browse',
      'case:load',
      'case:search',
      'group:about',
      'group:games',
      'group:media',
      'group:news',
      'group:portal',
      'group:search',
      'group:social',
      'group:tools',
      'is_4k',
      'is_50fps',
      'video_only',
      'vorbis',
      'vp8',
      'vp9',
    ];
  }

  const SYSTEM_HEALTH_TEST_SUITES = [
    'system_health.common_desktop',
    'system_health.common_mobile',
    'system_health.memory_desktop',
    'system_health.memory_mobile',
  ];

  const V8_TEST_SUITES = [
    'v8:ARES-6',
    'v8:ARES-6-Future',
    'v8:AreWeFastYet',
    'v8:BigNum',
    'v8:Compile',
    'v8:Embenchen',
    'v8:Emscripten',
    'v8:JSBench',
    'v8:JSTests',
    'v8:JetStream',
    'v8:JetStream-wasm',
    'v8:JetStream-wasm-interpreted',
    'v8:KrakenOrig',
    'v8:Liftoff-Micro',
    'v8:LoadTime',
    'v8:Massive',
    'v8:Memory',
    'v8:Micro',
    'v8:Octane2.1',
    'v8:Octane2.1-Future',
    'v8:Octane2.1-Harmony',
    'v8:Octane2.1-NoOpt',
    'v8:Octane2.1ES6',
    'v8:Promises',
    'v8:PunchStartup',
    'v8:RegExp',
    'v8:Ritz',
    'v8:RuntimeStats',
    'v8:SixSpeed',
    'v8:Spec2k',
    'v8:SunSpider',
    'v8:SunSpiderGolem',
    'v8:TraceurES6',
    'v8:TypeScript',
    'v8:Unity',
    'v8:Unity-Future',
    'v8:Unity-Liftoff',
    'v8:Unity-asm-wasm',
    'v8:Wasm',
    'v8:Wasm-Future',
    'v8:web-tooling-benchmark',
  ];

  function dummyTestSuites() {
    return [].concat(
        SYSTEM_HEALTH_TEST_SUITES,
        cp.OptionGroup.groupValues(V8_TEST_SUITES));
  }

  function todo(msg) {
    // eslint-disable-next-line no-console
    console.log('TODO ' + msg);
  }

  /* eslint-disable max-len */

  MEASUREMENTS_BY_TEST_SUITE.set('system_health.common_mobile', [
    'benchmark_duration',
    'browser_accessibility_events',
    'clock_sync_latency_linux_clock_monotonic_to_telemetry',
    'cpuPercentage:all_processes:all_threads:Load:Successful',
    'cpuPercentage:all_processes:all_threads:all_stages:all_initiators',
    'cpuPercentage:browser_process:CrBrowserMain:all_stages:' +
    'all_initiators',
    'cpuPercentage:browser_process:all_threads:all_stages:all_initiators',
    'cpuPercentage:gpu_process:all_threads:all_stages:all_initiators',
    'cpuPercentage:renderer_processes:CrRendererMain:all_stages:' +
    'all_initiators',
    'cpuPercentage:renderer_processes:all_threads:all_stages:' +
    'all_initiators',
    'cpuTime:all_processes:all_threads:Load:Successful',
    'cpuTime:all_processes:all_threads:all_stages:all_initiators',
    'cpuTime:browser_process:CrBrowserMain:all_stages:all_initiators',
    'cpuTime:browser_process:all_threads:all_stages:all_initiators',
    'cpuTime:gpu_process:all_threads:all_stages:all_initiators',
    'cpuTime:renderer_processes:CrRendererMain:all_stages:all_initiators',
    'cpuTime:renderer_processes:all_threads:all_stages:all_initiators',
    'cpuTimeToFirstMeaningfulPaint:composite',
    'cpuTimeToFirstMeaningfulPaint:gc',
    'cpuTimeToFirstMeaningfulPaint:gpu',
    'cpuTimeToFirstMeaningfulPaint:iframe_creation',
    'cpuTimeToFirstMeaningfulPaint:imageDecode',
    'cpuTimeToFirstMeaningfulPaint:input',
    'cpuTimeToFirstMeaningfulPaint:layout',
    'cpuTimeToFirstMeaningfulPaint:net',
    'cpuTimeToFirstMeaningfulPaint:other',
    'cpuTimeToFirstMeaningfulPaint:overhead',
    'cpuTimeToFirstMeaningfulPaint:parseHTML',
    'cpuTimeToFirstMeaningfulPaint:raster',
    'cpuTimeToFirstMeaningfulPaint:record',
    'cpuTimeToFirstMeaningfulPaint:renderer_misc',
    'cpuTimeToFirstMeaningfulPaint:resource_loading',
    'cpuTimeToFirstMeaningfulPaint:script_execute',
    'cpuTimeToFirstMeaningfulPaint:script_parse_and_compile',
    'cpuTimeToFirstMeaningfulPaint:startup',
    'cpuTimeToFirstMeaningfulPaint:style',
    'cpuTimeToFirstMeaningfulPaint:v8_runtime',
    'cpuTimeToFirstMeaningfulPaint',
    'cpu_time_percentage',
    'interactive:500ms_window:renderer_eqt_cpu',
    'interactive:500ms_window:renderer_eqt',
    'peak_event_rate',
    'peak_event_size_rate',
    'render_accessibility_events',
    'render_accessibility_locations',
    'timeToFirstContentfulPaint:blocked_on_network',
    'timeToFirstContentfulPaint:composite',
    'timeToFirstContentfulPaint:gc',
    'timeToFirstContentfulPaint:gpu',
    'timeToFirstContentfulPaint:idle',
    'timeToFirstContentfulPaint:iframe_creation',
    'timeToFirstContentfulPaint:imageDecode',
    'timeToFirstContentfulPaint:input',
    'timeToFirstContentfulPaint:layout',
    'timeToFirstContentfulPaint:net',
    'timeToFirstContentfulPaint:other',
    'timeToFirstContentfulPaint:overhead',
    'timeToFirstContentfulPaint:parseHTML',
    'timeToFirstContentfulPaint:raster',
    'timeToFirstContentfulPaint:record',
    'timeToFirstContentfulPaint:renderer_misc',
    'timeToFirstContentfulPaint:resource_loading',
    'timeToFirstContentfulPaint:script_execute',
    'timeToFirstContentfulPaint:script_parse_and_compile',
    'timeToFirstContentfulPaint:startup',
    'timeToFirstContentfulPaint:style',
    'timeToFirstContentfulPaint:v8_runtime',
    'timeToFirstContentfulPaint',
    'timeToFirstInteractive:blocked_on_network',
    'timeToFirstInteractive:composite',
    'timeToFirstInteractive:gc',
    'timeToFirstInteractive:gpu',
    'timeToFirstInteractive:idle',
    'timeToFirstInteractive:iframe_creation',
    'timeToFirstInteractive:imageDecode',
    'timeToFirstInteractive:input',
    'timeToFirstInteractive:layout',
    'timeToFirstInteractive:net',
    'timeToFirstInteractive:other',
    'timeToFirstInteractive:overhead',
    'timeToFirstInteractive:parseHTML',
    'timeToFirstInteractive:raster',
    'timeToFirstInteractive:record',
    'timeToFirstInteractive:renderer_misc',
    'timeToFirstInteractive:resource_loading',
    'timeToFirstInteractive:script_execute',
    'timeToFirstInteractive:script_parse_and_compile',
    'timeToFirstInteractive:startup',
    'timeToFirstInteractive:style',
    'timeToFirstInteractive:v8_runtime',
    'timeToFirstInteractive',
    'timeToFirstMeaningfulPaint:blocked_on_network',
    'timeToFirstMeaningfulPaint:composite',
    'timeToFirstMeaningfulPaint:gc',
    'timeToFirstMeaningfulPaint:gpu',
    'timeToFirstMeaningfulPaint:idle',
    'timeToFirstMeaningfulPaint:iframe_creation',
    'timeToFirstMeaningfulPaint:imageDecode',
    'timeToFirstMeaningfulPaint:input',
    'timeToFirstMeaningfulPaint:layout',
    'timeToFirstMeaningfulPaint:net',
    'timeToFirstMeaningfulPaint:other',
    'timeToFirstMeaningfulPaint:overhead',
    'timeToFirstMeaningfulPaint:parseHTML',
    'timeToFirstMeaningfulPaint:raster',
    'timeToFirstMeaningfulPaint:record',
    'timeToFirstMeaningfulPaint:renderer_misc',
    'timeToFirstMeaningfulPaint:resource_loading',
    'timeToFirstMeaningfulPaint:script_execute',
    'timeToFirstMeaningfulPaint:script_parse_and_compile',
    'timeToFirstMeaningfulPaint:startup',
    'timeToFirstMeaningfulPaint:style',
    'timeToFirstMeaningfulPaint:v8_runtime',
    'timeToFirstMeaningfulPaint',
    'timeToFirstPaint',
    'timeToOnload',
    'total:500ms_window:renderer_eqt_cpu',
    'total:500ms_window:renderer_eqt',
    'trace_import_duration',
    'trace_size',
  ]);
  MEASUREMENTS_BY_TEST_SUITE.set('system_health.common_desktop',
      MEASUREMENTS_BY_TEST_SUITE.get('system_health.common_mobile'));

  MEASUREMENTS_BY_TEST_SUITE.set('system_health.memory_mobile', [
    'benchmark_duration',
    'memory:chrome:all_processes:dump_count:background',
    'memory:chrome:all_processes:dump_count:detailed',
    'memory:chrome:all_processes:dump_count:heap_profiler',
    'memory:chrome:all_processes:dump_count:light',
    'memory:chrome:all_processes:dump_count',
    'memory:chrome:all_processes:process_count',
    'memory:chrome:all_processes:reported_by_chrome:allocated_objects_size',
    'memory:chrome:all_processes:reported_by_chrome:blink_gc:allocated_objects_size',
    'memory:chrome:all_processes:reported_by_chrome:blink_gc:effective_size',
    'memory:chrome:all_processes:reported_by_chrome:cc:effective_size',
    'memory:chrome:all_processes:reported_by_chrome:cc:locked_size',
    'memory:chrome:all_processes:reported_by_chrome:components:effective_size',
    'memory:chrome:all_processes:reported_by_chrome:discardable:effective_size',
    'memory:chrome:all_processes:reported_by_chrome:discardable:locked_size',
    'memory:chrome:all_processes:reported_by_chrome:dom_storage:effective_size',
    'memory:chrome:all_processes:reported_by_chrome:effective_size',
    'memory:chrome:all_processes:reported_by_chrome:font_caches:effective_size',
    'memory:chrome:all_processes:reported_by_chrome:gpu:effective_size',
    'memory:chrome:all_processes:reported_by_chrome:gpumemorybuffer:effective_size',
    'memory:chrome:all_processes:reported_by_chrome:java_heap:allocated_objects_size',
    'memory:chrome:all_processes:reported_by_chrome:java_heap:effective_size',
    'memory:chrome:all_processes:reported_by_chrome:leveldatabase:effective_size',
    'memory:chrome:all_processes:reported_by_chrome:leveldb:effective_size',
    'memory:chrome:all_processes:reported_by_chrome:locked_size',
    'memory:chrome:all_processes:reported_by_chrome:malloc:allocated_objects_size',
    'memory:chrome:all_processes:reported_by_chrome:malloc:effective_size',
    'memory:chrome:all_processes:reported_by_chrome:media:effective_size',
    'memory:chrome:all_processes:reported_by_chrome:net:effective_size',
    'memory:chrome:all_processes:reported_by_chrome:partition_alloc:allocated_objects_size',
    'memory:chrome:all_processes:reported_by_chrome:partition_alloc:effective_size',
    'memory:chrome:all_processes:reported_by_chrome:peak_size',
    'memory:chrome:all_processes:reported_by_chrome:shared_memory:effective_size',
    'memory:chrome:all_processes:reported_by_chrome:site_storage:effective_size',
    'memory:chrome:all_processes:reported_by_chrome:skia:effective_size',
    'memory:chrome:all_processes:reported_by_chrome:sqlite:effective_size',
    'memory:chrome:all_processes:reported_by_chrome:tracing:effective_size',
    'memory:chrome:all_processes:reported_by_chrome:ui:effective_size',
    'memory:chrome:all_processes:reported_by_chrome:v8:allocated_by_malloc:effective_size',
    'memory:chrome:all_processes:reported_by_chrome:v8:allocated_by_malloc:peak_size',
    'memory:chrome:all_processes:reported_by_chrome:v8:allocated_objects_size',
    'memory:chrome:all_processes:reported_by_chrome:v8:effective_size',
    'memory:chrome:all_processes:reported_by_chrome:v8:heap:allocated_objects_size',
    'memory:chrome:all_processes:reported_by_chrome:v8:heap:code_space:allocated_objects_size',
    'memory:chrome:all_processes:reported_by_chrome:v8:heap:code_space:effective_size',
    'memory:chrome:all_processes:reported_by_chrome:v8:heap:effective_size',
    'memory:chrome:all_processes:reported_by_chrome:v8:heap:large_object_space:allocated_objects_size',
    'memory:chrome:all_processes:reported_by_chrome:v8:heap:large_object_space:effective_size',
    'memory:chrome:all_processes:reported_by_chrome:v8:heap:map_space:allocated_objects_size',
    'memory:chrome:all_processes:reported_by_chrome:v8:heap:map_space:effective_size',
    'memory:chrome:all_processes:reported_by_chrome:v8:heap:new_space:allocated_objects_size',
    'memory:chrome:all_processes:reported_by_chrome:v8:heap:new_space:effective_size',
    'memory:chrome:all_processes:reported_by_chrome:v8:heap:old_space:allocated_objects_size',
    'memory:chrome:all_processes:reported_by_chrome:v8:heap:old_space:effective_size',
    'memory:chrome:all_processes:reported_by_chrome:v8:peak_size',
    'memory:chrome:all_processes:reported_by_chrome:web_cache:effective_size',
    'memory:chrome:all_processes:reported_by_os:gpu_memory:gl:proportional_resident_size',
    'memory:chrome:all_processes:reported_by_os:gpu_memory:graphics:proportional_resident_size',
    'memory:chrome:all_processes:reported_by_os:gpu_memory:other:proportional_resident_size',
    'memory:chrome:all_processes:reported_by_os:gpu_memory:proportional_resident_size',
    'memory:chrome:all_processes:reported_by_os:peak_resident_size',
    'memory:chrome:all_processes:reported_by_os:private_dirty_size',
    'memory:chrome:all_processes:reported_by_os:private_footprint_size',
    'memory:chrome:all_processes:reported_by_os:proportional_resident_size',
    'memory:chrome:all_processes:reported_by_os:resident_size',
    'memory:chrome:all_processes:reported_by_os:system_memory:ashmem:private_dirty_size',
    'memory:chrome:all_processes:reported_by_os:system_memory:ashmem:proportional_resident_size',
    'memory:chrome:all_processes:reported_by_os:system_memory:java_heap:private_dirty_size',
    'memory:chrome:all_processes:reported_by_os:system_memory:java_heap:proportional_resident_size',
    'memory:chrome:all_processes:reported_by_os:system_memory:native_heap:private_dirty_size',
    'memory:chrome:all_processes:reported_by_os:system_memory:native_heap:proportional_resident_size',
    'memory:chrome:all_processes:reported_by_os:system_memory:peak_resident_size',
    'memory:chrome:all_processes:reported_by_os:system_memory:private_dirty_size',
    'memory:chrome:all_processes:reported_by_os:system_memory:private_footprint_size',
    'memory:chrome:all_processes:reported_by_os:system_memory:proportional_resident_size',
    'memory:chrome:all_processes:reported_by_os:system_memory:resident_size',
    'memory:chrome:all_processes:reported_by_os:system_memory:stack:private_dirty_size',
    'memory:chrome:all_processes:reported_by_os:system_memory:stack:proportional_resident_size',
    'memory:chrome:browser_process:process_count',
    'memory:chrome:browser_process:reported_by_chrome:allocated_objects_size',
    'memory:chrome:browser_process:reported_by_chrome:blink_gc:allocated_objects_size',
    'memory:chrome:browser_process:reported_by_chrome:blink_gc:effective_size',
    'memory:chrome:browser_process:reported_by_chrome:cc:effective_size',
    'memory:chrome:browser_process:reported_by_chrome:components:effective_size',
    'memory:chrome:browser_process:reported_by_chrome:discardable:effective_size',
    'memory:chrome:browser_process:reported_by_chrome:discardable:locked_size',
    'memory:chrome:browser_process:reported_by_chrome:dom_storage:effective_size',
    'memory:chrome:browser_process:reported_by_chrome:effective_size',
    'memory:chrome:browser_process:reported_by_chrome:font_caches:effective_size',
    'memory:chrome:browser_process:reported_by_chrome:gpu:effective_size',
    'memory:chrome:browser_process:reported_by_chrome:gpumemorybuffer:effective_size',
    'memory:chrome:browser_process:reported_by_chrome:java_heap:allocated_objects_size',
    'memory:chrome:browser_process:reported_by_chrome:java_heap:effective_size',
    'memory:chrome:browser_process:reported_by_chrome:leveldatabase:effective_size',
    'memory:chrome:browser_process:reported_by_chrome:leveldb:effective_size',
    'memory:chrome:browser_process:reported_by_chrome:locked_size',
    'memory:chrome:browser_process:reported_by_chrome:malloc:allocated_objects_size',
    'memory:chrome:browser_process:reported_by_chrome:malloc:effective_size',
    'memory:chrome:browser_process:reported_by_chrome:net:effective_size',
    'memory:chrome:browser_process:reported_by_chrome:partition_alloc:allocated_objects_size',
    'memory:chrome:browser_process:reported_by_chrome:partition_alloc:effective_size',
    'memory:chrome:browser_process:reported_by_chrome:shared_memory:effective_size',
    'memory:chrome:browser_process:reported_by_chrome:site_storage:effective_size',
    'memory:chrome:browser_process:reported_by_chrome:skia:effective_size',
    'memory:chrome:browser_process:reported_by_chrome:sqlite:effective_size',
    'memory:chrome:browser_process:reported_by_chrome:tracing:effective_size',
    'memory:chrome:browser_process:reported_by_chrome:ui:effective_size',
    'memory:chrome:browser_process:reported_by_os:gpu_memory:gl:proportional_resident_size',
    'memory:chrome:browser_process:reported_by_os:gpu_memory:graphics:proportional_resident_size',
    'memory:chrome:browser_process:reported_by_os:gpu_memory:other:proportional_resident_size',
    'memory:chrome:browser_process:reported_by_os:gpu_memory:proportional_resident_size',
    'memory:chrome:browser_process:reported_by_os:peak_resident_size',
    'memory:chrome:browser_process:reported_by_os:private_dirty_size',
    'memory:chrome:browser_process:reported_by_os:private_footprint_size',
    'memory:chrome:browser_process:reported_by_os:proportional_resident_size',
    'memory:chrome:browser_process:reported_by_os:resident_size',
    'memory:chrome:browser_process:reported_by_os:system_memory:ashmem:private_dirty_size',
    'memory:chrome:browser_process:reported_by_os:system_memory:ashmem:proportional_resident_size',
    'memory:chrome:browser_process:reported_by_os:system_memory:java_heap:private_dirty_size',
    'memory:chrome:browser_process:reported_by_os:system_memory:java_heap:proportional_resident_size',
    'memory:chrome:browser_process:reported_by_os:system_memory:native_heap:private_dirty_size',
    'memory:chrome:browser_process:reported_by_os:system_memory:native_heap:proportional_resident_size',
    'memory:chrome:browser_process:reported_by_os:system_memory:peak_resident_size',
    'memory:chrome:browser_process:reported_by_os:system_memory:private_dirty_size',
    'memory:chrome:browser_process:reported_by_os:system_memory:private_footprint_size',
    'memory:chrome:browser_process:reported_by_os:system_memory:proportional_resident_size',
    'memory:chrome:browser_process:reported_by_os:system_memory:resident_size',
    'memory:chrome:browser_process:reported_by_os:system_memory:stack:private_dirty_size',
    'memory:chrome:browser_process:reported_by_os:system_memory:stack:proportional_resident_size',
    'memory:chrome:gpu_process:process_count',
    'memory:chrome:gpu_process:reported_by_chrome:allocated_objects_size',
    'memory:chrome:gpu_process:reported_by_chrome:effective_size',
    'memory:chrome:gpu_process:reported_by_chrome:gpu:effective_size',
    'memory:chrome:gpu_process:reported_by_chrome:java_heap:allocated_objects_size',
    'memory:chrome:gpu_process:reported_by_chrome:java_heap:effective_size',
    'memory:chrome:gpu_process:reported_by_chrome:malloc:allocated_objects_size',
    'memory:chrome:gpu_process:reported_by_chrome:malloc:effective_size',
    'memory:chrome:gpu_process:reported_by_chrome:shared_memory:effective_size',
    'memory:chrome:gpu_process:reported_by_chrome:tracing:effective_size',
    'memory:chrome:gpu_process:reported_by_os:gpu_memory:gl:proportional_resident_size',
    'memory:chrome:gpu_process:reported_by_os:gpu_memory:graphics:proportional_resident_size',
    'memory:chrome:gpu_process:reported_by_os:gpu_memory:other:proportional_resident_size',
    'memory:chrome:gpu_process:reported_by_os:gpu_memory:proportional_resident_size',
    'memory:chrome:gpu_process:reported_by_os:peak_resident_size',
    'memory:chrome:gpu_process:reported_by_os:private_dirty_size',
    'memory:chrome:gpu_process:reported_by_os:private_footprint_size',
    'memory:chrome:gpu_process:reported_by_os:proportional_resident_size',
    'memory:chrome:gpu_process:reported_by_os:resident_size',
    'memory:chrome:gpu_process:reported_by_os:system_memory:ashmem:private_dirty_size',
    'memory:chrome:gpu_process:reported_by_os:system_memory:ashmem:proportional_resident_size',
    'memory:chrome:gpu_process:reported_by_os:system_memory:java_heap:private_dirty_size',
    'memory:chrome:gpu_process:reported_by_os:system_memory:java_heap:proportional_resident_size',
    'memory:chrome:gpu_process:reported_by_os:system_memory:native_heap:private_dirty_size',
    'memory:chrome:gpu_process:reported_by_os:system_memory:native_heap:proportional_resident_size',
    'memory:chrome:gpu_process:reported_by_os:system_memory:peak_resident_size',
    'memory:chrome:gpu_process:reported_by_os:system_memory:private_dirty_size',
    'memory:chrome:gpu_process:reported_by_os:system_memory:private_footprint_size',
    'memory:chrome:gpu_process:reported_by_os:system_memory:proportional_resident_size',
    'memory:chrome:gpu_process:reported_by_os:system_memory:resident_size',
    'memory:chrome:gpu_process:reported_by_os:system_memory:stack:private_dirty_size',
    'memory:chrome:gpu_process:reported_by_os:system_memory:stack:proportional_resident_size',
    'memory:chrome:renderer_processes:process_count',
    'memory:chrome:renderer_processes:reported_by_chrome:allocated_objects_size',
    'memory:chrome:renderer_processes:reported_by_chrome:blink_gc:allocated_objects_size',
    'memory:chrome:renderer_processes:reported_by_chrome:blink_gc:effective_size',
    'memory:chrome:renderer_processes:reported_by_chrome:cc:effective_size',
    'memory:chrome:renderer_processes:reported_by_chrome:cc:locked_size',
    'memory:chrome:renderer_processes:reported_by_chrome:discardable:effective_size',
    'memory:chrome:renderer_processes:reported_by_chrome:discardable:locked_size',
    'memory:chrome:renderer_processes:reported_by_chrome:effective_size',
    'memory:chrome:renderer_processes:reported_by_chrome:font_caches:effective_size',
    'memory:chrome:renderer_processes:reported_by_chrome:gpu:effective_size',
    'memory:chrome:renderer_processes:reported_by_chrome:java_heap:allocated_objects_size',
    'memory:chrome:renderer_processes:reported_by_chrome:java_heap:effective_size',
    'memory:chrome:renderer_processes:reported_by_chrome:locked_size',
    'memory:chrome:renderer_processes:reported_by_chrome:malloc:allocated_objects_size',
    'memory:chrome:renderer_processes:reported_by_chrome:malloc:effective_size',
    'memory:chrome:renderer_processes:reported_by_chrome:media:effective_size',
    'memory:chrome:renderer_processes:reported_by_chrome:partition_alloc:allocated_objects_size',
    'memory:chrome:renderer_processes:reported_by_chrome:partition_alloc:effective_size',
    'memory:chrome:renderer_processes:reported_by_chrome:peak_size',
    'memory:chrome:renderer_processes:reported_by_chrome:shared_memory:effective_size',
    'memory:chrome:renderer_processes:reported_by_chrome:skia:effective_size',
    'memory:chrome:renderer_processes:reported_by_chrome:tracing:effective_size',
    'memory:chrome:renderer_processes:reported_by_chrome:v8:allocated_by_malloc:effective_size',
    'memory:chrome:renderer_processes:reported_by_chrome:v8:allocated_by_malloc:peak_size',
    'memory:chrome:renderer_processes:reported_by_chrome:v8:allocated_objects_size',
    'memory:chrome:renderer_processes:reported_by_chrome:v8:effective_size',
    'memory:chrome:renderer_processes:reported_by_chrome:v8:heap:allocated_objects_size',
    'memory:chrome:renderer_processes:reported_by_chrome:v8:heap:code_space:allocated_objects_size',
    'memory:chrome:renderer_processes:reported_by_chrome:v8:heap:code_space:effective_size',
    'memory:chrome:renderer_processes:reported_by_chrome:v8:heap:effective_size',
    'memory:chrome:renderer_processes:reported_by_chrome:v8:heap:large_object_space:allocated_objects_size',
    'memory:chrome:renderer_processes:reported_by_chrome:v8:heap:large_object_space:effective_size',
    'memory:chrome:renderer_processes:reported_by_chrome:v8:heap:map_space:allocated_objects_size',
    'memory:chrome:renderer_processes:reported_by_chrome:v8:heap:map_space:effective_size',
    'memory:chrome:renderer_processes:reported_by_chrome:v8:heap:new_space:allocated_objects_size',
    'memory:chrome:renderer_processes:reported_by_chrome:v8:heap:new_space:effective_size',
    'memory:chrome:renderer_processes:reported_by_chrome:v8:heap:old_space:allocated_objects_size',
    'memory:chrome:renderer_processes:reported_by_chrome:v8:heap:old_space:effective_size',
    'memory:chrome:renderer_processes:reported_by_chrome:v8:peak_size',
    'memory:chrome:renderer_processes:reported_by_chrome:web_cache:effective_size',
    'memory:chrome:renderer_processes:reported_by_os:peak_resident_size',
    'memory:chrome:renderer_processes:reported_by_os:private_dirty_size',
    'memory:chrome:renderer_processes:reported_by_os:private_footprint_size',
    'memory:chrome:renderer_processes:reported_by_os:proportional_resident_size',
    'memory:chrome:renderer_processes:reported_by_os:resident_size',
    'memory:chrome:renderer_processes:reported_by_os:system_memory:ashmem:private_dirty_size',
    'memory:chrome:renderer_processes:reported_by_os:system_memory:ashmem:proportional_resident_size',
    'memory:chrome:renderer_processes:reported_by_os:system_memory:java_heap:private_dirty_size',
    'memory:chrome:renderer_processes:reported_by_os:system_memory:java_heap:proportional_resident_size',
    'memory:chrome:renderer_processes:reported_by_os:system_memory:native_heap:private_dirty_size',
    'memory:chrome:renderer_processes:reported_by_os:system_memory:native_heap:proportional_resident_size',
    'memory:chrome:renderer_processes:reported_by_os:system_memory:peak_resident_size',
    'memory:chrome:renderer_processes:reported_by_os:system_memory:private_dirty_size',
    'memory:chrome:renderer_processes:reported_by_os:system_memory:private_footprint_size',
    'memory:chrome:renderer_processes:reported_by_os:system_memory:proportional_resident_size',
    'memory:chrome:renderer_processes:reported_by_os:system_memory:resident_size',
    'memory:chrome:renderer_processes:reported_by_os:system_memory:stack:private_dirty_size',
    'memory:chrome:renderer_processes:reported_by_os:system_memory:stack:proportional_resident_size',
  ]);

  MEASUREMENTS_BY_TEST_SUITE.set('v8:KrakenOrig', ['Total', 'ai-astar', 'audio-beat-detection', 'audio-dft', 'audio-fft', 'audio-oscillator', 'imaging-darkroom', 'imaging-desaturate', 'imaging-gaussian-blur', 'json-parse-financial', 'json-stringify-tinderbox', 'stanford-crypto-aes', 'stanford-crypto-ccm', 'stanford-crypto-pbkdf2', 'stanford-crypto-sha256-iterative']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:TypeScript', ['Performance']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:JetStream-wasm-interpreted', ['bigfib', 'quicksort', 'towers']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:Ritz', ['EvaluateFibonacci', 'SortNumbers', 'VLookupCells']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:Memory', ['ReservedMemoryContext', 'ReservedMemoryIsolate', 'SnapshotSizeBuiltins', 'SnapshotSizeContext', 'SnapshotSizeStartup']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:Unity-Liftoff', ['2D Physics Boxes:CodeSize', '2D Physics Boxes:Compile', '2D Physics Boxes:Instantiate', '2D Physics Boxes:LiftoffCompile', '2D Physics Boxes:LiftoffFunctions', '2D Physics Boxes:LiftoffUnsupportedFunctions', '2D Physics Boxes:RelocSize', '2D Physics Boxes:Runtime', '2D Physics Spheres:CodeSize', '2D Physics Spheres:Compile', '2D Physics Spheres:Instantiate', '2D Physics Spheres:LiftoffCompile', '2D Physics Spheres:LiftoffFunctions', '2D Physics Spheres:LiftoffUnsupportedFunctions', '2D Physics Spheres:RelocSize', '2D Physics Spheres:Runtime', 'Animation and Skinning:CodeSize', 'Animation and Skinning:Compile', 'Animation and Skinning:Instantiate', 'Animation and Skinning:LiftoffCompile', 'Animation and Skinning:LiftoffFunctions', 'Animation and Skinning:LiftoffUnsupportedFunctions', 'Animation and Skinning:RelocSize', 'Animation and Skinning:Runtime', 'Asteroid Field:CodeSize', 'Asteroid Field:Compile', 'Asteroid Field:Instantiate', 'Asteroid Field:LiftoffCompile', 'Asteroid Field:LiftoffFunctions', 'Asteroid Field:LiftoffUnsupportedFunctions', 'Asteroid Field:RelocSize', 'Asteroid Field:Runtime', 'Cryptohash:CodeSize', 'Cryptohash:Compile', 'Cryptohash:Instantiate', 'Cryptohash:LiftoffCompile', 'Cryptohash:LiftoffFunctions', 'Cryptohash:LiftoffUnsupportedFunctions', 'Cryptohash:RelocSize', 'Cryptohash:Runtime', 'Instantiate and Destroy:CodeSize', 'Instantiate and Destroy:Compile', 'Instantiate and Destroy:Instantiate', 'Instantiate and Destroy:LiftoffCompile', 'Instantiate and Destroy:LiftoffFunctions', 'Instantiate and Destroy:LiftoffUnsupportedFunctions', 'Instantiate and Destroy:RelocSize', 'Instantiate and Destroy:Runtime', 'Mandelbrot:CodeSize', 'Mandelbrot:Compile', 'Mandelbrot:Instantiate', 'Mandelbrot:LiftoffCompile', 'Mandelbrot:LiftoffFunctions', 'Mandelbrot:LiftoffUnsupportedFunctions', 'Mandelbrot:RelocSize', 'Mandelbrot:Runtime', 'Physics Spheres:CodeSize', 'Physics Spheres:Compile', 'Physics Spheres:Instantiate', 'Physics Spheres:LiftoffCompile', 'Physics Spheres:LiftoffFunctions', 'Physics Spheres:LiftoffUnsupportedFunctions', 'Physics Spheres:RelocSize', 'Physics Spheres:Runtime']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:Octane2.1ES6', ['Crypto', 'DeltaBlue', 'EarleyBoyer', 'NavierStokes', 'RayTrace', 'RegExp', 'Richards', 'Splay', 'Total']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:Wasm', ['AngryBots-Async:CodeSize', 'AngryBots-Async:Compile', 'AngryBots-Async:RelocSize', 'AngryBots:CodeSize', 'AngryBots:Compile', 'AngryBots:RelocSize', 'AngryBots:Validate', 'Instantiate-Microbench:Instantiate', 'Sqlite-Async:CodeSize', 'Sqlite-Async:Compile', 'Sqlite-Async:RelocSize', 'Sqlite:CodeSize', 'Sqlite:Compile', 'Sqlite:RelocSize', 'Sqlite:Validate']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:JetStream-wasm', ['bigfib', 'container', 'dry', 'float-mm', 'gcc-loops', 'n-body', 'quicksort', 'towers']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:ARES-6-Future', ['Air averageWorstCase', 'Air firstIteration', 'Air steadyState', 'Babylon averageWorstCase', 'Babylon firstIteration', 'Babylon steadyState', 'Basic averageWorstCase', 'Basic firstIteration', 'Basic steadyState', 'ML averageWorstCase', 'ML firstIteration', 'ML steadyState', 'Total summary']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:Octane2.1', ['Box2D', 'CodeLoad', 'Crypto', 'DeltaBlue', 'EarleyBoyer', 'Gameboy', 'Mandreel', 'MandreelLatency', 'NavierStokes', 'PdfJS', 'RayTrace', 'RegExp', 'Richards', 'Splay', 'SplayLatency', 'Total', 'Typescript', 'zlib']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:SunSpiderGolem', ['3dCube', '3dMorph', '3dRaytrace', 'AccessBinaryTrees', 'AccessFannkuch', 'AccessNbody', 'AccessNsieve', 'Bitops3bitBitsInByte', 'BitopsBitsInByte', 'BitopsBitwiseAnd', 'BitopsNsieveBits', 'ControlflowRecursive', 'CryptoAes', 'CryptoMd5', 'CryptoSha1', 'DateFormatTofte', 'DateFormatXparb', 'MathCordic', 'MathPartialSums', 'MathSpectralNorm', 'RegexpDna', 'StringBase64', 'StringFasta', 'StringTagcloud', 'StringUnpackCode', 'StringValidateInput']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:Octane2.1-NoOpt', ['Ignition:Box2D', 'Ignition:CodeLoad', 'Ignition:Crypto', 'Ignition:DeltaBlue', 'Ignition:EarleyBoyer', 'Ignition:Gameboy', 'Ignition:Mandreel', 'Ignition:NavierStokes', 'Ignition:PdfJS', 'Ignition:RayTrace', 'Ignition:RegExp', 'Ignition:Richards', 'Ignition:Splay', 'Ignition:SplayLatency', 'Ignition:Total', 'Ignition:TotalBaselineCodeSize', 'Ignition:TotalBaselineCompileCount', 'Ignition:Typescript']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:BigNum', ['P256:BigNum.mod params.curve.q', 'P256:BigNum.mod params.n', 'P256:FastModulus.NIST.P_256.residue', 'P256:FastModulusFFFFFF.residue', 'P256:modMultiply with Montgomery', 'P256:modMultiply with residue', 'RSA:RSA encryption & decryption']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:ARES-6', ['Air averageWorstCase', 'Air firstIteration', 'Air steadyState', 'Babylon averageWorstCase', 'Babylon firstIteration', 'Babylon steadyState', 'Basic averageWorstCase', 'Basic firstIteration', 'Basic steadyState', 'ML averageWorstCase', 'ML firstIteration', 'ML steadyState', 'Total summary']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:Embenchen', ['Box2d', 'Bullet', 'Copy', 'Corrections', 'Fannkuch', 'Fasta', 'LuaBinaryTrees', 'MemOps', 'Primes', 'Skinning', 'ZLib']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:Compile', ['stalls']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:Promises', ['bluebird-doxbee', 'bluebird-parallel', 'wikipedia']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:PunchStartup', ['NewDocument']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:Unity', ['2D Physics Boxes:CodeSize', '2D Physics Boxes:Compile', '2D Physics Boxes:Instantiate', '2D Physics Boxes:Parse', '2D Physics Boxes:PreParse', '2D Physics Boxes:RelocSize', '2D Physics Boxes:Runtime', '2D Physics Boxes:Total', '2D Physics Spheres:CodeSize', '2D Physics Spheres:Compile', '2D Physics Spheres:Instantiate', '2D Physics Spheres:Parse', '2D Physics Spheres:PreParse', '2D Physics Spheres:RelocSize', '2D Physics Spheres:Runtime', '2D Physics Spheres:Total', 'Animation and Skinning:CodeSize', 'Animation and Skinning:Compile', 'Animation and Skinning:Instantiate', 'Animation and Skinning:Parse', 'Animation and Skinning:PreParse', 'Animation and Skinning:RelocSize', 'Animation and Skinning:Runtime', 'Animation and Skinning:Total', 'Asteroid Field:CodeSize', 'Asteroid Field:Compile', 'Asteroid Field:Instantiate', 'Asteroid Field:Parse', 'Asteroid Field:PreParse', 'Asteroid Field:RelocSize', 'Asteroid Field:Runtime', 'Asteroid Field:Total', 'Cryptohash:CodeSize', 'Cryptohash:Compile', 'Cryptohash:Instantiate', 'Cryptohash:Parse', 'Cryptohash:PreParse', 'Cryptohash:RelocSize', 'Cryptohash:Runtime', 'Cryptohash:Total', 'Instantiate and Destroy:CodeSize', 'Instantiate and Destroy:Compile', 'Instantiate and Destroy:Instantiate', 'Instantiate and Destroy:Parse', 'Instantiate and Destroy:PreParse', 'Instantiate and Destroy:RelocSize', 'Instantiate and Destroy:Runtime', 'Instantiate and Destroy:Total', 'Mandelbrot:CodeSize', 'Mandelbrot:Compile', 'Mandelbrot:Instantiate', 'Mandelbrot:Parse', 'Mandelbrot:PreParse', 'Mandelbrot:RelocSize', 'Mandelbrot:Runtime', 'Mandelbrot:Total', 'Physics Spheres:CodeSize', 'Physics Spheres:Compile', 'Physics Spheres:Instantiate', 'Physics Spheres:Parse', 'Physics Spheres:PreParse', 'Physics Spheres:RelocSize', 'Physics Spheres:Runtime', 'Physics Spheres:Total']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:Unity-Future', ['2D Physics Boxes:CodeSize', '2D Physics Boxes:Compile', '2D Physics Boxes:Instantiate', '2D Physics Boxes:Parse', '2D Physics Boxes:PreParse', '2D Physics Boxes:RelocSize', '2D Physics Boxes:Runtime', '2D Physics Boxes:Total', '2D Physics Spheres:CodeSize', '2D Physics Spheres:Compile', '2D Physics Spheres:Instantiate', '2D Physics Spheres:Parse', '2D Physics Spheres:PreParse', '2D Physics Spheres:RelocSize', '2D Physics Spheres:Runtime', '2D Physics Spheres:Total', 'Animation and Skinning:CodeSize', 'Animation and Skinning:Compile', 'Animation and Skinning:Instantiate', 'Animation and Skinning:Parse', 'Animation and Skinning:PreParse', 'Animation and Skinning:RelocSize', 'Animation and Skinning:Runtime', 'Animation and Skinning:Total', 'Asteroid Field:CodeSize', 'Asteroid Field:Compile', 'Asteroid Field:Instantiate', 'Asteroid Field:Parse', 'Asteroid Field:PreParse', 'Asteroid Field:RelocSize', 'Asteroid Field:Runtime', 'Asteroid Field:Total', 'Cryptohash:CodeSize', 'Cryptohash:Compile', 'Cryptohash:Instantiate', 'Cryptohash:Parse', 'Cryptohash:PreParse', 'Cryptohash:RelocSize', 'Cryptohash:Runtime', 'Cryptohash:Total', 'Instantiate and Destroy:CodeSize', 'Instantiate and Destroy:Compile', 'Instantiate and Destroy:Instantiate', 'Instantiate and Destroy:Parse', 'Instantiate and Destroy:PreParse', 'Instantiate and Destroy:RelocSize', 'Instantiate and Destroy:Runtime', 'Instantiate and Destroy:Total', 'Mandelbrot:CodeSize', 'Mandelbrot:Compile', 'Mandelbrot:Instantiate', 'Mandelbrot:Parse', 'Mandelbrot:PreParse', 'Mandelbrot:RelocSize', 'Mandelbrot:Runtime', 'Mandelbrot:Total', 'Physics Spheres:CodeSize', 'Physics Spheres:Compile', 'Physics Spheres:Instantiate', 'Physics Spheres:Parse', 'Physics Spheres:PreParse', 'Physics Spheres:RelocSize', 'Physics Spheres:Runtime', 'Physics Spheres:Total']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:RegExp', ['RegExp:Ctor', 'RegExp:Exec', 'RegExp:Flags', 'RegExp:Match', 'RegExp:Replace', 'RegExp:Search', 'RegExp:SlowExec', 'RegExp:SlowFlags', 'RegExp:SlowMatch', 'RegExp:SlowReplace', 'RegExp:SlowSearch', 'RegExp:SlowSplit', 'RegExp:SlowTest', 'RegExp:Split', 'RegExp:Test', 'RegExp:Total']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:LoadTime', ['1k_functions', 'angular', 'ember', 'jquery', 'react', 'swiffy', 'zepto']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:Massive', ['Box2D-F32:Box2D-F32', 'Box2D-F32:Box2D-F32_max', 'Box2D-F32:Box2D-F32_min', 'Box2D:Box2D', 'Box2D:Box2D_max', 'Box2D:Box2D_min', 'LuaBinaryTrees', 'LuaScimark:FFT', 'LuaScimark:LU', 'LuaScimark:MC', 'LuaScimark:SOR', 'LuaScimark:SPARSE', 'LuaScimark:SciMark', 'Poppler', 'SQLite']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:JSTests', ['Array:DoubleEvery', 'Array:DoubleFilter', 'Array:DoubleFind', 'Array:DoubleFindIndex', 'Array:DoubleMap', 'Array:DoubleReduce', 'Array:DoubleReduceRight', 'Array:DoubleSome', 'Array:FastEvery', 'Array:FastFilter', 'Array:FastFind', 'Array:FastFindIndex', 'Array:FastMap', 'Array:FastReduce', 'Array:FastReduceRight', 'Array:FastSome', 'Array:GenericFilter', 'Array:GenericFind', 'Array:GenericFindIndex', 'Array:GenericMap', 'Array:NaiveFilterReplacement', 'Array:NaiveFindIndexReplacement', 'Array:NaiveFindReplacement', 'Array:NaiveMapReplacement', 'Array:OptFastEvery', 'Array:OptFastFilter', 'Array:OptFastFind', 'Array:OptFastFindIndex', 'Array:OptFastMap', 'Array:OptFastReduce', 'Array:OptFastReduceRight', 'Array:OptFastSome', 'Array:SmiEvery', 'Array:SmiFilter', 'Array:SmiFind', 'Array:SmiFindIndex', 'Array:SmiJoin', 'Array:SmiMap', 'Array:SmiReduce', 'Array:SmiReduceRight', 'Array:SmiSome', 'Array:SmiToString', 'Array:SparseSmiJoin', 'Array:SparseSmiToString', 'Array:SparseStringJoin', 'Array:SparseStringToString', 'Array:StringJoin', 'Array:StringToString', 'Array:Total', 'AsyncAwait:BaselineES2017', 'AsyncAwait:BaselineNaivePromises', 'AsyncAwait:Native', 'AsyncAwait:Total', 'BytecodeHandlers:Arithmetic', 'BytecodeHandlers:Bitwise', 'BytecodeHandlers:Compare', 'BytecodeHandlers:StringConcat', 'Classes:DefaultConstructor', 'Classes:LeafConstructors', 'Classes:Super', 'Classes:Total', 'Closures:Closures', 'Closures:Total', 'ClosuresMarkForTierUp:Closures', 'ClosuresMarkForTierUp:Total', 'Collections:Map-Double', 'Collections:Map-Iteration', 'Collections:Map-Iterator', 'Collections:Map-Object', 'Collections:Map-Object-Set-Get-Large', 'Collections:Map-Smi', 'Collections:Map-String', 'Collections:Set-Double', 'Collections:Set-Iteration', 'Collections:Set-Iterator', 'Collections:Set-Object', 'Collections:Set-Smi', 'Collections:Set-String', 'Collections:Total', 'Collections:WeakMap', 'Collections:WeakMap-Constructor', 'Collections:WeakSet', 'Collections:WeakSet-Constructor', 'Exceptions:Total', 'Exceptions:Try-Catch', 'ExpressionDepth:Add', 'ExpressionDepth:And-Test', 'ExpressionDepth:And-Value', 'ExpressionDepth:BitwiseOr', 'ExpressionDepth:Comma-Test', 'ExpressionDepth:Comma-Value', 'ExpressionDepth:Equals-Test', 'ExpressionDepth:Equals-Value', 'ExpressionDepth:GreaterThan-Test', 'ExpressionDepth:GreaterThan-Value', 'ExpressionDepth:Or-Test', 'ExpressionDepth:Or-Value', 'ExpressionDepth:StrictEquals-Test', 'ExpressionDepth:StrictEquals-Value', 'ExpressionDepth:StringConcat', 'ExpressionDepth:Sub', 'ExpressionDepth:Total', 'ForLoops:Let-Standard', 'ForLoops:Total', 'ForLoops:Var-Standard', 'Generators', 'Inspector:AsyncStacksInstrumentation', 'Inspector:Debugger.getPossibleBreakpoints', 'Inspector:Debugger.paused', 'Inspector:Runtime.evaluate(String16Cstor)', 'Inspector:Total', 'Iterators:ForOf', 'Iterators:Total', 'Keys:Object.keys()', 'Keys:Object.keys().forEach()', 'Keys:Total',
    'Keys:for (i < Object.keys().length)', 'Keys:for (i < array.length)', 'Keys:for (i < length)', 'Keys:for-in', 'Keys:for-in hasOwnProperty()', 'ManyClosures:ManyClosures', 'ManyClosures:Total', 'Modules:BasicExport', 'Modules:BasicImport', 'Modules:BasicNamespace', 'Modules:Total', 'Object:Assign', 'Object:Create', 'Object:Entries', 'Object:EntriesMegamorphic', 'Object:Total', 'Object:Values', 'Object:ValuesMegamorphic', 'Parsing:MultiLineComment', 'Parsing:OneLineComment', 'Parsing:OneLineComments', 'Parsing:Total', 'PropertyQueries:Object.hasOwnProperty--DEINTERN-prop', 'PropertyQueries:Object.hasOwnProperty--INTERN-prop', 'PropertyQueries:Object.hasOwnProperty--NE-DEINTERN-prop', 'PropertyQueries:Object.hasOwnProperty--NE-INTERN-prop', 'PropertyQueries:Object.hasOwnProperty--NE-el', 'PropertyQueries:Object.hasOwnProperty--el', 'PropertyQueries:Object.hasOwnProperty--el-str', 'PropertyQueries:Total', 'PropertyQueries:in--DEINTERN-prop', 'PropertyQueries:in--INTERN-prop', 'PropertyQueries:in--NE-DEINTERN-prop', 'PropertyQueries:in--NE-INTERN-prop', 'PropertyQueries:in--NE-el', 'PropertyQueries:in--el', 'PropertyQueries:in--el-str', 'Proxies:GetIndexWithTrap', 'Proxies:GetIndexWithoutTrap', 'Proxies:GetStringWithTrap', 'Proxies:GetStringWithoutTrap', 'Proxies:GetSymbolWithTrap', 'Proxies:GetSymbolWithoutTrap', 'Proxies:HasInIdiom', 'Proxies:HasStringWithTrap', 'Proxies:HasStringWithoutTrap', 'Proxies:HasSymbolWithTrap', 'Proxies:HasSymbolWithoutTrap', 'Proxies:SetIndexWithTrap', 'Proxies:SetIndexWithoutTrap', 'Proxies:SetStringWithTrap', 'Proxies:SetStringWithoutTrap', 'Proxies:SetSymbolWithTrap', 'Proxies:SetSymbolWithoutTrap', 'Proxies:Total', 'RestParameters:Basic1', 'RestParameters:ReturnArgsBabel', 'RestParameters:ReturnArgsNative', 'RestParameters:Total', 'Scope:Total', 'Scope:With', 'SpreadCalls:Call', 'SpreadCalls:CallMethod', 'SpreadCalls:CallNew', 'SpreadCalls:Total', 'StringIterators:ForOf_OneByteLong', 'StringIterators:ForOf_OneByteShort', 'StringIterators:ForOf_TwoByteLong', 'StringIterators:ForOf_TwoByteShort', 'StringIterators:ForOf_WithSurrogatePairsLong', 'StringIterators:ForOf_WithSurrogatePairsShort', 'StringIterators:Spread_OneByteShort', 'StringIterators:Spread_TwoByteShort', 'StringIterators:Spread_WithSurrogatePairsShort', 'StringIterators:Total', 'Strings:StringCharCodeAtConstant', 'Strings:StringCharCodeAtNonConstant', 'Strings:StringFunctions', 'Strings:StringIndexOfConstant', 'Strings:StringIndexOfNonConstant', 'Strings:Total', 'Templates:LargeUntagged', 'Templates:Tagged', 'Templates:Total', 'Templates:Untagged', 'TypedArrays:ConstructAllTypedArrays', 'TypedArrays:ConstructArrayLike', 'TypedArrays:ConstructBySameTypedArray', 'TypedArrays:ConstructByTypedArray', 'TypedArrays:ConstructWithBuffer', 'TypedArrays:Constructor', 'TypedArrays:CopyWithin', 'TypedArrays:SetFromArrayLike', 'TypedArrays:SetFromDifferentType', 'TypedArrays:SetFromSameType', 'TypedArrays:SliceNoSpecies', 'TypedArrays:Sort',
    'TypedArrays:SubarrayNoSpecies']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:Octane2.1-Harmony', ['Box2D', 'CodeLoad', 'Crypto', 'DeltaBlue', 'EarleyBoyer', 'Gameboy', 'Mandreel', 'MandreelLatency', 'NavierStokes', 'PdfJS', 'RayTrace', 'RegExp', 'Richards', 'Splay', 'SplayLatency', 'Total', 'Typescript', 'zlib']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:Wasm-Future', ['AngryBots-Async:CodeSize', 'AngryBots-Async:Compile', 'AngryBots-Async:RelocSize', 'AngryBots:CodeSize', 'AngryBots:Compile', 'AngryBots:RelocSize', 'AngryBots:Validate', 'Sqlite-Async:CodeSize', 'Sqlite-Async:Compile', 'Sqlite-Async:RelocSize', 'Sqlite:CodeSize', 'Sqlite:Compile', 'Sqlite:RelocSize', 'Sqlite:Validate']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:JetStream', ['3d-cube', '3d-raytrace', 'Total', 'base64', 'bigfib.cpp', 'box2d', 'code-first-load', 'code-multi-load', 'container.cpp', 'cordic', 'crypto', 'crypto-aes', 'crypto-md5', 'crypto-sha1', 'date-format-tofte', 'date-format-xparb', 'delta-blue', 'dry.c', 'earley-boyer', 'float-mm.c', 'gbemu', 'gcc-loops.cpp', 'hash-map', 'mandreel', 'mandreel-latency', 'n-body', 'n-body.c', 'navier-stokes', 'pdfjs', 'proto-raytracer', 'quicksort.c', 'regex-dna', 'regexp-2010', 'richards', 'splay', 'splay-latency', 'tagcloud', 'towers.c', 'typescript', 'zlib']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:Emscripten', ['Box2d', 'Bullet', 'Copy', 'Corrections', 'Fannkuch', 'Fasta', 'Life', 'LuaBinaryTrees', 'MemOps', 'NBodyJava', 'Primes', 'Skinning', 'ZLib']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:Spec2k', ['164.gzip:CodeSize', '164.gzip:MinMaxSpread', '164.gzip:RelocSize', '164.gzip:Run', '177.mesa:CodeSize', '177.mesa:MinMaxSpread', '177.mesa:RelocSize', '177.mesa:Run', '179.art:CodeSize', '179.art:MinMaxSpread', '179.art:RelocSize', '179.art:Run', '181.mcf:CodeSize', '181.mcf:MinMaxSpread', '181.mcf:RelocSize', '181.mcf:Run', '256.bzip2:CodeSize', '256.bzip2:MinMaxSpread', '256.bzip2:RelocSize', '256.bzip2:Run']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:AreWeFastYet', ['Box2dLoadTime', 'Box2dThroughput', 'BulletLoadTime', 'BulletThroughput', 'Copy', 'Corrections', 'Fannkuch', 'Fasta', 'Life', 'LuaBinaryTreesLoadTime', 'LuaBinaryTreesThroughput', 'MemOps', 'Primes', 'Skinning', 'ZlibLoadTime', 'ZlibThroughput']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:Unity-asm-wasm', ['2D Physics Boxes:AsmWasm', '2D Physics Boxes:AsmWasmPeak', '2D Physics Boxes:CodeSize', '2D Physics Boxes:Compile', '2D Physics Boxes:Instantiate', '2D Physics Boxes:LazyCompile', '2D Physics Boxes:Parse', '2D Physics Boxes:PreParse', '2D Physics Boxes:RelocSize', '2D Physics Boxes:Runtime', '2D Physics Boxes:Total', '2D Physics Spheres:AsmWasm', '2D Physics Spheres:AsmWasmPeak', '2D Physics Spheres:CodeSize', '2D Physics Spheres:Compile', '2D Physics Spheres:Instantiate', '2D Physics Spheres:LazyCompile', '2D Physics Spheres:Parse', '2D Physics Spheres:PreParse', '2D Physics Spheres:RelocSize', '2D Physics Spheres:Runtime', '2D Physics Spheres:Total', 'Animation and Skinning:AsmWasm', 'Animation and Skinning:AsmWasmPeak', 'Animation and Skinning:CodeSize', 'Animation and Skinning:Compile', 'Animation and Skinning:Instantiate', 'Animation and Skinning:LazyCompile', 'Animation and Skinning:Parse', 'Animation and Skinning:PreParse', 'Animation and Skinning:RelocSize', 'Animation and Skinning:Runtime', 'Animation and Skinning:Total', 'Asteroid Field:AsmWasm', 'Asteroid Field:AsmWasmPeak', 'Asteroid Field:CodeSize', 'Asteroid Field:Compile', 'Asteroid Field:Instantiate', 'Asteroid Field:LazyCompile', 'Asteroid Field:Parse', 'Asteroid Field:PreParse', 'Asteroid Field:RelocSize', 'Asteroid Field:Runtime', 'Asteroid Field:Total', 'Cryptohash:AsmWasm', 'Cryptohash:AsmWasmPeak', 'Cryptohash:CodeSize', 'Cryptohash:Compile', 'Cryptohash:Instantiate', 'Cryptohash:LazyCompile', 'Cryptohash:Parse', 'Cryptohash:PreParse', 'Cryptohash:RelocSize', 'Cryptohash:Runtime', 'Cryptohash:Total', 'Instantiate and Destroy:AsmWasm', 'Instantiate and Destroy:AsmWasmPeak', 'Instantiate and Destroy:CodeSize', 'Instantiate and Destroy:Compile', 'Instantiate and Destroy:Instantiate', 'Instantiate and Destroy:LazyCompile', 'Instantiate and Destroy:Parse', 'Instantiate and Destroy:PreParse', 'Instantiate and Destroy:RelocSize', 'Instantiate and Destroy:Runtime', 'Instantiate and Destroy:Total', 'Mandelbrot:AsmWasm', 'Mandelbrot:AsmWasmPeak', 'Mandelbrot:CodeSize', 'Mandelbrot:Compile', 'Mandelbrot:Instantiate', 'Mandelbrot:LazyCompile', 'Mandelbrot:Parse', 'Mandelbrot:PreParse', 'Mandelbrot:RelocSize', 'Mandelbrot:Runtime', 'Mandelbrot:Total', 'Physics Spheres:AsmWasm', 'Physics Spheres:AsmWasmPeak', 'Physics Spheres:CodeSize', 'Physics Spheres:Compile', 'Physics Spheres:Instantiate', 'Physics Spheres:LazyCompile', 'Physics Spheres:Parse', 'Physics Spheres:PreParse', 'Physics Spheres:RelocSize', 'Physics Spheres:Runtime', 'Physics Spheres:Total']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:Octane2.1-Future', ['Box2D', 'CodeLoad', 'Crypto', 'DeltaBlue', 'EarleyBoyer', 'Gameboy', 'Mandreel', 'MandreelLatency', 'NavierStokes', 'PdfJS', 'RayTrace', 'RegExp', 'Richards', 'Splay', 'SplayLatency', 'Total', 'Typescript', 'zlib']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:Liftoff-Micro', ['add-big-i32-10-Liftoff:CodeSize', 'add-big-i32-10-Liftoff:CompileTime', 'add-big-i32-10-Liftoff:Execution', 'add-big-i32-10-Turbofan:CodeSize', 'add-big-i32-10-Turbofan:CompileTime', 'add-big-i32-10-Turbofan:Execution', 'add-big-i32-100-Liftoff:CodeSize', 'add-big-i32-100-Liftoff:CompileTime', 'add-big-i32-100-Liftoff:Execution', 'add-big-i32-100-Turbofan:CodeSize', 'add-big-i32-100-Turbofan:CompileTime', 'add-big-i32-100-Turbofan:Execution', 'add-big-i32-1000-Liftoff:CodeSize', 'add-big-i32-1000-Liftoff:CompileTime', 'add-big-i32-1000-Liftoff:Execution', 'add-big-i32-1000-Turbofan:CodeSize', 'add-big-i32-1000-Turbofan:CompileTime', 'add-big-i32-1000-Turbofan:Execution', 'add-small-i32-10-Liftoff:CodeSize', 'add-small-i32-10-Liftoff:CompileTime', 'add-small-i32-10-Liftoff:Execution', 'add-small-i32-10-Turbofan:CodeSize', 'add-small-i32-10-Turbofan:CompileTime', 'add-small-i32-10-Turbofan:Execution', 'add-small-i32-100-Liftoff:CodeSize', 'add-small-i32-100-Liftoff:CompileTime', 'add-small-i32-100-Liftoff:Execution', 'add-small-i32-100-Turbofan:CodeSize', 'add-small-i32-100-Turbofan:CompileTime', 'add-small-i32-100-Turbofan:Execution', 'add-small-i32-1000-Liftoff:CodeSize', 'add-small-i32-1000-Liftoff:CompileTime', 'add-small-i32-1000-Liftoff:Execution', 'add-small-i32-1000-Turbofan:CodeSize', 'add-small-i32-1000-Turbofan:CompileTime', 'add-small-i32-1000-Turbofan:Execution', 'fib-32-10-Liftoff:CodeSize', 'fib-32-10-Liftoff:CompileTime', 'fib-32-10-Liftoff:Execution', 'fib-32-10-Turbofan:CodeSize', 'fib-32-10-Turbofan:CompileTime', 'fib-32-10-Turbofan:Execution', 'fib-32-100-Liftoff:CodeSize', 'fib-32-100-Liftoff:CompileTime', 'fib-32-100-Liftoff:Execution', 'fib-32-100-Turbofan:CodeSize', 'fib-32-100-Turbofan:CompileTime', 'fib-32-100-Turbofan:Execution', 'fib-32-1000-Liftoff:CodeSize', 'fib-32-1000-Liftoff:CompileTime', 'fib-32-1000-Liftoff:Execution', 'fib-32-1000-Turbofan:CodeSize', 'fib-32-1000-Turbofan:CompileTime', 'fib-32-1000-Turbofan:Execution', 'return-i32-const-Liftoff:CodeSize', 'return-i32-const-Liftoff:CompileTime', 'return-i32-const-Liftoff:Execution', 'return-i32-const-Turbofan:CodeSize', 'return-i32-const-Turbofan:CompileTime', 'return-i32-const-Turbofan:Execution']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:SunSpider', ['3d-cube', '3d-morph', '3d-raytrace', 'Total', 'access-binary-trees', 'access-fannkuch', 'access-nbody', 'access-nsieve', 'bitops-3bit-bits-in-byte', 'bitops-bits-in-byte', 'bitops-bitwise-and', 'bitops-nsieve-bits', 'controlflow-recursive', 'crypto-aes', 'crypto-md5', 'crypto-sha1', 'date-format-tofte', 'date-format-xparb', 'math-cordic', 'math-partial-sums', 'math-spectral-norm', 'regexp-dna', 'string-base64', 'string-fasta', 'string-tagcloud', 'string-unpack-code', 'string-validate-input']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:SixSpeed', ['Array pattern destructuring:ES5', 'Array pattern destructuring:ES6', 'Classes:Babel', 'Classes:ES5', 'Classes:ES6', 'Computed property names in object literals:ES5', 'Computed property names in object literals:ES6', 'Defaults:ES5', 'Defaults:ES6', 'Map get string:ES5', 'Map get string:ES6', 'Map-Set add-set-has object:ES5', 'Map-Set add-set-has object:ES6', 'Map-Set add-set-has:ES5', 'Map-Set add-set-has:ES6', 'Map-Set has:ES5', 'Map-Set has:ES6', 'Spread:Babel', 'Spread:ES5', 'Spread:ES6', 'SpreadLiteral:Babel', 'SpreadLiteral:ES5', 'SpreadLiteral:ES6', 'Super:Babel', 'Super:ES5', 'Super:ES6', 'SuperSpread:Babel', 'SuperSpread:ES5', 'SuperSpread:ES6']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:JSBench', ['JSBenchAmazon', 'JSBenchFacebook', 'JSBenchGoogle']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:Micro', ['asm_loop', 'constant', 'get_object']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:web-tooling-benchmark', ['Geometric mean', 'acorn', 'babel', 'babylon', 'buble', 'chai', 'coffeescript', 'espree', 'esprima', 'jshint', 'lebab', 'prepack', 'prettier', 'source-map', 'typescript', 'uglify-es', 'uglify-js']);
  MEASUREMENTS_BY_TEST_SUITE.set('v8:TraceurES6', ['Traceur']);

  const RUNTIMESTATS_MEASUREMENT_BASES = ['API_ArrayBuffer_Neuter', 'API_ArrayBuffer_New', 'API_Array_New', 'API_Context_New', 'API_Error_New', 'API_External_New', 'API_Float32Array_New', 'API_FunctionTemplate_GetFunction', 'API_FunctionTemplate_New', 'API_FunctionTemplate_NewWithCache', 'API_Function_Call', 'API_Function_New', 'API_Function_NewInstance', 'API_Int32Array_New', 'API_ObjectTemplate_New', 'API_Object_CreateDataProperty', 'API_Object_DefineOwnProperty', 'API_Object_Delete', 'API_Object_Get', 'API_Object_GetPropertyAttributes', 'API_Object_GetPropertyNames', 'API_Object_Has', 'API_Object_HasOwnProperty', 'API_Object_New', 'API_Object_Set', 'API_Object_SetAccessor', 'API_Object_SetIntegrityLevel', 'API_Object_SetPrivate', 'API_Object_SetPrototype', 'API_Object_ToNumber', 'API_Object_ToString', 'API_Persistent_New', 'API_Private_New', 'API_Promise_Resolver_New', 'API_Promise_Resolver_Reject', 'API_Promise_Resolver_Resolve', 'API_ScriptCompiler_Compile', 'API_ScriptCompiler_CompileFunctionInContext', 'API_ScriptCompiler_CompileUnbound', 'API_Script_Run', 'API_String_Concat', 'API_String_NewExternalOneByte', 'API_String_NewExternalTwoByte', 'API_String_NewFromOneByte', 'API_String_NewFromTwoByte', 'API_String_NewFromUtf8', 'API_String_Write', 'API_String_WriteUtf8', 'API_ValueDeserializer_ReadHeader', 'API_ValueDeserializer_ReadValue', 'API_ValueSerializer_WriteValue', 'AccessorGetterCallback', 'AddDictionaryProperty', 'AllocateInNewSpace', 'AllocateInTargetSpace', 'ArrayBufferConstructor_ConstructStub', 'ArrayBufferConstructor_DoNotInitialize', 'ArrayBufferPrototypeGetByteLength', 'ArrayBufferPrototypeSlice', 'ArrayBufferViewGetByteLength', 'ArrayBufferViewGetByteOffset', 'ArrayBufferViewWasNeutered', 'ArrayConcat', 'ArrayIndexOf', 'ArrayLengthGetter', 'ArrayLengthSetter', 'ArrayPop', 'ArrayPush', 'ArrayShift', 'ArraySpeciesConstructor', 'ArraySplice', 'ArrayUnshift', 'AvailableLocalesOf', 'BooleanConstructor', 'BooleanConstructor_ConstructStub', 'BoundFunctionLengthGetter', 'BoundFunctionNameGetter', 'CanonicalizeLanguageTag', 'CompileAnalyse', 'CompileBackgroundAnalyse', 'CompileBackgroundIgnition', 'CompileBackgroundRenumber', 'CompileBackgroundRewriteReturnResult', 'CompileBackgroundScopeAnalysis', 'CompileBackgroundScript', 'CompileDeserialize', 'CompileEval', 'CompileForOnStackReplacement', 'CompileFunction', 'CompileGetFromOptimizedCodeMap', 'CompileIgnition', 'CompileIgnitionFinalization', 'CompileLazy', 'CompileOptimized_NotConcurrent', 'CompileRenumber', 'CompileRewriteReturnResult', 'CompileScopeAnalysis', 'CompileScript', 'CompileSerialize', 'CompleteInobjectSlackTrackingForMap', 'ConsoleAssert', 'ConsoleDebug', 'ConsoleError', 'ConsoleInfo', 'ConsoleLog', 'ConsoleTime', 'ConsoleTimeStamp', 'ConsoleWarn', 'CreateArrayLiteral', 'CreateDataProperty', 'CreateListFromArrayLike', 'CreateNumberFormat', 'CreateObjectLiteral', 'CreateRegExpLiteral', 'DataViewConstructor_ConstructStub', 'DataViewPrototypeGetBuffer', 'DataViewPrototypeGetByteLength', 'DataViewPrototypeGetByteOffset', 'DataViewPrototypeGetFloat32', 'DataViewPrototypeGetUint32', 'DataViewPrototypeGetUint8', 'DateConstructor_ConstructStub', 'DateCurrentTime', 'DateNow', 'DateParse', 'DatePrototypeGetYear', 'DatePrototypeSetDate', 'DatePrototypeSetFullYear', 'DatePrototypeSetHours', 'DatePrototypeSetMilliseconds', 'DatePrototypeSetMinutes', 'DatePrototypeSetMonth', 'DatePrototypeSetSeconds', 'DatePrototypeSetTime', 'DatePrototypeSetUTCDate', 'DatePrototypeSetYear', 'DatePrototypeToDateString', 'DatePrototypeToISOString', 'DatePrototypeToJson', 'DatePrototypeToString', 'DatePrototypeToUTCString', 'DateUTC', 'DeclareEvalFunction', 'DeclareEvalVar', 'DeclareGlobalsForInterpreter', 'DefineAccessorPropertyUnchecked', 'DefineDataPropertyInLiteral', 'DeleteLookupSlot', 'DeleteProperty', 'DeoptimizeCode', 'DeserializeLazy', 'ElementsTransitionAndStoreIC_Miss', 'EnqueuePromiseReactionJob', 'EnqueuePromiseResolveThenableJob', 'ErrorCaptureStackTrace', 'ErrorConstructor', 'ErrorPrototypeToString', 'EstimateNumberOfElements', 'EvictOptimizedCodeSlot', 'ForInEnumerate', 'ForInHasProperty', 'FunctionCallback', 'FunctionConstructor', 'FunctionLengthGetter', 'FunctionPrototypeGetter', 'FunctionPrototypeSetter', 'FunctionPrototypeToString', 'GCEpilogueCallback', 'GCPrologueCallback', 'GC_BACKGROUND_ARRAY_BUFFER_FREE', 'GC_BACKGROUND_STORE_BUFFER', 'GC_BACKGROUND_UNMAPPER', 'GC_Custom_IncrementalMarkingObserver', 'GC_Custom_SlowAllocateRaw', 'GC_HEAP_EPILOGUE', 'GC_HEAP_EPILOGUE_REDUCE_NEW_SPACE', 'GC_HEAP_EXTERNAL_EPILOGUE', 'GC_HEAP_EXTERNAL_PROLOGUE', 'GC_HEAP_EXTERNAL_WEAK_GLOBAL_HANDLES', 'GC_HEAP_PROLOGUE', 'GC_MC_BACKGROUND_EVACUATE_COPY', 'GC_MC_BACKGROUND_EVACUATE_UPDATE_POINTERS', 'GC_MC_BACKGROUND_MARKING', 'GC_MC_BACKGROUND_SWEEPING', 'GC_MC_CLEAR', 'GC_MC_CLEAR_DEPENDENT_CODE', 'GC_MC_CLEAR_MAPS', 'GC_MC_CLEAR_STRING_TABLE', 'GC_MC_CLEAR_WEAK_CELLS', 'GC_MC_CLEAR_WEAK_COLLECTIONS', 'GC_MC_CLEAR_WEAK_LISTS', 'GC_MC_EPILOGUE', 'GC_MC_EVACUATE', 'GC_MC_EVACUATE_CLEAN_UP', 'GC_MC_EVACUATE_COPY', 'GC_MC_EVACUATE_EPILOGUE', 'GC_MC_EVACUATE_PROLOGUE', 'GC_MC_EVACUATE_REBALANCE', 'GC_MC_EVACUATE_UPDATE_POINTERS', 'GC_MC_EVACUATE_UPDATE_POINTERS_SLOTS_MAIN', 'GC_MC_EVACUATE_UPDATE_POINTERS_SLOTS_MAP_SPACE', 'GC_MC_EVACUATE_UPDATE_POINTERS_TO_NEW_ROOTS', 'GC_MC_EVACUATE_UPDATE_POINTERS_WEAK', 'GC_MC_FINISH', 'GC_MC_INCREMENTAL', 'GC_MC_INCREMENTAL_EXTERNAL_EPILOGUE', 'GC_MC_INCREMENTAL_EXTERNAL_PROLOGUE', 'GC_MC_INCREMENTAL_FINALIZE', 'GC_MC_INCREMENTAL_FINALIZE_BODY', 'GC_MC_INCREMENTAL_START', 'GC_MC_INCREMENTAL_SWEEPING', 'GC_MC_INCREMENTAL_WRAPPER_PROLOGUE', 'GC_MC_INCREMENTAL_WRAPPER_TRACING', 'GC_MC_MARK', 'GC_MC_MARK_FINISH_INCREMENTAL', 'GC_MC_MARK_MAIN', 'GC_MC_MARK_ROOTS', 'GC_MC_MARK_WEAK_CLOSURE', 'GC_MC_MARK_WEAK_CLOSURE_EPHEMERAL', 'GC_MC_MARK_WEAK_CLOSURE_HARMONY', 'GC_MC_MARK_WEAK_CLOSURE_WEAK_HANDLES', 'GC_MC_MARK_WEAK_CLOSURE_WEAK_ROOTS', 'GC_MC_MARK_WRAPPER_EPILOGUE', 'GC_MC_MARK_WRAPPER_PROLOGUE', 'GC_MC_MARK_WRAPPER_TRACING', 'GC_MC_PROLOGUE', 'GC_MC_SWEEP', 'GC_MC_SWEEP_CODE', 'GC_MC_SWEEP_MAP', 'GC_MC_SWEEP_OLD', 'GC_SCAVENGER_BACKGROUND_SCAVENGE_PARALLEL', 'GC_SCAVENGER_PROCESS_ARRAY_BUFFERS', 'GC_SCAVENGER_SCAVENGE', 'GC_SCAVENGER_SCAVENGE_PARALLEL', 'GC_SCAVENGER_SCAVENGE_ROOTS', 'GC_SCAVENGER_SCAVENGE_WEAK', 'GC_SCAVENGER_SCAVENGE_WEAK_GLOBAL_HANDLES_IDENTIFY', 'GC_SCAVENGER_SCAVENGE_WEAK_GLOBAL_HANDLES_PROCESS', 'GenerateRandomNumbers', 'GetDefaultICULocale', 'GetMoreDataCallback', 'GetProperty', 'GlobalDecodeURI', 'GlobalDecodeURIComponent', 'GlobalEncodeURI', 'GlobalEncodeURIComponent', 'GlobalEscape', 'GlobalEval', 'GlobalUnescape', 'Group-API', 'Group-Callback', 'Group-Compile', 'Group-Compile-Total', 'Group-CompileBackground', 'Group-GC', 'Group-GC-Background', 'Group-GC-Custom', 'Group-IC', 'Group-JavaScript', 'Group-Optimize', 'Group-Parse', 'Group-Parse-Total', 'Group-ParseBackground', 'Group-Runtime', 'Group-Total-V8', 'HandleApiCall', 'HasComplexElements', 'HasFastPackedElements', 'HasInPrototypeChain', 'HasProperty', 'IndexedDescriptorCallback', 'IndexedEnumeratorCallback', 'InternalNumberFormat', 'InterpreterDeserializeLazy', 'InterpreterNewClosure', 'Interrupt', 'IsConstructor', 'IsInitializedIntlObjectOfType', 'IterableToListCanBeElided', 'JS_Execution', 'JsonParse', 'JsonStringify', 'KeyedGetProperty', 'KeyedLoadIC_KeyedLoadSloppyArgumentsStub', 'KeyedLoadIC_LoadElementDH', 'KeyedLoadIC_LoadIndexedInterceptorStub', 'KeyedLoadIC_LoadIndexedStringDH', 'KeyedLoadIC_Miss', 'KeyedStoreIC_ElementsTransitionAndStoreStub', 'KeyedStoreIC_Miss', 'KeyedStoreIC_Slow', 'KeyedStoreIC_StoreElementStub', 'KeyedStoreIC_StoreFastElementStub', 'LoadElementWithInterceptor', 'LoadGlobalIC_LoadScriptContextField', 'LoadGlobalIC_Miss', 'LoadGlobalIC_Slow', 'LoadIC_FunctionPrototypeStub', 'LoadIC_LoadAccessorDH', 'LoadIC_LoadAccessorFromPrototypeDH', 'LoadIC_LoadApiGetterFromPrototypeDH', 'LoadIC_LoadConstantDH', 'LoadIC_LoadConstantFromPrototypeDH', 'LoadIC_LoadFieldDH', 'LoadIC_LoadFieldFromPrototypeDH', 'LoadIC_LoadGlobalDH', 'LoadIC_LoadInterceptorDH', 'LoadIC_LoadNativeDataPropertyDH', 'LoadIC_LoadNativeDataPropertyFromPrototypeDH', 'LoadIC_LoadNonMaskingInterceptorDH', 'LoadIC_LoadNonexistentDH', 'LoadIC_LoadNormalDH', 'LoadIC_LoadNormalFromPrototypeDH', 'LoadIC_Miss', 'LoadIC_NonReceiver', 'LoadIC_Premonomorphic', 'LoadIC_SlowStub', 'LoadIC_StringLength', 'LoadLookupSlot', 'LoadLookupSlotForCall', 'LoadLookupSlotInsideTypeof', 'LoadPropertyWithInterceptor', 'MapGrow', 'MapShrink', 'Map_SetPrototype', 'Map_TransitionToAccessorProperty', 'Map_TransitionToDataProperty', 'MarkAsInitializedIntlObjectOfType', 'NamedEnumeratorCallback', 'NamedGetterCallback', 'NamedQueryCallback', 'NamedSetterCallback', 'NewArray', 'NewObject', 'NewSloppyArguments_Generic', 'NotifyDeoptimized', 'NumberPrototypeToFixed', 'NumberPrototypeToPrecision', 'NumberPrototypeToString', 'NumberToString', 'ObjectAssign', 'ObjectCreate', 'ObjectDefineProperties', 'ObjectDefineProperty', 'ObjectEntries', 'ObjectEntriesSkipFastPath', 'ObjectFreeze', 'ObjectGetOwnPropertyNames', 'ObjectGetOwnPropertySymbols', 'ObjectGetPrototypeOf', 'ObjectHasOwnProperty', 'ObjectIsExtensible', 'ObjectIsFrozen', 'ObjectIsSealed', 'ObjectKeys', 'ObjectLookupGetter', 'ObjectLookupSetter', 'ObjectPreventExtensions', 'ObjectPrototypeGetProto', 'ObjectPrototypePropertyIsEnumerable', 'ObjectPrototypeSetProto', 'ObjectSeal', 'ObjectSetPrototypeOf', 'ObjectValues', 'Object_DeleteProperty', 'OptimizeCode', 'OrdinaryHasInstance', 'ParseArrowFunctionLiteral', 'ParseBackgroundFunctionLiteral', 'ParseBackgroundProgram', 'ParseEval', 'ParseFunction', 'ParseFunctionLiteral', 'ParseProgram', 'PreParseBackgroundNoVariableResolution', 'PreParseBackgroundWithVariableResolution', 'PreParseNoVariableResolution', 'PreParseWithVariableResolution', 'PromiseRevokeReject', 'PrototypeMap_TransitionToAccessorProperty', 'PrototypeMap_TransitionToDataProperty', 'PrototypeObject_DeleteProperty', 'PushBlockContext', 'PushCatchContext', 'PushWithContext', 'ReThrow', 'RecompileSynchronous', 'ReconfigureToDataProperty', 'ReflectDefineProperty', 'RegExpCapture1Getter', 'RegExpCapture2Getter', 'RegExpCapture3Getter', 'RegExpCapture4Getter', 'RegExpCapture5Getter', 'RegExpCapture6Getter', 'RegExpCapture7Getter', 'RegExpCapture8Getter', 'RegExpCapture9Getter', 'RegExpExec', 'RegExpExecMultiple', 'RegExpInitializeAndCompile', 'RegExpInputGetter', 'RegExpInternalReplace', 'RegExpLastMatchGetter', 'RegExpPrototypeToString', 'RegExpReplace', 'RegExpSplit', 'RemoveArrayHoles', 'ReportPromiseReject', 'ResolvePossiblyDirectEval', 'SetNativeFlag', 'SetProperty', 'ShrinkPropertyDictionary', 'StackGuard', 'StoreCallbackProperty', 'StoreGlobalIC_Miss', 'StoreGlobalIC_Slow', 'StoreIC_Miss', 'StoreIC_NonReceiver', 'StoreIC_Premonomorphic', 'StoreIC_SlowStub', 'StoreIC_StoreAccessorOnPrototypeDH', 'StoreIC_StoreApiSetterOnPrototypeDH', 'StoreIC_StoreFieldDH', 'StoreIC_StoreGlobalDH', 'StoreIC_StoreInterceptorStub', 'StoreIC_StoreNativeDataPropertyDH', 'StoreIC_StoreNormalDH', 'StoreIC_StoreTransitionDH', 'StoreLookupSlot_Sloppy', 'StringAdd', 'StringBuilderConcat', 'StringBuilderJoin', 'StringCharCodeAt', 'StringEqual', 'StringGreaterThan', 'StringGreaterThanOrEqual', 'StringIncludes', 'StringIndexOf', 'StringIndexOfUnchecked', 'StringLengthGetter', 'StringLessThan', 'StringLessThanOrEqual', 'StringLocaleConvertCase', 'StringParseFloat', 'StringParseInt', 'StringPrototypeEndsWith', 'StringPrototypeLastIndexOf', 'StringPrototypeStartsWith', 'StringPrototypeToUpperCaseIntl', 'StringReplaceNonGlobalRegExpWithFunction', 'StringSplit', 'StringToArray', 'StringToLowerCaseIntl', 'StringToNumber', 'StringTrim', 'SubString', 'SymbolConstructor', 'SymbolFor', 'Throw', 'ThrowCalledNonCallable', 'ThrowConstructedNonConstructable', 'ThrowIteratorResultNotAnObject', 'ThrowTypeError', 'ToString', 'Total', 'TransitionElementsKind', 'TryMigrateInstance', 'TrySliceSimpleNonFastElements', 'TypedArrayCopyElements', 'TypedArrayGetBuffer', 'TypedArrayGetLength', 'TypedArrayPrototypeBuffer', 'UnwindAndFindExceptionHandler', 'WeakCollectionSet'];
  const RUNTIMESTATS_MEASUREMENTS = [];
  for (const base of RUNTIMESTATS_MEASUREMENT_BASES) {
    RUNTIMESTATS_MEASUREMENTS.push(base + ':count');
    RUNTIMESTATS_MEASUREMENTS.push(base + ':duration');
  }
  MEASUREMENTS_BY_TEST_SUITE.set('v8:RuntimeStats', RUNTIMESTATS_MEASUREMENTS);

  BOTS_BY_TEST_SUITE.set('system_health.common_desktop', [
    'ChromiumPerf:chromium-rel-mac-retina',
    'ChromiumPerf:chromium-rel-mac11',
    'ChromiumPerf:chromium-rel-mac11-air',
    'ChromiumPerf:chromium-rel-mac11-pro',
    'ChromiumPerf:chromium-rel-mac12',
    'ChromiumPerf:chromium-rel-mac12-mini-8gb',
    'ChromiumPerf:chromium-rel-win10',
    'ChromiumPerf:chromium-rel-win7-dual',
    'ChromiumPerf:chromium-rel-win7-gpu-ati',
    'ChromiumPerf:chromium-rel-win7-gpu-intel',
    'ChromiumPerf:chromium-rel-win7-gpu-nvidia',
    'ChromiumPerf:chromium-rel-win7-x64-dual',
    'ChromiumPerf:chromium-rel-win8-dual',
    'ChromiumPerf:linux-release',
    'ChromiumPerf:win-high-dpi',
  ]);
  BOTS_BY_TEST_SUITE.set('system_health.memory_desktop',
      BOTS_BY_TEST_SUITE.get('system_health.common_desktop'));

  BOTS_BY_TEST_SUITE.set('system_health.common_mobile', [
    'ChromiumPerf:android-nexus5',
    'ChromiumPerf:android-nexus5X',
    'ChromiumPerf:android-nexus6',
    'ChromiumPerf:android-nexus7v2',
    'ChromiumPerf:android-one',
    'ChromiumPerf:android-webview-nexus5X',
    'ChromiumPerf:android-webview-nexus6',
  ]);
  BOTS_BY_TEST_SUITE.set('system_health.memory_mobile',
      BOTS_BY_TEST_SUITE.get('system_health.common_mobile'));

  const V8_BOTS = [
    'internal.client.v8:Atom_x64',
    'internal.client.v8:ChromeOS',
    'internal.client.v8:Haswell_x64',
    'internal.client.v8:Nexus10',
    'internal.client.v8:Nexus5',
    'internal.client.v8:Nexus7',
    'internal.client.v8:Volantis',
    'internal.client.v8:ia32',
    'internal.client.v8:x64',
  ];

  for (const testSuite of V8_TEST_SUITES) {
    BOTS_BY_TEST_SUITE.set(testSuite, V8_BOTS);
  }

  TEST_CASES_BY_TEST_SUITE.set('v8:JSTests', ['LongString-StringConcat-10', 'LongString-StringConcat-2', 'LongString-StringConcat-3', 'LongString-StringConcat-5', 'Number-Add', 'Number-And', 'Number-Decrement', 'Number-Div', 'Number-Equals-False', 'Number-Equals-True', 'Number-Increment', 'Number-Mod', 'Number-Mul', 'Number-Oddball-Add', 'Number-Oddball-Div', 'Number-Oddball-Mod', 'Number-Oddball-Mul', 'Number-Oddball-Sub', 'Number-Or', 'Number-RelationalCompare', 'Number-ShiftLeft', 'Number-ShiftRight', 'Number-ShiftRightLogical', 'Number-StrictEquals-False', 'Number-StrictEquals-True', 'Number-String-Add', 'Number-Sub', 'Number-Xor', 'NumberString-StringConcat-10', 'NumberString-StringConcat-2', 'NumberString-StringConcat-3', 'NumberString-StringConcat-5', 'Object-Add', 'Object-Div', 'Object-Mod', 'Object-Mul', 'Object-Sub', 'ObjectNull-Equals', 'ShortString-StringConcat-10', 'ShortString-StringConcat-2', 'ShortString-StringConcat-3', 'ShortString-StringConcat-5', 'Smi-Add', 'Smi-And', 'Smi-Constant-Add', 'Smi-Constant-And', 'Smi-Constant-Div', 'Smi-Constant-Mod', 'Smi-Constant-Mul', 'Smi-Constant-Or', 'Smi-Constant-ShiftLeft', 'Smi-Constant-ShiftRight', 'Smi-Constant-ShiftRightLogical', 'Smi-Constant-Sub', 'Smi-Constant-Xor', 'Smi-Decrement', 'Smi-Div', 'Smi-Equals-False', 'Smi-Equals-True', 'Smi-Increment', 'Smi-Mod', 'Smi-Mul', 'Smi-Or', 'Smi-RelationalCompare', 'Smi-ShiftLeft', 'Smi-ShiftRight', 'Smi-ShiftRightLogical', 'Smi-StrictEquals-False', 'Smi-StrictEquals-True', 'Smi-Sub', 'Smi-Xor', 'SmiString-Equals', 'SmiString-RelationalCompare', 'SmiString-StrictEquals', 'String-Add', 'String-Equals-False', 'String-Equals-True', 'String-RelationalCompare', 'String-StrictEquals-False', 'String-StrictEquals-True', 'Total']);
  TEST_CASES_BY_TEST_SUITE.set('v8:RuntimeStats', ['Total:Default', 'Total:Future', 'adwords.google.com:Default', 'adwords.google.com:Future', 'baidu.com:Default', 'baidu.com:Future', 'bcc.co.uk-amp:Default', 'bcc.co.uk-amp:Future', 'bing.com:Default', 'bing.com:Future', 'cnn.com:Default', 'cnn.com:Future', 'discourse.org:Default', 'discourse.org:Future', 'ebay.fr:Default', 'ebay.fr:Future', 'facebook.com:Default', 'facebook.com:Future', 'google.de:Default', 'google.de:Future', 'inbox.google.com:Default', 'inbox.google.com:Future', 'instagram.com:Default', 'instagram.com:Future', 'linkedin.com:Default', 'linkedin.com:Future', 'maps.google.co.jp:Default', 'maps.google.co.jp:Future', 'msn.com:Default', 'msn.com:Future', 'pinterest.com:Default', 'pinterest.com:Future', 'qq.com:Default', 'qq.com:Future', 'reddit.com:Default', 'reddit.com:Future', 'reddit.musicplayer.io:Default', 'reddit.musicplayer.io:Future', 'sina.com.cn:Default', 'sina.com.cn:Future', 'speedometer-angular:Default', 'speedometer-angular:Future', 'speedometer-backbone:Default', 'speedometer-backbone:Future', 'speedometer-ember:Default', 'speedometer-ember:Future', 'speedometer-jquery:Default', 'speedometer-jquery:Future', 'speedometer-vanilla:Default', 'speedometer-vanilla:Future', 'taobao.com:Default', 'taobao.com:Future', 'twitter.com:Default', 'twitter.com:Future', 'weibo.com:Default', 'weibo.com:Future', 'wikipedia.org-visual-editor:Default', 'wikipedia.org-visual-editor:Future', 'wikipedia.org:Default', 'wikipedia.org:Future', 'wikiwand.com:Default', 'wikiwand.com:Future', 'yahoo.co.jp:Default', 'yahoo.co.jp:Future', 'yandex.ru:Default', 'yandex.ru:Future', 'youtube.com-polymer-watch:Default', 'youtube.com-polymer-watch:Future', 'youtube.com:Default', 'youtube.com:Future']);

  const SYSTEM_HEALTH_TEST_CASES = [
    'blank:about:blank',
    'browse:media:facebook_photos',
    'browse:media:imgur',
    'browse:media:youtube',
    'browse:news:flipboard',
    'browse:news:hackernews',
    'browse:news:nytimes',
    'browse:news:qq',
    'browse:news:reddit',
    'browse:news:washingtonpost',
    'browse:social:facebook',
    'browse:social:twitter',
    'load:games:bubbles',
    'load:games:lazors',
    'load:games:spychase',
    'load:media:9gag',
    'load:media:dailymotion',
    'load:media:facebook_photos',
    'load:media:flickr',
    'load:media:google_images',
    'load:media:imgur',
    'load:media:soundcloud',
    'load:media:youtube',
    'load:news:bbc',
    'load:news:cnn',
    'load:news:flipboard',
    'load:news:hackernews',
    'load:news:nytimes',
    'load:news:qq',
    'load:news:reddit',
    'load:news:sohu',
    'load:news:washingtonpost',
    'load:news:wikipedia',
    'load:search:amazon',
    'load:search:baidu',
    'load:search:ebay',
    'load:search:google',
    'load:search:taobao',
    'load:search:yahoo',
    'load:search:yandex',
    'load:social:facebook',
    'load:social:instagram',
    'load:social:pinterest',
    'load:social:tumblr',
    'load:social:twitter',
    'load:tools:docs',
    'load:tools:drive',
    'load:tools:dropbox',
    'load:tools:gmail',
    'load:tools:maps',
    'load:tools:stackoverflow',
    'load:tools:weather',
    'search:portal:google',
  ];

  for (const testSuite of SYSTEM_HEALTH_TEST_SUITES) {
    TEST_CASES_BY_TEST_SUITE.set(testSuite, SYSTEM_HEALTH_TEST_CASES);
  }

  /* eslint-enable max-len */

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
