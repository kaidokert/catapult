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
      'group:chrome',
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

  function dummyTestSuites() {
    return SYSTEM_HEALTH_TEST_SUITES;
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

  const SYSTEM_HEALTH_TEST_CASES = [
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
    'load:chrome:blank',
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
