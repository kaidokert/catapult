/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  const TEST_PATH_COMPONENT_QUERY_PARAMS = [
    'testSuite', 'bot', 'measurement', 'story', 'statistic',
  ];

  class ChartSection extends cp.ElementBase {
    static get is() { return 'chart-section'; }

    static get properties() {
      return cp.ElementBase.statePathProperties('statePath', {
        chartLayout: {type: Object},
        histograms: {type: Object},
        isLoading: {type: Boolean},
        isShowingOptions: {type: Boolean},
        legend: {type: Array},
        minimapLayout: {type: Object},
        onlyChart: {type: Boolean},
        relatedTabs: {type: Array},
        sectionId: {type: String},
        selectedRelatedTabIndex: {type: Number},
        showHistogramsControls: {type: Boolean},
        testPathComponents: {
          type: Array,
        },
        title: {type: String},
      });
    }

    ready() {
      super.ready();
      this.scrollIntoView(true);
    }

    showLegend_(onlyChart, legend, histograms) {
      return !onlyChart && !this._empty(legend) && this._empty(histograms);
    }

    closeSection_() {
      this.dispatch(cp.ChromeperfApp.actions.closeSection(this.statePath));
    }

    onTitleKeyup_(e) {
      this.dispatch('setTitle', this.statePath, e.target.value);
    }

    toggleOptions_() {
      this.dispatch('showOptions', this.statePath, !this.isShowingOptions);
    }

    onMinimapBrush_(e) {
      this.dispatch('brushMinimap',
          this.statePath, e.detail.brushIndex, e.detail.value);
    }

    onBrush_(e) {
      this.dispatch('brushChart',
          this.statePath, e.detail.brushIndex, e.detail.value);
    }

    onChartClick_(e) {
      this.dispatch('chartClick', this.statePath);
    }

    onDotClick_(e) {
      this.dispatch('dotClick',
          this.statePath,
          e.detail.ctrlKey,
          e.detail.lineIndex,
          e.detail.datumIndex);
    }

    onDotMouseOver_(e) {
      this.dispatch('dotMouseOver', this.statePath, e.detail.lineIndex);
    }

    onDotMouseOut_(e) {
      this.dispatch('dotMouseOut', this.statePath, e.detail.lineIndex);
    }

    onLegendMouseOver_(e) {
      this.dispatch('legendMouseOver', this.statePath, e.detail.testPath);
    }

    onLegendMouseOut_(e) {
      this.dispatch('legendMouseOut', this.statePath, e.detail.testPath);
    }

    toggleChartOnly_() {
      this.dispatch('toggleChartOnly', this.statePath);
    }

    onSelectRelatedTab_(e) {
      this.dispatch('selectRelatedTab', this.statePath, e.target.selected);
    }

    onSparklineTap_(e) {
      // eslint-disable-next-line no-console
      console.log('TODO promote sparkline to chart');
    }

    static clearAllFocused(sectionState) {
      return {
        ...sectionState,
        testPathComponents: sectionState.testPathComponents.map(component => {
          return {...component, isFocused: false};
        }),
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

    static buildLegend(components, testPathCartesianProduct, colors) {
      const items = [];
      if (testPathCartesianProduct.length < 2) return items;
      const colorMap = new Map();
      for (let i = 0; i < colors.length; ++i) {
        colorMap.set(JSON.stringify(testPathCartesianProduct[i]), colors[i]);
      }
      return ChartSection.buildLegendInternal_([], components, colorMap);
    }

    static buildLegendInternal_(prefix, components, colorMap) {
      if (components.length === 1) {
        // Recursion base case.

        if (components[0].length === 1) {
          const testPath = prefix.concat([components[0][0]]);
          return [{
            label: components[0][0],
            testPath,
            color: colorMap.get(JSON.stringify(testPath)),
          }];
        }

        const items = [];
        for (const label of components[0]) {
          const testPath = prefix.concat([label]);
          items.push({
            label,
            testPath,
            color: colorMap.get(JSON.stringify(testPath)),
          });
        }
        return items;
      }

      if (components[0].length === 1) {
        // Skip this grouping level.
        return ChartSection.buildLegendInternal_(
            prefix.concat([components[0][0]]), components.slice(1), colorMap);
      }

      // Recursive case.
      const items = [];
      components[0].sort((a, b) => a.localeCompare(b));
      for (const label of components[0]) {
        const children = ChartSection.buildLegendInternal_(
            prefix.concat([label]), components.slice(1), colorMap);
        if (children.length === 1) {
          items.push({
            label,
            testPath: children[0].testPath,
            color: children[0].color,
          });
          continue;
        }
        items.push({label, children});
      }
      return items;
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

    static testPathEqual(a, b) {
      if (a.length !== b.length) return false;
      for (let i = 0; i < a.length; ++i) {
        if (a[i] !== b[i]) return false;
      }
      return true;
    }
  }

  ChartSection.actions = {
    setTitle: (statePath, title) => async (dispatch, getState) => {
      dispatch({
        type: 'element-base.setStateAtPath',
        statePath,
        delta: {title, isTitleCustom: true},
      });
    },

    showOptions: (statePath, isShowingOptions) =>
      async (dispatch, getState) => {
        dispatch({
          type: 'element-base.setStateAtPath',
          statePath,
          delta: {isShowingOptions},
        });
      },

    brushMinimap: (statePath, brushIndex, value) =>
      async (dispatch, getState) => {
        dispatch({
          type: 'chart-section.brushMinimap',
          statePath,
          brushIndex,
          value,
        });
      },

    brushChart: (statePath, brushIndex, value) =>
      async (dispatch, getState) => {
        dispatch({
          type: 'chart-section.brushChart',
          statePath,
          brushIndex,
          value,
        });
      },

    restoreFromQueryParams: (statePath, queryParams) =>
      async (dispatch, getState) => {
        const section = cp.ElementBase.getStateAtPath(
            getState(), statePath).testPathComponents;
        for (let i = 0; i < TEST_PATH_COMPONENT_QUERY_PARAMS.length; ++i) {
          const param = TEST_PATH_COMPONENT_QUERY_PARAMS[i];
          if (queryParams[param]) {
            const selectedOptions = queryParams[param].split(',');
            if (!tr.b.setsEqual(new Set(selectedOptions),
                new Set(components[i].selectedOptions))) {
              dispatch(cp.TestPathComponent.actions.select(
                  statePath, i, selectedOptions));
            }
          }
        }
      },

    maybeLoadTimeseries: statePath => async (dispatch, getState) => {
      // If the first 3 components are filled, then load the timeseries.
      const section = cp.ElementBase.getStateAtPath(getState(), statePath);
      const components = section.testPathComponents;
      if (components[0].selectedOptions.length &&
          components[1].selectedOptions.length &&
          components[2].selectedOptions.length &&
          components[4].selectedOptions.length) {
        dispatch(ChartSection.actions.loadTimeseries(statePath));
      } else {
        dispatch(ChartSection.actions.clearTimeseries(statePath));
      }
      dispatch(cp.ChromeperfApp.actions.updateLocation());
    },

    clearTimeseries: statePath => async (dispatch, getState) => {
      dispatch({
        type: 'chart-section.clearTimeseries',
        statePath,
      });
    },

    toggleChartOnly: statePath => async (dispatch, getState) => {
      dispatch({
        type: 'chart-section.toggleChartOnly',
        statePath,
      });
    },

    updateLocation: sectionState => async (dispatch, getState) => {
      const components = sectionState.testPathComponents;
      if (components[0].selectedOptions.length > 1 ||
          components[1].selectedOptions.length > 1 ||
          components[2].selectedOptions.length > 1 ||
          components[3].selectedOptions.length > 1 ||
          components[4].selectedOptions.length > 1) {
        dispatch(cp.ChromeperfApp.actions.saveSession());
        return;
      }
      if (components[0].selectedOptions.length === 0 ||
          components[1].selectedOptions.length === 0 ||
          components[2].selectedOptions.length === 0 ||
          components[4].selectedOptions.length === 0) {
        dispatch(cp.ChromeperfApp.actions.updateRoute('', {}));
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

      dispatch(cp.ChromeperfApp.actions.updateRoute('chart', queryParams));
    },

    loadTimeseries: statePath => async (dispatch, getState) => {
      dispatch({
        type: 'chart-section.startLoadingTimeseries',
        statePath,
      });

      const section = cp.ElementBase.getStateAtPath(getState(), statePath);
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
      // eslint-disable-next-line no-console
      console.log('TODO fetch Rows from backend via cache');
      await tr.b.timeout(500);
      fetchMark.end();

      let brightnessRange;
      if (testPathCartesianProduct.length > 15) {
        // eslint-disable-next-line no-console
        console.log('TODO brightnessRange');
      }
      const colors = tr.b.generateFixedColorScheme(
          testPathCartesianProduct.length, {hueOffset: 0.64});

      // eslint-disable-next-line no-console
      console.log('TODO refactor to call cp.LineChart.layout()');

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

      const minimapLines = [{
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
        minimapLines[0].data.push(datum);
      }

      const chartLines = [];
      for (let tpi = 0; tpi < colors.length; ++tpi) {
        const testPath = testPathCartesianProduct[tpi];
        const color = colors[tpi];
        const y0 = 1 + parseInt(98 * Math.random());
        const sequence = {
          color: '' + color,
          testPath,
          dotColor: '' + color,
          data: [{x: 1, y: y0}],
          strokeWidth: 1,
        };
        chartLines.push(sequence);
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

      const minimapBrushes = [60, 90];
      const chartBrushes = [];

      // eslint-disable-next-line no-console
      console.log('TODO pass innerHeight - rect.height to histograms');

      let legend = [];
      if (chartBrushes.length === 0) {
        // TODO move this into the layoutChart reducer
        legend = ChartSection.buildLegend(
            selectedTestPathComponents, testPathCartesianProduct, colors);
      }

      dispatch({
        type: 'chart-section.layoutChart',
        statePath,
        title,
        legend,

        minimapLayout: {
          height: minimapHeight,
          yAxisWidth: maxYAxisTickWidth,
          xAxisHeight: textHeight,
          graphHeight: minimapHeight - textHeight - 15,
          dotRadius: 0,
          dotCursor: '',
          lines: minimapLines,
          xAxisTicks: minimapXAxisTicks,
          showXAxisTickLines: true,
          fhowYAxisTickLines: false,
          brushes: minimapBrushes,
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
          lines: chartLines,
          yAxisTicks: chartYAxisTicks,
          xAxisTicks: chartXAxisTicks,
          brushes: chartBrushes,
        },
      });

      // eslint-disable-next-line no-console
      console.log('TODO fetch RelatedNameMaps via cache');
      // eslint-disable-next-line no-console
      console.log('TODO build tabs of related sparklines');

      dispatch({
        type: 'chart-section.layoutRelatedTabs',
        statePath,

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
                  lines: chartLines,
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
                  lines: chartLines,
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
                  lines: chartLines,
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
                  lines: chartLines,
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
                  lines: chartLines,
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
                  lines: chartLines,
                  yAxisTicks: [],
                  xAxisTicks: [],
                  brushes: [],
                },
              },
            ],
          },
        ],
      });
    },

    selectRelatedTab: (statePath, selectedRelatedTabIndex) =>
      async (dispatch, getState) => {
        dispatch({
          type: 'element-base.setStateAtPath',
          statePath,
          delta: {selectedRelatedTabIndex},
        });
      },

    chartClick: statePath => async (dispatch, getState) => {
      dispatch({
        type: 'chart-section.chartClick',
        statePath,
      });
    },

    dotClick: (statePath, ctrlKey, lineIndex, datumIndex) =>
      async (dispatch, getState) => {
        dispatch({
          type: 'chart-section.dotClick',
          statePath,
          ctrlKey,
          lineIndex,
          datumIndex,
        });

        dispatch({
          type: 'chart-section.startLoadingTimeseries',
          statePath,
        });

        const section = cp.ElementBase.getStateAtPath(getState(), statePath);

        dispatch({
          type: 'chart-section.receiveHistograms',
          statePath,
          histograms: await cp.dummyHistograms(section),
        });
      },

    dotMouseOver: (statePath, lineIndex) => async (dispatch, getState) => {
      statePath = statePath.concat(['chartLayout', 'lines']);
      const lines = cp.ElementBase.getStateAtPath(getState(), statePath);
      if (lines.length < 2) return;
      dispatch({
        type: 'chart-section.dotMouseOver',
        statePath,
        lineIndex,
      });
    },

    dotMouseOut: (statePath, lineIndex) => async (dispatch, getState) => {
      statePath = statePath.concat(['chartLayout', 'lines', lineIndex]);
      dispatch({
        type: 'element-base.setStateAtPath',
        statePath,
        delta: {strokeWidth: 1},
      });
    },

    legendMouseOver: (statePath, testPath) => async (dispatch, getState) => {
      const section = cp.ElementBase.getStateAtPath(getState(), statePath);
      for (let i = 0; i < section.chartLayout.lines.length; ++i) {
        if (!ChartSection.testPathEqual(
            section.chartLayout.lines[i].testPath, testPath)) {
          continue;
        }
        dispatch(ChartSection.actions.dotMouseOver(statePath, i));
      }
    },

    legendMouseOut: (statePath, testPath) => async (dispatch, getState) => {
      const section = cp.ElementBase.getStateAtPath(getState(), statePath);
      for (let i = 0; i < section.chartLayout.lines.length; ++i) {
        if (!ChartSection.testPathEqual(
            section.chartLayout.lines[i].testPath, testPath)) {
          continue;
        }
        dispatch(ChartSection.actions.dotMouseOut(statePath, i));
      }
    },
  };

  ChartSection.reducers = {
    receiveHistograms: cp.ElementBase.updatingReducer((section, action) => {
      return {
        isLoading: false,
        histograms: action.histograms,
      };
    }),

    chartClick: cp.ElementBase.updatingReducer((section, action) => {
      return {
        chartLayout: {
          ...section.chartLayout,
          brushes: [],
        },
        histograms: undefined,
      };
    }),

    dotClick: cp.ElementBase.updatingReducer((section, action) => {
      const sequence = section.chartLayout.lines[action.lineIndex];
      const datumX = sequence.data[action.datumIndex].x;
      let prevX = 0;
      if (action.datumIndex > 0) prevX = sequence.data[action.datumIndex - 1].x;
      let nextX = 100;
      if (action.datumIndex < sequence.data.length - 1) {
        nextX = sequence.data[action.datumIndex + 1].x;
      }
      const brushes = [0.5 * (datumX + prevX), 0.5 * (datumX + nextX)];
      if (action.ctrlKey) {
        brushes.push.apply(brushes, section.chartLayout.brushes);
      }
      return {
        chartLayout: {
          ...section.chartLayout,
          brushes,
        },
      };
    }),

    dotMouseOver: cp.ElementBase.updatingReducer((lines, action) => {
      // Set its strokeWidth:2
      const line = lines[lineIndex];
      lines = Array.from(lines);
      lines.splice(lineIndex, 1, {
        ...line,
        strokeWidth: 2,
      });
      if (action.lineIndex !== (lines.length - 1)) {
        // Move action.lineIndex to the end.
        [lines[action.lineIndex], lines[lines.length - 1]] =
          [lines[lines.length - 1], lines[action.lineIndex]];
      }
      return lines;
    }),

    layoutChart: cp.ElementBase.updatingReducer((section, action) => {
      return {
        isLoading: false,
        title: action.title,
        minimapLayout: action.minimapLayout,
        chartLayout: action.chartLayout,
        histograms: action.histograms,
        legend: action.legend,
      };
    }),

    toggleChartOnly: cp.ElementBase.updatingReducer((section, action) => {
      return {onlyChart: !section.onlyChart};
    }),

    clearTimeseries: cp.ElementBase.updatingReducer((section, action) => {
      return {
        chartLayout: false,
        minimapLayout: false,
        histograms: undefined,
        relatedTabs: [],
      };
    }),

    startLoadingTimeseries: cp.ElementBase.updatingReducer(
        (section, action) => {
          return {isLoading: true};
        }),

    layoutRelatedTabs: cp.ElementBase.updatingReducer((section, action) => {
      return {relatedTabs: action.relatedTabs};
    }),

    brushChart: cp.ElementBase.updatingReducer((section, action) => {
      const brushes = Array.from(section.chartLayout.brushes);
      brushes.splice(action.brushIndex, 1, action.value);
      return {chartLayout: {...section.chartLayout, brushes}};
    }),

    brushMinimap: cp.ElementBase.updatingReducer((section, action) => {
      const brushes = Array.from(section.minimapLayout.brushes);
      brushes.splice(action.brushIndex, 1, action.value);
      return {minimapLayout: {...section.minimapLayout, brushes}};
    }),
  };

  // eslint-disable-next-line no-console
  console.log('TODO fetch list_tests via cache');

  ChartSection.NEW_STATE = {
    isLoading: false,
    onlyChart: false,
    title: '',
    isTitleCustom: false,
    legend: [],
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

  cp.ElementBase.register(ChartSection);

  return {
    ChartSection,
  };
});
