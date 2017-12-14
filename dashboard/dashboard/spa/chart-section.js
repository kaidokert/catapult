/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  const TEST_PATH_COMPONENT_QUERY_PARAMS = [
    'testSuite', 'bot', 'measurement', 'story', 'statistic',
  ];

  class ChartSection extends cp.Element {
    static get is() { return 'chart-section'; }

    static get properties() {
      return cp.sectionProperties({
        chartLayout: {type: Object},
        histograms: {type: Object},
        isLoading: {type: Boolean},
        isShowingOptions: {type: Boolean},
        minimapLayout: {type: Object},
        onlyChart: {type: Boolean},
        relatedTabs: {type: Array},
        selectedRelatedTabIndex: {type: Number},
        showHistogramsControls: {type: Boolean},
        testPathComponents: {type: Array},
        title: {type: String},
      });
    }

    async ready() {
      super.ready();
      this.scrollIntoView(true);
    }

    closeSection_() {
      this.dispatch(cp.ChromeperfApp.closeSection(this.sectionId));
    }

    onTitleKeyup_(e) {
      this.dispatch(ChartSection.setTitle(this.sectionId, e.target.value));
    }

    static setTitle(sectionId, title) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'chart-section.setTitle',
          sectionId,
          title,
        });
      };
    }

    toggleOptions_() {
      this.dispatch(ChartSection.showOptions(
          this.sectionId, !this.isShowingOptions));
    }

    static showOptions(sectionId, showOptions) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'chart-section.showOptions',
          sectionId,
          showOptions,
        });
      };
    }

    onMinimapBrush_(e) {
      this.dispatch(ChartSection.brushMinimap(
          this.sectionId, e.detail.brushIndex, e.detail.value));
    }

    onBrush_(e) {
      this.dispatch(ChartSection.brushChart(
          this.sectionId, e.detail.brushIndex, e.detail.value));
    }

    static brushMinimap(sectionId, brushIndex, value) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'chart-section.brushMinimap',
          sectionId,
          brushIndex,
          value,
        });
      };
    }

    static brushChart(sectionId, brushIndex, value) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'chart-section.brushChart',
          sectionId,
          brushIndex,
          value,
        });
      };
    }

    onDotClick_(e) {
      // TODO
    }

    onDotMouseOver_(e) {
      // TODO
    }

    onDotMouseOut_(e) {
      // TODO
    }

    toggleChartOnly_() {
      this.dispatch(ChartSection.toggleChartOnly(this.sectionId));
    }

    static toggleChartOnly(sectionId) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'chart-section.toggleChartOnly',
          sectionId,
        });
      };
    }

    static cartesianProduct(components) {
      if (components.length === 1) {
        // Recursion base case.
        return components[0].map(value => [value]);
      }
      const products = [];
      const subProducts = ChartSection.cartesianProduct(components.slice(1));
      for (const value of components[0]) {
        for (const subProduct of subProducts) {
          products.push([value].concat(subProduct));
        }
      }
      return products;
    }

    static updateLocation(sectionState) {
      return async (dispatch, getState) => {
        const components = sectionState.testPathComponents;
        if (components[0].selectedOptions.length > 1 ||
            components[1].selectedOptions.length > 1 ||
            components[2].selectedOptions.length > 1 ||
            components[3].selectedOptions.length > 1 ||
            components[4].selectedOptions.length > 1) {
          dispatch(cp.ChromeperfApp.saveSession());
          return;
        }
        if (components[0].selectedOptions.length === 0 ||
            components[1].selectedOptions.length === 0 ||
            components[2].selectedOptions.length === 0 ||
            components[4].selectedOptions.length === 0) {
          dispatch(cp.ChromeperfApp.updateRoute('', {}));
          return;
        }

        const queryParams = {};
        for (let i = 0; i < 3; ++i) {
          queryParams[TEST_PATH_COMPONENT_QUERY_PARAMS[i]] =
            components[i].selectedOptions.join(',');
        }
        if (components[3].selectedOptions.length === 1) {
          queryParams.story = components[3].selectedOptions[0];
        }
        if (components[4].selectedOptions[0] !== 'avg') {
          queryParams.statistic = components[4].selectedOptions[0];
        }

        // eslint-disable-next-line no-console
        console.log('TODO store options, onlyChart, selectedRelatedTab');

        dispatch(cp.ChromeperfApp.updateRoute('chart', queryParams));
      };
    }

    static restoreFromQueryParams(sectionId, queryParams) {
      return async (dispatch, getState) => {
        const components =
          getState().sectionsById[sectionId].testPathComponents;
        for (let i = 0; i < TEST_PATH_COMPONENT_QUERY_PARAMS.length; ++i) {
          const param = TEST_PATH_COMPONENT_QUERY_PARAMS[i];
          if (queryParams[param]) {
            const selectedOptions = queryParams[param].split(',');
            if (!tr.b.setsEqual(new Set(selectedOptions),
                new Set(components[i].selectedOptions))) {
              dispatch(cp.TestPathComponent.select(
                  sectionId, i, selectedOptions));
            }
          }
        }
      };
    }

    static maybeLoadTimeseries(sectionId) {
      return async (dispatch, getState) => {
        // If the first 3 components are filled, then load the timeseries.
        const state = getState();
        const section = state.sectionsById[sectionId];
        const components = section.testPathComponents;
        if (components[0].selectedOptions.length &&
            components[1].selectedOptions.length &&
            components[2].selectedOptions.length &&
            components[4].selectedOptions.length) {
          dispatch(ChartSection.loadTimeseries(sectionId));
        } else {
          dispatch(ChartSection.clearTimeseries(sectionId));
        }
        dispatch(cp.ChromeperfApp.updateLocation());
      };
    }

    static clearTimeseries(sectionId) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'chart-section.clearTimeseries',
          sectionId,
        });
      };
    }

    static loadTimeseries(sectionId) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'chart-section.startLoadingTimeseries',
          sectionId,
        });

        const section = getState().sectionsById[sectionId];
        const selectedTestPathComponents =
          section.testPathComponents.slice(0, 4).map(component => (
            component.isAggregated ?
            [component.selectedOptions] :
            component.selectedOptions));
        if (section.testPathComponents[3].selectedOptions.length === 0) {
          selectedTestPathComponents.pop();
        }
        selectedTestPathComponents.push(
            section.testPathComponents[4].selectedOptions);
        let title = section.title;
        if (!section.isTitleCustom) {
          title = selectedTestPathComponents[2].join(', ');
          title += ' on ';
          title += selectedTestPathComponents[1].join(', ');
        }
        const testPathCartesianProduct = ChartSection.cartesianProduct(
            selectedTestPathComponents);

        const fetchMark = tr.b.Timing.mark('chart-section', 'fetch');
        // TODO fetch rows and histograms from backend via cache
        await tr.b.timeout(500);
        fetchMark.end();

        // TODO use brightnessRange when > 15
        const colors = tr.b.generateFixedColorScheme(
            testPathCartesianProduct.length, {hueOffset: 0.64});

        // TODO LineChart.layout()

        const maxYAxisTickWidth = 30;
        const textHeight = 15;
        const minimapHeight = 60;
        const chartHeight = 200;

        const minimapXAxisTicks = [
          'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
          '2018', 'Feb', 'Mar', 'Apr', 'May',
        ].map((text, index, texts) => {
          return {
            text,
            x: (100 * (index + 0.5) / texts.length),
            y: minimapHeight - 5,
          };
        });

        const minimapSequences = [{
          color: '' + colors[0],
          data: [{x: 1, y: 50}],
          dotColor: '' + colors[0],
          strokeWidth: 1,
        }];
        const sequenceLength = 100;
        for (let i = 1; i < sequenceLength; i += 1) {
          const datum = {
            x: 1 + parseInt(98 * (i + 1) / sequenceLength),
            y: 1 + parseInt(98 * Math.random()),
          };
          minimapSequences[0].data.push(datum);
        }

        const chartSequences = [];
        for (const color of colors) {
          const y0 = 1 + parseInt(98 * Math.random());
          const sequence = {
            color: '' + color,
            dotColor: '' + color,
            data: [{x: 1, y: y0}],
            strokeWidth: 1,
          };
          chartSequences.push(sequence);
          for (let i = 1; i < sequenceLength; i += 1) {
            const datum = {
              x: 1 + parseInt(98 * (i + 1) / sequenceLength),
              y: 1 + parseInt(98 * Math.random()),
            };
            sequence.data.push(datum);
          }
        }

        const chartXAxisTicks = [
          'Dec', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13',
          '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24',
          '25', '26', '27', '28', '29', '30', '31', '2018', '2', '3',
        ].map((text, index, texts) => {
          return {
            text,
            x: (100 * (index + 0.5) / texts.length),
            y: chartHeight - 5,
          };
        });

        const chartYAxisTicks = [
          '9MB', '8MB', '7MB', '6MB', '5MB', '4MB', '3MB', '2MB', '1MB',
        ].map((text, index, texts) => {
          return {
            text,
            x: 0,
            y: 20 + (chartHeight - textHeight - 20) * index / texts.length,
          };
        });

        const histograms = new tr.v.HistogramSet();
        for (let i = 0; i < testPathCartesianProduct.length; ++i) {
          const testPath = testPathCartesianProduct[i];
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
                    new tr.v.d.GenericSet([tr.b.formatDate(new Date())]),
                  ],
                  [
                    tr.v.d.RESERVED_NAMES.NAME_COLORS,
                    new tr.v.d.GenericSet([colors[i].toString()]),
                  ],
                ]),
              });
        }

        dispatch({
          type: 'chart-section.layoutChart',
          sectionId,
          title,

          minimapLayout: {
            height: minimapHeight,
            yAxisWidth: maxYAxisTickWidth,
            xAxisHeight: textHeight,
            graphHeight: minimapHeight - textHeight - 15,
            dotRadius: 0,
            dotCursor: '',
            sequences: minimapSequences,
            xAxisTicks: minimapXAxisTicks,
            showXAxisTickLines: true,
            fhowYAxisTickLines: false,
            brushes: [60, 90],
          },

          chartLayout: {
            height: chartHeight,
            yAxisWidth: maxYAxisTickWidth,
            xAxisHeight: textHeight,
            graphHeight: chartHeight - textHeight - 15,
            dotRadius: 6,
            dotCursor: 'pointer',
            showYAxisTickLines: true,
            showXAxisTickLines: true,
            sequences: chartSequences,
            yAxisTicks: chartYAxisTicks,
            xAxisTicks: chartXAxisTicks,
            brushes: [95, 100],
          },

          histograms,
        });

        // TODO fetch RelatedNameMaps

        dispatch({
          type: 'chart-section.layoutRelatedTabs',
          sectionId,

          relatedTabs: [
            {
              name: 'Processes',
              sparklines: [
                {
                  name: 'browser process',
                  layout: {
                    height: 100,
                    yAxisWidth: 0,
                    xAxisHeight: 0,
                    graphHeight: 100 - 15,
                    dotRadius: 0,
                    dotCursor: 'pointer',
                    showYAxisTickLines: false,
                    showXAxisTickLines: false,
                    sequences: chartSequences,
                    yAxisTicks: [],
                    xAxisTicks: [],
                    brushes: [],
                  },
                },
                {
                  name: 'gpu process',
                  layout: {
                    height: 100,
                    yAxisWidth: 0,
                    xAxisHeight: 0,
                    graphHeight: 100 - 15,
                    dotRadius: 0,
                    dotCursor: 'pointer',
                    showYAxisTickLines: false,
                    showXAxisTickLines: false,
                    sequences: chartSequences,
                    yAxisTicks: [],
                    xAxisTicks: [],
                    brushes: [],
                  },
                },
                {
                  name: 'renderer processes',
                  layout: {
                    height: 100,
                    yAxisWidth: 0,
                    xAxisHeight: 0,
                    graphHeight: 100 - 15,
                    dotRadius: 0,
                    dotCursor: 'pointer',
                    showYAxisTickLines: false,
                    showXAxisTickLines: false,
                    sequences: chartSequences,
                    yAxisTicks: [],
                    xAxisTicks: [],
                    brushes: [],
                  },
                },
              ],
            },
            {
              name: 'Components',
              sparklines: [
                {
                  name: 'browser process',
                  layout: {
                    height: 100,
                    yAxisWidth: 0,
                    xAxisHeight: 0,
                    graphHeight: 100 - 15,
                    dotRadius: 0,
                    dotCursor: 'pointer',
                    showYAxisTickLines: false,
                    showXAxisTickLines: false,
                    sequences: chartSequences,
                    yAxisTicks: [],
                    xAxisTicks: [],
                    brushes: [],
                  },
                },
                {
                  name: 'gpu process',
                  layout: {
                    height: 100,
                    yAxisWidth: 0,
                    xAxisHeight: 0,
                    graphHeight: 100 - 15,
                    dotRadius: 0,
                    dotCursor: 'pointer',
                    showYAxisTickLines: false,
                    showXAxisTickLines: false,
                    sequences: chartSequences,
                    yAxisTicks: [],
                    xAxisTicks: [],
                    brushes: [],
                  },
                },
                {
                  name: 'renderer processes',
                  layout: {
                    height: 100,
                    yAxisWidth: 0,
                    xAxisHeight: 0,
                    graphHeight: 100 - 15,
                    dotRadius: 0,
                    dotCursor: 'pointer',
                    showYAxisTickLines: false,
                    showXAxisTickLines: false,
                    sequences: chartSequences,
                    yAxisTicks: [],
                    xAxisTicks: [],
                    brushes: [],
                  },
                },
              ],
            },
          ],
        });
      };
    }

    onSelectRelatedTab_(e) {
      this.dispatch(ChartSection.selectRelatedTab(
          this.sectionId, e.target.selected));
    }

    static selectRelatedTab(sectionId, selectedRelatedTabIndex) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'chart-section.selectRelatedTab',
          sectionId,
          selectedRelatedTabIndex,
        });
      };
    }

    onSparklineTap_(e) {
      // TODO
    }

    static clearAllFocused(sectionState) {
      return {
        ...sectionState,
        testPathComponents: sectionState.testPathComponents.map(component => {
          return {...component, isFocused: false};
        }),
      };
    }

    static groupNames(names) {
      const options = [];
      for (const name of names) {
        const parts = name.split(':');
        let parent = options;
        for (let i = 0; i < parts.length; ++i) {
          const part = parts[i];
          let found = false;
          for (const option of parent) {
            if (option.label === part) {
              if (i === parts.length - 1) {
                option.children.push({
                  label: part,
                  value: name,
                });
              } else {
                parent = option.children;
              }
              found = true;
              break;
            }
          }
          if (!found) {
            if (i === parts.length - 1) {
              parent.push({
                label: part,
                value: name,
              });
            } else {
              const option = {
                children: [],
                isExpanded: false,
                label: part,
                value: parts.slice(0, i + 1).join(':'),
              };
              parent.push(option);
              parent = option.children;
            }
          }
        }
      }
      return options;
    }
  }
  customElements.define(ChartSection.is, ChartSection);

  ChartSection.NEW_STATE = {
    isLoading: false,
    onlyChart: false,
    title: '',
    isTitleCustom: false,
    chartLayout: false,
    minimapLayout: false,
    histograms: undefined,
    showHistogramsControls: false,
    relatedTabs: [],
    selectedRelatedTabIndex: -1,
    testPathComponents: [
      {
        placeholder: 'Test suite (100)',
        canAggregate: true,
        isFocused: true,
        inputValue: '',
        selectedOptions: [],
        multipleSelectedOptions: false,
        options: [
          'system_health.common_desktop',
          'system_health.common_mobile',
          'system_health.memory_desktop',
          'system_health.memory_mobile',
          {
            label: 'v8',
            isExpanded: false,
            children: [
              {label: 'AreWeFastYet', value: 'v8:AreWeFastYet'},
              {label: 'Compile', value: 'v8:Compile'},
              {label: 'Embenchen', value: 'v8:Embenchen'},
              {label: 'RuntimeStats', value: 'v8:RuntimeStats'},
            ],
          },
        ],
      },
      {
        placeholder: 'Bot (88)',
        canAggregate: true,
        isFocused: false,
        inputValue: '',
        selectedOptions: [],
        multipleSelectedOptions: false,
        options: [
          {
            label: 'ChromiumPerf',
            isExpanded: true,
            children: [
              'android-nexus5',
              'android-nexus5X',
              'android-nexus6',
              'android-nexus7v2',
              'android-one',
              'android-webview-nexus5X',
              'android-webview-nexus6',
              'chromium-rel-mac-retina',
              'chromium-rel-mac11',
              'chromium-rel-mac11-air',
              'chromium-rel-mac11-pro',
              'chromium-rel-mac12',
              'chromium-rel-mac12-mini-8gb',
              'chromium-rel-win10',
              'chromium-rel-win7-dual',
              'chromium-rel-win7-gpu-ati',
              'chromium-rel-win7-gpu-intel',
              'chromium-rel-win7-gpu-nvidia',
              'chromium-rel-win7-x64-dual',
              'chromium-rel-win8-dual',
              'linux-release',
              'win-high-dpi',
            ],
          },
          {
            label: 'internal.client.v8',
            isExpanded: true,
            children: [
              'Nexus5',
              'Nexus7',
              'Volantis',
              'ia32',
              'x64',
            ],
          },
        ],
      },
      {
        placeholder: 'Measurement (500)',
        canAggregate: false,
        isFocused: false,
        inputValue: '',
        selectedOptions: [],
        multipleSelectedOptions: false,
        options: ChartSection.groupNames([
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
        ]),
      },
      {
        placeholder: 'Stories (53)',
        canAggregate: true,
        isFocused: false,
        inputValue: '',
        selectedOptions: [],
        multipleSelectedOptions: false,
        tagOptions: ChartSection.groupNames([
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
        ]),
        options: [
          {
            label: 'All 53 stories',
            isExpanded: true,
            value: '*',
            children: ChartSection.groupNames([
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
            ]),
          },
        ],
      },
      {
        placeholder: 'Statistics',
        canAggregate: false,
        inputValue: 'avg',
        selectedOptions: ['avg'],
        multipleSelectedOptions: false,
        isFocused: false,
        options: [
          'avg',
          'std',
          'median',
          '90%',
          '95%',
          '99%',
        ],
      },
    ],
  };

  cp.sectionReducer('chart-section.showOptions', (state, action, section) => {
    return {
      isShowingOptions: action.showOptions,
    };
  });

  cp.sectionReducer('chart-section.setTitle', (state, action, section) => {
    return {
      title: action.title,
      isTitleCustom: true,
    };
  });

  cp.sectionReducer('chart-section.selectRelatedTab',
      (state, action, section) => {
        return {
          selectedRelatedTabIndex: action.selectedRelatedTabIndex,
        };
      });

  cp.sectionReducer('chart-section.layoutChart', (state, action, section) => {
    return {
      isLoading: false,
      title: action.title,
      minimapLayout: action.minimapLayout,
      chartLayout: action.chartLayout,
      histograms: action.histograms,
    };
  });

  cp.sectionReducer('chart-section.toggleChartOnly',
      (state, action, section) => {
        return {
          onlyChart: !section.onlyChart,
        };
      });

  cp.sectionReducer('chart-section.clearTimeseries',
      (state, action, section) => {
        return {
          chartLayout: false,
          minimapLayout: false,
          histograms: undefined,
          relatedTabs: [],
        };
      });

  cp.sectionReducer('chart-section.startLoadingTimeseries',
      (state, action, section) => {
        return {
          isLoading: true,
        };
      });

  cp.sectionReducer('chart-section.layoutRelatedTabs',
      (state, action, section) => {
        return {relatedTabs: action.relatedTabs};
      });

  cp.sectionReducer('chart-section.brushChart', (state, action, section) => {
    let brushes = section.chartLayout.brushes;
    brushes = brushes.slice(0, action.brushIndex).concat([action.value
    ]).concat(brushes.slice(action.brushIndex + 1));
    return {chartLayout: {...section.chartLayout, brushes}};
  });

  cp.sectionReducer('chart-section.brushMinimap', (state, action, section) => {
    let brushes = section.minimapLayout.brushes;
    brushes = brushes.slice(0, action.brushIndex).concat([action.value
    ]).concat(brushes.slice(action.brushIndex + 1));
    return {minimapLayout: {...section.minimapLayout, brushes}};
  });

  return {
    ChartSection,
  };
});
