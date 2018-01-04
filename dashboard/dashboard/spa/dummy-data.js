/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

tr.exportTo('cp', () => {
  function dummyAlertsSources() {
    return [
      'Bug:543210',
      'Bug:654321',
      'Bug:765432',
      'Bug:876543',
      'Bug:987654',
      'Sheriff:ARC',
      'Sheriff:Angle',
      'Sheriff:Binary Size',
      'Sheriff:Blink Memory Mobile',
      'Sheriff:Chrome OS Graphics',
      'Sheriff:Chrome OS Installer',
      'Sheriff:Chrome OS',
      'Sheriff:Chrome Accessibility',
      'Sheriff:Chromium AV',
      'Sheriff:Chromium',
      'Sheriff:CloudView',
      'Sheriff:Cronet',
      'Sheriff:Jochen',
      'Sheriff:Mojo',
      'Sheriff:NaCl',
      'Sheriff:Network Service',
      'Sheriff:OWP Storage',
      'Sheriff:Oilpan',
      'Sheriff:Pica',
      'Sheriff:Power',
      'Sheriff:Service Worker',
      'Sheriff:Tracing',
      'Sheriff:V8 Memory',
      'Sheriff:V8',
      'Sheriff:WebView',
      'Releasing:M63:Public',
      'Releasing:M63:Memory',
      'Releasing:M63:Power',
      'Releasing:M64:Public',
      'Releasing:M64:Memory',
      'Releasing:M64:Power',
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

  function dummyAlerts(improvements) {
    const alerts = [];
    for (let i = 0; i < 10; ++i) {
      const revs = new tr.b.math.Range();
      revs.addValue(parseInt(1e7 * Math.random()));
      revs.addValue(parseInt(1e7 * Math.random()));
      alerts.push({
        bot: 'android-nexus5',
        end_revision: revs.max,
        improvement: improvements && (Math.random() > 0.5),
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
    for (let bi = 0; bi < section.chartLayout.xBrushes.length; bi += 2) {
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

  function dummyBots(testSuites) {
    const bots = [];
    if (testSuites.filter(s => s.indexOf('v8') === 0).length) {
      bots.push.apply(bots, [
        'internal.client.v8:Nexus5',
        'internal.client.v8:Nexus7',
        'internal.client.v8:Volantis',
        'internal.client.v8:ia32',
        'internal.client.v8:x64',
      ]);
    }
    if (testSuites.filter(
        s => s.indexOf('system_health.common') === 0).length) {
      bots.push.apply(bots, [
        'ChromiumPerf:android-nexus5',
        'ChromiumPerf:android-nexus5X',
        'ChromiumPerf:android-nexus6',
        'ChromiumPerf:android-nexus7v2',
        'ChromiumPerf:android-one',
        'ChromiumPerf:android-webview-nexus5X',
        'ChromiumPerf:android-webview-nexus6',
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
    }
    return bots;
  }

  function dummyMeasurements(testSuites) {
    const measurements = ['benchmark_duration'];
    if (testSuites.filter(s => s.indexOf('v8') === 0).length) {
      measurements.push.apply(measurements, []);
    }
    if (testSuites.filter(
        s => s.indexOf('system_health.common') === 0).length) {
      measurements.push.apply(measurements, [
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
    }
    return measurements;
  }

  function dummyStories(testSuites) {
    const stories = [];
    if (testSuites.filter(s => s.indexOf('v8') === 0).length) {
      stories.push.apply(stories, []);
    }
    if (testSuites.filter(s => s.indexOf('system_health') === 0).length) {
      stories.push.apply(stories, [
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
      ]);
    }
    return stories;
  }

  function dummyStoryTags(testSuites) {
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

  function todo(msg) {
    // eslint-disable-next-line no-console
    console.log('TODO ' + msg);
  }

  return {
    dummyAlerts,
    dummyBots,
    dummyHistograms,
    dummyMeasurements,
    dummyReleasingSection,
    dummyAlertsSources,
    dummyStories,
    dummyStoryTags,
    dummyTimeseries,
    todo,
  };
});
