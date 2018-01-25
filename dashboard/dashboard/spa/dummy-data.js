/* Copyright 2017 The Chromium Authors. All rights reserved.
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

  function dummyTimeseries(improvement, unit) {
    const data = [];
    const sequenceLength = 100;
    for (let i = 0; i < sequenceLength; i += 1) {
      const value = parseInt(100 * Math.random());
      data.push({
        x: parseInt(100 * i / sequenceLength),
        y: value,
        value: unit.format(value),
        chromiumCommitPositions: [123, 456],
      });
    }
    data[parseInt(Math.random() * sequenceLength)].icon = (
      improvement ? 'thumb-up' : 'error');
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
      // These are test path components 0:1
      bots.push.apply(bots, [
        'internal.client.v8:Atom_x64',
        'internal.client.v8:ChromeOS',
        'internal.client.v8:Haswell_x64',
        'internal.client.v8:Nexus10',
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

  // test path component 4
  const V8_MEASUREMENT0S = [
    '164.gzip', '177.mesa', '179.art', '181.mcf', '1k_functions', '256.bzip2',
    '2D Physics Boxes', '2D Physics Spheres', '3d-cube', '3d-morph',
    '3d-raytrace', '3dCube', '3dMorph', '3dRaytrace', 'API:ArrayBuffer_Neuter',
    'API:ArrayBuffer_New', 'API:Array_New', 'API:Context_New', 'API:Error_New',
    'API:External_New', 'API:Float32Array_New',
    'API:FunctionTemplate_GetFunction', 'API:FunctionTemplate_New',
    'API:FunctionTemplate_NewWithCache', 'API:Function_Call',
    'API:Function_New', 'API:Function_NewInstance', 'API:Int32Array_New',
    'API:ObjectTemplate_New', 'API:Object_CreateDataProperty',
    'API:Object_DefineOwnProperty', 'API:Object_Delete', 'API:Object_Get',
    'API:Object_GetPropertyAttributes', 'API:Object_GetPropertyNames',
    'API:Object_Has', 'API:Object_HasOwnProperty', 'API:Object_New',
    'API:Object_Set', 'API:Object_SetAccessor', 'API:Object_SetIntegrityLevel',
    'API:Object_SetPrivate', 'API:Object_SetPrototype', 'API:Object_ToNumber',
    'API:Object_ToString', 'API:Persistent_New', 'API:Private_New',
    'API:Promise_Resolver_New', 'API:Promise_Resolver_Reject',
    'API:Promise_Resolver_Resolve', 'API:ScriptCompiler_Compile',
    'API:ScriptCompiler_CompileFunctionInContext',
    'API:ScriptCompiler_CompileUnbound', 'API:Script_Run', 'API:String_Concat',
    'API:String_NewExternalOneByte', 'API:String_NewExternalTwoByte',
    'API:String_NewFromOneByte', 'API:String_NewFromTwoByte',
    'API:String_NewFromUtf8', 'API:String_Write', 'API:String_WriteUtf8',
    'API:ValueDeserializer_ReadHeader', 'API:ValueDeserializer_ReadValue',
    'API:ValueSerializer_WriteValue', 'AccessBinaryTrees', 'AccessFannkuch',
    'AccessNbody', 'AccessNsieve', 'AccessorGetterCallback',
    'AddDictionaryProperty', 'Air averageWorstCase', 'Air firstIteration',
    'Air steadyState', 'AllocateInNewSpace', 'AllocateInTargetSpace',
    'AngryBots', 'AngryBots-Async', 'Animation and Skinning', 'Array',
    'Array pattern destructuring', 'ArrayBufferConstructor_ConstructStub',
    'ArrayBufferConstructor_DoNotInitialize',
    'ArrayBufferPrototypeGetByteLength',
    'ArrayBufferPrototypeSlice', 'ArrayBufferViewGetByteLength',
    'ArrayBufferViewGetByteOffset', 'ArrayBufferViewWasNeutered', 'ArrayConcat',
    'ArrayIndexOf', 'ArrayLengthGetter', 'ArrayLengthSetter', 'ArrayPop',
    'ArrayPush', 'ArrayShift', 'ArraySpeciesConstructor', 'ArraySplice',
    'ArrayUnshift', 'Asteroid Field', 'AsyncAwait', 'AvailableLocalesOf',
    'Babylon averageWorstCase', 'Babylon firstIteration', 'Babylon steadyState',
    'Basic averageWorstCase', 'Basic firstIteration', 'Basic steadyState',
    'Bitops3bitBitsInByte', 'BitopsBitsInByte', 'BitopsBitwiseAnd',
    'BitopsNsieveBits', 'BooleanConstructor',
    'BooleanConstructor_ConstructStub', 'BoundFunctionLengthGetter',
    'BoundFunctionNameGetter', 'Box2D', 'Box2D-F32', 'Box2d', 'Box2dLoadTime',
    'Box2dThroughput', 'Bullet', 'BulletLoadTime', 'BulletThroughput',
    'BytecodeHandlers', 'CanonicalizeLanguageTag', 'Classes', 'Closures',
    'ClosuresMarkForTierUp', 'CodeLoad', 'Collections', 'Compile:Analyse',
    'Compile:BackgroundAnalyse', 'Compile:BackgroundIgnition',
    'Compile:BackgroundRenumber', 'Compile:BackgroundRewriteReturnResult',
    'Compile:BackgroundScopeAnalysis', 'Compile:BackgroundScript',
    'Compile:Deserialize', 'Compile:Eval', 'Compile:ForOnStackReplacement',
    'Compile:Function', 'Compile:GetFromOptimizedCodeMap', 'Compile:Ignition',
    'Compile:IgnitionFinalization', 'Compile:Lazy',
    'Compile:Optimized_NotConcurrent', 'Compile:Renumber',
    'Compile:RewriteReturnResult', 'Compile:ScopeAnalysis', 'Compile:Script',
    'Compile:Serialize', 'CompleteInobjectSlackTrackingForMap',
    'Computed property names in object literals', 'ConsoleAssert',
    'ConsoleDebug', 'ConsoleError', 'ConsoleInfo', 'ConsoleLog', 'ConsoleTime',
    'ConsoleTimeStamp', 'ConsoleWarn', 'ControlflowRecursive', 'Copy',
    'Corrections', 'CreateArrayLiteral', 'CreateDataProperty',
    'CreateListFromArrayLike', 'CreateNumberFormat', 'CreateObjectLiteral',
    'CreateRegExpLiteral', 'Crypto', 'CryptoAes', 'CryptoMd5', 'CryptoSha1',
    'Cryptohash', 'DataViewConstructor_ConstructStub',
    'DataViewPrototypeGetBuffer', 'DataViewPrototypeGetByteLength',
    'DataViewPrototypeGetByteOffset', 'DataViewPrototypeGetFloat32',
    'DataViewPrototypeGetUint32', 'DataViewPrototypeGetUint8',
    'DateConstructor_ConstructStub', 'DateCurrentTime', 'DateFormatTofte',
    'DateFormatXparb', 'DateNow', 'DateParse', 'DatePrototypeGetYear',
    'DatePrototypeSetDate', 'DatePrototypeSetFullYear', 'DatePrototypeSetHours',
    'DatePrototypeSetMilliseconds', 'DatePrototypeSetMinutes',
    'DatePrototypeSetMonth', 'DatePrototypeSetSeconds', 'DatePrototypeSetTime',
    'DatePrototypeSetUTCDate', 'DatePrototypeSetYear',
    'DatePrototypeToDateString', 'DatePrototypeToISOString',
    'DatePrototypeToJson', 'DatePrototypeToString', 'DatePrototypeToUTCString',
    'DateUTC', 'DeclareEvalFunction', 'DeclareEvalVar',
    'DeclareGlobalsForInterpreter', 'Defaults',
    'DefineAccessorPropertyUnchecked', 'DefineDataPropertyInLiteral',
    'DeleteLookupSlot', 'DeleteProperty', 'DeltaBlue', 'DeoptimizeCode',
    'DeserializeLazy', 'EarleyBoyer', 'ElementsTransitionAndStoreIC_Miss',
    'EnqueuePromiseReactionJob', 'EnqueuePromiseResolveThenableJob',
    'ErrorCaptureStackTrace', 'ErrorConstructor', 'ErrorPrototypeToString',
    'EstimateNumberOfElements', 'EvaluateFibonacci', 'EvictOptimizedCodeSlot',
    'Exceptions', 'ExpressionDepth', 'Fannkuch', 'Fasta', 'ForInEnumerate',
    'ForInHasProperty', 'ForLoops', 'FunctionCallback', 'FunctionConstructor',
    'FunctionLengthGetter', 'FunctionPrototypeGetter',
    'FunctionPrototypeSetter', 'FunctionPrototypeToString',
    'GCEpilogueCallback', 'GCPrologueCallback',
    'GC:BACKGROUND_ARRAY_BUFFER_FREE', 'GC:BACKGROUND_STORE_BUFFER',
    'GC:BACKGROUND_UNMAPPER', 'GC:Custom_IncrementalMarkingObserver',
    'GC:Custom_SlowAllocateRaw', 'GC:HEAP_EPILOGUE',
    'GC:HEAP_EPILOGUE_REDUCE_NEW_SPACE', 'GC:HEAP_EXTERNAL_EPILOGUE',
    'GC:HEAP_EXTERNAL_PROLOGUE', 'GC:HEAP_EXTERNAL_WEAK_GLOBAL_HANDLES',
    'GC:HEAP_PROLOGUE', 'GC:MC_BACKGROUND_EVACUATE_COPY',
    'GC:MC_BACKGROUND_EVACUATE_UPDATE_POINTERS', 'GC:MC_BACKGROUND_MARKING',
    'GC:MC_BACKGROUND_SWEEPING', 'GC:MC_CLEAR', 'GC:MC_CLEAR_DEPENDENT_CODE',
    'GC:MC_CLEAR_MAPS', 'GC:MC_CLEAR_STRING_TABLE', 'GC:MC_CLEAR_WEAK_CELLS',
    'GC:MC_CLEAR_WEAK_COLLECTIONS', 'GC:MC_CLEAR_WEAK_LISTS', 'GC:MC_EPILOGUE',
    'GC:MC_EVACUATE', 'GC:MC_EVACUATE_CLEAN_UP', 'GC:MC_EVACUATE_COPY',
    'GC:MC_EVACUATE_EPILOGUE', 'GC:MC_EVACUATE_PROLOGUE',
    'GC:MC_EVACUATE_REBALANCE', 'GC:MC_EVACUATE_UPDATE_POINTERS',
    'GC:MC_EVACUATE_UPDATE_POINTERS_SLOTS_MAIN',
    'GC:MC_EVACUATE_UPDATE_POINTERS_SLOTS_MAP_SPACE',
    'GC:MC_EVACUATE_UPDATE_POINTERS_TO_NEW_ROOTS',
    'GC:MC_EVACUATE_UPDATE_POINTERS_WEAK', 'GC:MC_FINISH', 'GC:MC_INCREMENTAL',
    'GC:MC_INCREMENTAL_EXTERNAL_EPILOGUE',
    'GC:MC_INCREMENTAL_EXTERNAL_PROLOGUE', 'GC:MC_INCREMENTAL_FINALIZE',
    'GC:MC_INCREMENTAL_FINALIZE_BODY', 'GC:MC_INCREMENTAL_START',
    'GC:MC_INCREMENTAL_SWEEPING', 'GC:MC_INCREMENTAL_WRAPPER_PROLOGUE',
    'GC:MC_INCREMENTAL_WRAPPER_TRACING', 'GC:MC_MARK',
    'GC:MC_MARK_FINISH_INCREMENTAL', 'GC:MC_MARK_MAIN', 'GC:MC_MARK_ROOTS',
    'GC:MC_MARK_WEAK_CLOSURE', 'GC:MC_MARK_WEAK_CLOSURE_EPHEMERAL',
    'GC:MC_MARK_WEAK_CLOSURE_HARMONY', 'GC:MC_MARK_WEAK_CLOSURE_WEAK_HANDLES',
    'GC:MC_MARK_WEAK_CLOSURE_WEAK_ROOTS', 'GC:MC_MARK_WRAPPER_EPILOGUE',
    'GC:MC_MARK_WRAPPER_PROLOGUE', 'GC:MC_MARK_WRAPPER_TRACING',
    'GC:MC_PROLOGUE', 'GC:MC_SWEEP', 'GC:MC_SWEEP_CODE', 'GC:MC_SWEEP_MAP',
    'GC:MC_SWEEP_OLD', 'GC:SCAVENGER_BACKGROUND_SCAVENGE_PARALLEL',
    'GC:SCAVENGER_PROCESS_ARRAY_BUFFERS', 'GC:SCAVENGER_SCAVENGE',
    'GC:SCAVENGER_SCAVENGE_PARALLEL', 'GC:SCAVENGER_SCAVENGE_ROOTS',
    'GC:SCAVENGER_SCAVENGE_WEAK',
    'GC:SCAVENGER_SCAVENGE_WEAK_GLOBAL_HANDLES_IDENTIFY',
    'GC:SCAVENGER_SCAVENGE_WEAK_GLOBAL_HANDLES_PROCESS', 'Gameboy',
    'GenerateRandomNumbers', 'Generators', 'Geometric mean',
    'GetDefaultICULocale', 'GetMoreDataCallback', 'GetProperty',
    'GlobalDecodeURI', 'GlobalDecodeURIComponent', 'GlobalEncodeURI',
    'GlobalEncodeURIComponent', 'GlobalEscape', 'GlobalEval', 'GlobalUnescape',
    'Group-API', 'Group-Callback', 'Group-Compile', 'Group-Compile-Total',
    'Group-CompileBackground', 'Group-GC', 'Group-GC-Background',
    'Group-GC-Custom', 'Group-IC', 'Group-JavaScript', 'Group-Optimize',
    'Group-Parse', 'Group-Parse-Total', 'Group-ParseBackground',
    'Group-Runtime', 'Group-Total-V8', 'HandleApiCall', 'HasComplexElements',
    'HasFastPackedElements', 'HasInPrototypeChain', 'HasProperty', 'Ignition',
    'IndexedDescriptorCallback', 'IndexedEnumeratorCallback', 'Inspector',
    'Instantiate and Destroy', 'Instantiate-Microbench', 'InternalNumberFormat',
    'InterpreterDeserializeLazy', 'InterpreterNewClosure', 'Interrupt',
    'IsConstructor', 'IsInitializedIntlObjectOfType',
    'IterableToListCanBeElided', 'Iterators', 'JSBenchAmazon',
    'JSBenchFacebook', 'JSBenchGoogle', 'JS_Execution', 'JsonParse',
    'JsonStringify', 'KeyedGetProperty',
    'KeyedLoadIC_KeyedLoadSloppyArgumentsStub', 'KeyedLoadIC_LoadElementDH',
    'KeyedLoadIC_LoadIndexedInterceptorStub', 'KeyedLoadIC_LoadIndexedStringDH',
    'KeyedLoadIC_Miss', 'KeyedStoreIC_ElementsTransitionAndStoreStub',
    'KeyedStoreIC_Miss', 'KeyedStoreIC_Slow', 'KeyedStoreIC_StoreElementStub',
    'KeyedStoreIC_StoreFastElementStub', 'Keys', 'Life',
    'LoadElementWithInterceptor', 'LoadGlobalIC_LoadScriptContextField',
    'LoadGlobalIC_Miss', 'LoadGlobalIC_Slow', 'LoadIC:FunctionPrototypeStub',
    'LoadIC:LoadAccessorDH', 'LoadIC:LoadAccessorFromPrototypeDH',
    'LoadIC:LoadApiGetterFromPrototypeDH', 'LoadIC:LoadConstantDH',
    'LoadIC:LoadConstantFromPrototypeDH', 'LoadIC:LoadFieldDH',
    'LoadIC:LoadFieldFromPrototypeDH', 'LoadIC:LoadGlobalDH',
    'LoadIC:LoadInterceptorDH', 'LoadIC:LoadNativeDataPropertyDH',
    'LoadIC:LoadNativeDataPropertyFromPrototypeDH',
    'LoadIC:LoadNonMaskingInterceptorDH', 'LoadIC:LoadNonexistentDH',
    'LoadIC:LoadNormalDH', 'LoadIC:LoadNormalFromPrototypeDH', 'LoadIC:Miss',
    'LoadIC:NonReceiver', 'LoadIC:Premonomorphic', 'LoadIC:SlowStub',
    'LoadIC:StringLength', 'LoadLookupSlot', 'LoadLookupSlotForCall',
    'LoadLookupSlotInsideTypeof', 'LoadPropertyWithInterceptor',
    'LuaBinaryTrees', 'LuaBinaryTreesLoadTime', 'LuaBinaryTreesThroughput',
    'LuaScimark', 'ML averageWorstCase', 'ML firstIteration', 'ML steadyState',
    'Mandelbrot', 'Mandreel', 'MandreelLatency', 'ManyClosures',
    'Map get string', 'Map-Set add-set-has', 'Map-Set add-set-has object',
    'Map-Set has', 'MapGrow', 'MapShrink', 'Map_SetPrototype',
    'Map_TransitionToAccessorProperty', 'Map_TransitionToDataProperty',
    'MarkAsInitializedIntlObjectOfType', 'MathCordic', 'MathPartialSums',
    'MathSpectralNorm', 'MemOps', 'Modules', 'NBodyJava',
    'NamedEnumeratorCallback', 'NamedGetterCallback', 'NamedQueryCallback',
    'NamedSetterCallback', 'NavierStokes', 'NewArray', 'NewDocument',
    'NewObject', 'NewSloppyArguments_Generic', 'NotifyDeoptimized',
    'NumberPrototypeToFixed', 'NumberPrototypeToPrecision',
    'NumberPrototypeToString', 'NumberToString', 'Object', 'ObjectAssign',
    'ObjectCreate', 'ObjectDefineProperties', 'ObjectDefineProperty',
    'ObjectEntries', 'ObjectEntriesSkipFastPath', 'ObjectFreeze',
    'ObjectGetOwnPropertyNames', 'ObjectGetOwnPropertySymbols',
    'ObjectGetPrototypeOf', 'ObjectHasOwnProperty', 'ObjectIsExtensible',
    'ObjectIsFrozen', 'ObjectIsSealed', 'ObjectKeys', 'ObjectLookupGetter',
    'ObjectLookupSetter', 'ObjectPreventExtensions', 'ObjectPrototypeGetProto',
    'ObjectPrototypePropertyIsEnumerable', 'ObjectPrototypeSetProto',
    'ObjectSeal', 'ObjectSetPrototypeOf', 'ObjectValues',
    'Object_DeleteProperty', 'OptimizeCode', 'OrdinaryHasInstance', 'P256',
    'ParseArrowFunctionLiteral', 'ParseBackgroundFunctionLiteral',
    'ParseBackgroundProgram', 'ParseEval', 'ParseFunction',
    'ParseFunctionLiteral', 'ParseProgram', 'Parsing', 'PdfJS', 'Performance',
    'Physics Spheres', 'Poppler', 'PreParseBackgroundNoVariableResolution',
    'PreParseBackgroundWithVariableResolution', 'PreParseNoVariableResolution',
    'PreParseWithVariableResolution', 'Primes', 'PromiseRevokeReject',
    'PropertyQueries', 'PrototypeMap_TransitionToAccessorProperty',
    'PrototypeMap_TransitionToDataProperty', 'PrototypeObject_DeleteProperty',
    'Proxies', 'PushBlockContext', 'PushCatchContext', 'PushWithContext', 'RSA',
    'RayTrace', 'ReThrow', 'RecompileSynchronous', 'ReconfigureToDataProperty',
    'ReflectDefineProperty', 'RegExp', 'RegExpCapture1Getter',
    'RegExpCapture2Getter', 'RegExpCapture3Getter', 'RegExpCapture4Getter',
    'RegExpCapture5Getter', 'RegExpCapture6Getter', 'RegExpCapture7Getter',
    'RegExpCapture8Getter', 'RegExpCapture9Getter', 'RegExpExec',
    'RegExpExecMultiple', 'RegExpInitializeAndCompile', 'RegExpInputGetter',
    'RegExpInternalReplace', 'RegExpLastMatchGetter', 'RegExpPrototypeToString',
    'RegExpReplace', 'RegExpSplit', 'RegexpDna', 'RemoveArrayHoles',
    'ReportPromiseReject', 'ReservedMemoryContext', 'ReservedMemoryIsolate',
    'ResolvePossiblyDirectEval', 'RestParameters', 'Richards', 'SQLite',
    'Scope', 'SetNativeFlag', 'SetProperty', 'ShrinkPropertyDictionary',
    'Skinning', 'SnapshotSizeBuiltins', 'SnapshotSizeContext',
    'SnapshotSizeStartup', 'SortNumbers', 'Splay', 'SplayLatency', 'Spread',
    'SpreadCalls', 'SpreadLiteral', 'Sqlite', 'Sqlite-Async', 'StackGuard',
    'StoreCallbackProperty', 'StoreGlobalIC_Miss', 'StoreGlobalIC_Slow',
    'StoreIC:Miss', 'StoreIC:NonReceiver', 'StoreIC:Premonomorphic',
    'StoreIC:SlowStub', 'StoreIC:StoreAccessorOnPrototypeDH',
    'StoreIC:StoreApiSetterOnPrototypeDH', 'StoreIC:StoreFieldDH',
    'StoreIC:StoreGlobalDH', 'StoreIC:StoreInterceptorStub',
    'StoreIC:StoreNativeDataPropertyDH', 'StoreIC:StoreNormalDH',
    'StoreIC:StoreTransitionDH', 'StoreLookupSlot_Sloppy', 'String:Add',
    'String:Base64', 'String:BuilderConcat', 'String:BuilderJoin',
    'String:CharCodeAt', 'String:Equal', 'String:Fasta', 'String:GreaterThan',
    'String:GreaterThanOrEqual', 'String:Includes', 'String:IndexOf',
    'String:IndexOfUnchecked', 'String:Iterators', 'String:LengthGetter',
    'String:LessThan', 'String:LessThanOrEqual', 'String:LocaleConvertCase',
    'String:ParseFloat', 'String:ParseInt', 'String:PrototypeEndsWith',
    'String:PrototypeLastIndexOf', 'String:PrototypeStartsWith',
    'String:PrototypeToUpperCaseIntl',
    'String:ReplaceNonGlobalRegExpWithFunction', 'String:Split',
    'String:Tagcloud', 'String:ToArray', 'String:ToLowerCaseIntl',
    'String:ToNumber', 'String:Trim', 'String:UnpackCode',
    'String:ValidateInput', 'Strings', 'SubString', 'Super',
    'SuperSpread', 'SymbolConstructor', 'SymbolFor', 'Templates', 'Throw',
    'ThrowCalledNonCallable', 'ThrowConstructedNonConstructable',
    'ThrowIteratorResultNotAnObject', 'ThrowTypeError', 'ToString', 'Total',
    'Total summary', 'Traceur', 'TransitionElementsKind', 'TryMigrateInstance',
    'TrySliceSimpleNonFastElements', 'TypedArrayCopyElements',
    'TypedArrayGetBuffer', 'TypedArrayGetLength', 'TypedArrayPrototypeBuffer',
    'TypedArrays', 'Typescript', 'UnwindAndFindExceptionHandler',
    'VLookupCells', 'WeakCollectionSet', 'ZLib', 'ZlibLoadTime',
    'ZlibThroughput', 'access-binary-trees', 'access-fannkuch', 'access-nbody',
    'access-nsieve', 'acorn', 'add:big-i32-10-Liftoff',
    'add:big-i32-10-Turbofan', 'add:big-i32-100-Liftoff',
    'add:big-i32-100-Turbofan', 'add:big-i32-1000-Liftoff',
    'add:big-i32-1000-Turbofan', 'add:small-i32-10-Liftoff',
    'add:small-i32-10-Turbofan', 'add:small-i32-100-Liftoff',
    'add:small-i32-100-Turbofan', 'add:small-i32-1000-Liftoff',
    'add:small-i32-1000-Turbofan', 'ai-astar', 'angular', 'asm_loop',
    'audio-beat-detection', 'audio-dft', 'audio-fft', 'audio-oscillator',
    'babel', 'babylon', 'base64', 'bigfib', 'bigfib.cpp',
    'bitops-3bit-bits-in-byte', 'bitops-bits-in-byte', 'bitops-bitwise-and',
    'bitops-nsieve-bits', 'bluebird-doxbee', 'bluebird-parallel', 'box2d',
    'buble', 'chai', 'code-first-load', 'code-multi-load', 'coffeescript',
    'constant', 'container', 'container.cpp', 'controlflow-recursive', 'cordic',
    'crypto', 'crypto-aes', 'crypto-md5', 'crypto-sha1', 'date-format-tofte',
    'date-format-xparb', 'delta-blue', 'dry', 'dry.c', 'earley-boyer', 'ember',
    'espree', 'esprima', 'fib-32-10-Liftoff', 'fib-32-10-Turbofan',
    'fib-32-100-Liftoff', 'fib-32-100-Turbofan', 'fib-32-1000-Liftoff',
    'fib-32-1000-Turbofan', 'float-mm', 'float-mm.c', 'gbemu', 'gcc-loops',
    'gcc-loops.cpp', 'get_object', 'hash-map', 'imaging-darkroom',
    'imaging-desaturate', 'imaging-gaussian-blur', 'jquery', 'jshint',
    'json-parse-financial', 'json-stringify-tinderbox', 'lebab', 'mandreel',
    'mandreel-latency', 'math-cordic', 'math-partial-sums',
    'math-spectral-norm', 'n-body', 'n-body.c', 'navier-stokes', 'pdfjs',
    'prepack', 'prettier', 'proto-raytracer', 'quicksort', 'quicksort.c',
    'react', 'regex-dna', 'regexp-2010', 'regexp-dna',
    'return-i32-const-Liftoff', 'return-i32-const-Turbofan', 'richards',
    'source-map', 'splay', 'splay-latency', 'stalls', 'stanford-crypto-aes',
    'stanford-crypto-ccm', 'stanford-crypto-pbkdf2',
    'stanford-crypto-sha256-iterative', 'string-base64', 'string-fasta',
    'string-tagcloud', 'string-unpack-code', 'string-validate-input', 'swiffy',
    'tagcloud', 'towers', 'towers.c', 'typescript', 'uglify-es', 'uglify-js',
    'wikipedia', 'zepto', 'zlib'
  ];

  // test path component 5
  const V8_MEASUREMENT1S = [
    'Add', 'And-Test', 'And-Value', 'Arithmetic', 'AsmWasm', 'AsmWasmPeak',
    'Assign', 'AsyncStacksInstrumentation', 'Babel', 'BaselineES2017',
    'BaselineNaivePromises', 'Basic1', 'BasicExport', 'BasicImport',
    'BasicNamespace', 'BigNum.mod params.curve.q', 'BigNum.mod params.n',
    'Bitwise', 'BitwiseOr', 'Box2D', 'Box2D-F32', 'Box2D-F32_max',
    'Box2D-F32_min', 'Box2D_max', 'Box2D_min', 'Call', 'CallMethod', 'CallNew',
    'Closures', 'CodeLoad', 'CodeSize', 'Comma-Test', 'Comma-Value', 'Compare',
    'Compile', 'CompileTime', 'ConstructAllTypedArrays', 'ConstructArrayLike',
    'ConstructBySameTypedArray', 'ConstructByTypedArray', 'ConstructWithBuffer',
    'Constructor', 'CopyWithin', 'Create', 'Crypto', 'Ctor',
    'Debugger.getPossibleBreakpoints', 'Debugger.paused', 'DefaultConstructor',
    'DeltaBlue', 'DoubleEvery', 'DoubleFilter', 'DoubleFind', 'DoubleFindIndex',
    'DoubleMap', 'DoubleReduce', 'DoubleReduceRight', 'DoubleSome', 'ES5',
    'ES6', 'EarleyBoyer', 'Entries', 'EntriesMegamorphic', 'Equals-Test',
    'Equals-Value', 'Exec', 'Execution', 'FFT', 'FastEvery', 'FastFilter',
    'FastFind', 'FastFindIndex', 'FastMap', 'FastModulus.NIST.P_256.residue',
    'FastModulusFFFFFF.residue', 'FastReduce', 'FastReduceRight', 'FastSome',
    'Flags', 'ForOf', 'ForOf_OneByteLong', 'ForOf_OneByteShort',
    'ForOf_TwoByteLong', 'ForOf_TwoByteShort', 'ForOf_WithSurrogatePairsLong',
    'ForOf_WithSurrogatePairsShort', 'Gameboy', 'GenericFilter', 'GenericFind',
    'GenericFindIndex', 'GenericMap', 'GetIndexWithTrap', 'GetIndexWithoutTrap',
    'GetStringWithTrap', 'GetStringWithoutTrap', 'GetSymbolWithTrap',
    'GetSymbolWithoutTrap', 'GreaterThan-Test', 'GreaterThan-Value',
    'HasInIdiom', 'HasStringWithTrap', 'HasStringWithoutTrap',
    'HasSymbolWithTrap', 'HasSymbolWithoutTrap', 'Instantiate', 'LU',
    'LargeUntagged', 'LazyCompile', 'LeafConstructors', 'Let-Standard',
    'LiftoffCompile', 'LiftoffFunctions', 'LiftoffUnsupportedFunctions', 'MC',
    'Mandreel', 'ManyClosures', 'Map-Double', 'Map-Iteration', 'Map-Iterator',
    'Map-Object', 'Map-Object-Set-Get-Large', 'Map-Smi', 'Map-String', 'Match',
    'MinMaxSpread', 'MultiLineComment', 'NaiveFilterReplacement',
    'NaiveFindIndexReplacement', 'NaiveFindReplacement', 'NaiveMapReplacement',
    'Native', 'NavierStokes', 'Object:hasOwnProperty--DEINTERN-prop',
    'Object:hasOwnProperty--INTERN-prop',
    'Object:hasOwnProperty--NE-DEINTERN-prop',
    'Object:hasOwnProperty--NE-INTERN-prop', 'Object:hasOwnProperty--NE-el',
    'Object:hasOwnProperty--el', 'Object:hasOwnProperty--el-str',
    'Object:keys()', 'Object:keys().forEach()', 'OneLineComment',
    'OneLineComments', 'OptFastEvery', 'OptFastFilter', 'OptFastFind',
    'OptFastFindIndex', 'OptFastMap', 'OptFastReduce', 'OptFastReduceRight',
    'OptFastSome', 'Or-Test', 'Or-Value', 'Parse', 'PdfJS', 'PreParse',
    'RSA encryption & decryption', 'RayTrace', 'RegExp', 'RelocSize', 'Replace',
    'ReturnArgsBabel', 'ReturnArgsNative', 'Richards', 'Run', 'Runtime',
    'Runtime.evaluate(String16Cstor)', 'SOR', 'SPARSE', 'SciMark', 'Search',
    'Set-Double', 'Set-Iteration', 'Set-Iterator', 'Set-Object', 'Set-Smi',
    'Set-String', 'SetFromArrayLike', 'SetFromDifferentType', 'SetFromSameType',
    'SetIndexWithTrap', 'SetIndexWithoutTrap', 'SetStringWithTrap',
    'SetStringWithoutTrap', 'SetSymbolWithTrap', 'SetSymbolWithoutTrap',
    'SliceNoSpecies', 'SlowExec', 'SlowFlags', 'SlowMatch', 'SlowReplace',
    'SlowSearch', 'SlowSplit', 'SlowTest', 'SmiEvery', 'SmiFilter', 'SmiFind',
    'SmiFindIndex', 'SmiJoin', 'SmiMap', 'SmiReduce', 'SmiReduceRight',
    'SmiSome', 'SmiToString', 'Sort', 'SparseSmiJoin', 'SparseSmiToString',
    'SparseStringJoin', 'SparseStringToString', 'Splay', 'SplayLatency',
    'Split', 'Spread_OneByteShort', 'Spread_TwoByteShort',
    'Spread_WithSurrogatePairsShort', 'StrictEquals-Test', 'StrictEquals-Value',
    'StringCharCodeAtConstant', 'StringCharCodeAtNonConstant', 'StringConcat',
    'StringFunctions', 'StringIndexOfConstant', 'StringIndexOfNonConstant',
    'StringJoin', 'StringToString', 'Sub', 'SubarrayNoSpecies', 'Super',
    'Tagged', 'Test', 'Total', 'TotalBaselineCodeSize',
    'TotalBaselineCompileCount', 'Try-Catch', 'Typescript', 'Untagged',
    'Validate', 'Values', 'ValuesMegamorphic', 'Var-Standard', 'WeakMap',
    'WeakMap-Constructor', 'WeakSet', 'WeakSet-Constructor', 'With', 'count',
    'duration', 'for (i < Object.keys().length)', 'for (i < array.length)',
    'for (i < length)', 'for-in', 'for-in hasOwnProperty()',
    'in--DEINTERN-prop', 'in--INTERN-prop', 'in--NE-DEINTERN-prop',
    'in--NE-INTERN-prop', 'in--NE-el', 'in--el', 'in--el-str',
    'modMultiply with Montgomery', 'modMultiply with residue',
  ];

  const V8_MEASUREMENTS = [];
  for (const m0 of V8_MEASUREMENT0S) {
    for (const m1 of V8_MEASUREMENT1S) {
      V8_MEASUREMENTS.push(m0 + ':' + m1);
    }
  }

  function dummyMeasurements(testSuites) {
    const measurements = ['benchmark_duration'];
    if (testSuites.filter(s => s.indexOf('v8') === 0).length) {
      for (const m of V8_MEASUREMENTS) {
        measurements.push(m);
      }
    }
    if (testSuites.filter(
        s => s.indexOf('system_health.memory') === 0).length) {
      measurements.push.apply(measurements, [
      ]);
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

  const V8_TEST_CASE0S = [
    'LongString:StringConcat-10', 'LongString:StringConcat-2',
    'LongString:StringConcat-3', 'LongString:StringConcat-5', 'Number:Add',
    'Number:And', 'Number:Decrement', 'Number:Div', 'Number:Equals-False',
    'Number:Equals-True', 'Number:Increment', 'Number:Mod', 'Number:Mul',
    'Number:Oddball-Add', 'Number:Oddball-Div', 'Number:Oddball-Mod',
    'Number:Oddball-Mul', 'Number:Oddball-Sub', 'Number:Or',
    'Number:RelationalCompare', 'Number:ShiftLeft', 'Number:ShiftRight',
    'Number:ShiftRightLogical', 'Number:StrictEquals-False',
    'Number:StrictEquals-True', 'Number:String-Add', 'Number:Sub', 'Number:Xor',
    'NumberString-StringConcat-10', 'NumberString-StringConcat-2',
    'NumberString-StringConcat-3', 'NumberString-StringConcat-5', 'Object:Add',
    'Object:Div', 'Object:Mod', 'Object:Mul', 'Object:Sub', 'ObjectNull-Equals',
    'ShortString:StringConcat-10', 'ShortString:StringConcat-2',
    'ShortString:StringConcat-3', 'ShortString:StringConcat-5', 'Smi:Add',
    'Smi:And', 'Smi:Constant-Add', 'Smi:Constant-And', 'Smi:Constant-Div',
    'Smi:Constant-Mod', 'Smi:Constant-Mul', 'Smi:Constant-Or',
    'Smi:Constant-ShiftLeft', 'Smi:Constant-ShiftRight',
    'Smi:Constant-ShiftRightLogical', 'Smi:Constant-Sub', 'Smi:Constant-Xor',
    'Smi:Decrement', 'Smi:Div', 'Smi:Equals-False', 'Smi:Equals-True',
    'Smi:Increment', 'Smi:Mod', 'Smi:Mul', 'Smi:Or', 'Smi:RelationalCompare',
    'Smi:ShiftLeft', 'Smi:ShiftRight', 'Smi:ShiftRightLogical',
    'Smi:StrictEquals-False', 'Smi:StrictEquals-True', 'Smi:Sub', 'Smi:Xor',
    'SmiString:Equals', 'SmiString:RelationalCompare', 'SmiString:StrictEquals',
    'String:Add', 'String:Equals-False', 'String:Equals-True',
    'String:RelationalCompare', 'String:StrictEquals-False',
    'String:StrictEquals-True', 'Total', 'adwords.google.com', 'baidu.com',
    'bcc.co.uk-amp', 'bing.com', 'cnn.com', 'discourse.org', 'ebay.fr',
    'facebook.com', 'google.de', 'inbox.google.com', 'instagram.com',
    'linkedin.com', 'maps.google.co.jp', 'msn.com', 'pinterest.com', 'qq.com',
    'reddit.com', 'reddit.musicplayer.io', 'sina.com.cn', 'speedometer-angular',
    'speedometer-backbone', 'speedometer-ember', 'speedometer-jquery',
    'speedometer-vanilla', 'taobao.com', 'twitter.com', 'weibo.com',
    'wikipedia.org', 'wikipedia.org-visual-editor', 'wikiwand.com',
    'yahoo.co.jp', 'yandex.ru', 'youtube.com', 'youtube.com-polymer-watch',
  ];

  const V8_TEST_CASE1S = ['Default', 'Future'];

  function dummyTestCases(testSuites) {
    const testCases = [];
    if (testSuites.filter(s => s.indexOf('v8') === 0).length) {
      for (const case0 of V8_TEST_CASE0S) {
        for (const case1 of V8_TEST_CASE1S) {
          testCases.push(case0 + ':' + case1);
        }
      }
    }
    if (testSuites.filter(s => s.indexOf('system_health') === 0).length) {
      testCases.push.apply(testCases, [
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
    return testCases;
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

  const SYSTEM_HEALTH_TEST_SUITES = [
    'system_health.common_desktop',
    'system_health.common_mobile',
    'system_health.memory_desktop',
    'system_health.memory_mobile',
  ];

  // These are test path components 2:3.
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
