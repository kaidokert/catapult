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
      return {
        ...cp.ElementBase.statePathProperties('statePath', {
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
        }),
        ...cp.ElementBase.statePathProperties('sharedStatePath', {
          xCursor: {type: Number},
        }),
      };
    }

    ready() {
      super.ready();
      this.scrollIntoView(true);
    }

    connectedCallback() {
      super.connectedCallback();
      this.dispatch('connected', this.statePath);
    }

    showLegend_(onlyChart, legend, histograms) {
      return !onlyChart && !this._empty(legend) && this._empty(histograms);
    }

    closeSection_() {
      this.dispatchEvent(new CustomEvent('close-section', {
        bubbles: true,
        composed: true,
        detail: {sectionId: this.sectionId},
      }));
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

    onSelectTestPathComponent_(e) {
      e.cancelBubble = true;
      this.dispatch('selectTestPathComponent', this.statePath, e.model.index);
    }

    onAggregateTestPathComponent_(e) {
      this.dispatch('maybeLoadTimeseries', this.statePath);
    }

    onRelatedTabTap_(e) {
      e.cancelBubble = true;
      this.dispatch('selectRelatedTab', this.statePath, e.model.tabIndex);
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

    static testPathEqual(a, b) {
      if (a.length !== b.length) return false;
      for (let i = 0; i < a.length; ++i) {
        if (a[i] !== b[i]) return false;
      }
      return true;
    }
  }

  ChartSection.actions = {
    connected: statePath => async (dispatch, getState) => {
      dispatch(ChartSection.actions.focusNextComponent(statePath));
    },

    loadParameters: statePath => async (dispatch, getState) => {
      const testSuites = Polymer.Path.get(
          getState(), `${statePath}.testPathComponents.0.selectedOptions`);
      const bots = cp.dummyBots(testSuites);
      dispatch(cp.ElementBase.actions.updateObjectAtPath(
          `${statePath}.testPathComponents.1`, {
            options: cp.OptionGroup.groupValues(bots).map(option => {
              return {...option, isExpanded: true};
            }),
            placeholder: `Bots (${bots.length})`,
          }));

      const measurements = cp.dummyMeasurements(testSuites);
      dispatch(cp.ElementBase.actions.updateObjectAtPath(
          `${statePath}.testPathComponents.2`, {
            options: cp.OptionGroup.groupValues(measurements),
            placeholder: `Measurements (${measurements.length})`,
          }));

      const stories = cp.dummyStories(testSuites);
      dispatch(cp.ElementBase.actions.updateObjectAtPath(
          `${statePath}.testPathComponents.3`, {
            options: [{
              label: `All ${stories.length} test cases`,
              isExpanded: true,
              value: '*',
              options: cp.OptionGroup.groupValues(stories),
            }],
            placeholder: `Test cases (${stories.length})`,
          }));
      dispatch(cp.ElementBase.actions.updateObjectAtPath(
          `${statePath}.testPathComponents.3.tags`, {
            options: cp.OptionGroup.groupValues(
                cp.dummyStoryTags(testSuites)),
          }));
    },

    selectTestPathComponent: (statePath, index) =>
      async (dispatch, getState) => {
        if (index === 0) {
          dispatch(ChartSection.actions.loadParameters(statePath));
        }

        dispatch(ChartSection.actions.focusNextComponent(statePath));
        dispatch(ChartSection.actions.maybeLoadTimeseries(statePath));
      },

    focusNextComponent: statePath => async (dispatch, getState) => {
      // The first 3 components are required.
      // Focus the next empty required test path component.
      for (let i = 0; i < 3; ++i) {
        const componentPath = `${statePath}.testPathComponents.${i}`;
        const componentState = Polymer.Path.get(getState(), componentPath);
        if (componentState.selectedOptions.length === 0) {
          dispatch(cp.DropdownInput.actions.focus(componentPath));
          return;
        }
      }
      dispatch(cp.DropdownInput.actions.blurAll());
    },

    setTitle: (statePath, title) => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObjectAtPath(statePath, {
        title,
        isTitleCustom: true,
      }));
    },

    showOptions: (statePath, isShowingOptions) =>
      async (dispatch, getState) => {
        dispatch(cp.ElementBase.actions.updateObjectAtPath(statePath, {
          isShowingOptions,
        }));
      },

    brushMinimap: (statePath, brushIndex, value) =>
      async (dispatch, getState) => {
        dispatch(cp.ElementBase.actions.updateObjectAtPath(
            `${statePath}.minimapLayout.xBrushes.${brushIndex}`,
            {normalized: value}));
      },

    brushChart: (statePath, brushIndex, value) =>
      async (dispatch, getState) => {
        dispatch(cp.ElementBase.actions.updateObjectAtPath(
            `${statePath}.chartLayout.xBrushes.${brushIndex}`,
            {normalized: value}));
      },

    restoreFromQueryParams: (statePath, queryParams) =>
      async (dispatch, getState) => {
        const components = Polymer.Path.get(
            getState(), statePath).testPathComponents;
        for (let i = 0; i < TEST_PATH_COMPONENT_QUERY_PARAMS.length; ++i) {
          const param = TEST_PATH_COMPONENT_QUERY_PARAMS[i];
          if (queryParams[param]) {
            const selectedOptions = queryParams[param].split(',');
            if (!tr.b.setsEqual(new Set(selectedOptions),
                new Set(components[i].selectedOptions))) {
              const componentPath = `${statePath}.testPathComponents.${i}`;
              dispatch(cp.TestPathComponent.actions.select(
                  componentPath, selectedOptions));
            }
          }
        }
        dispatch(ChartSection.actions.loadParameters(statePath));
        dispatch(ChartSection.actions.focusNextComponent(statePath));
        dispatch(ChartSection.actions.maybeLoadTimeseries(statePath));
      },

    maybeLoadTimeseries: statePath => async (dispatch, getState) => {
      // If the first 3 components are filled, then load the timeseries.
      const section = Polymer.Path.get(getState(), statePath);
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
      dispatch(cp.ElementBase.actions.toggleBooleanAtPath(
          `${statePath}.onlyChart`));
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
      dispatch(cp.ElementBase.actions.updateObjectAtPath(
          statePath, {isLoading: true}));

      const section = Polymer.Path.get(getState(), statePath);
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
      console.log('TODO refactor to call cp.MultiChart.layout()');

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

      const minimapBrushes = [
        {x: 60, normalized: 60},
        {x: 90, normalized: 90},
      ];
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
          xBrushes: minimapBrushes,
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
          xBrushes: chartBrushes,
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
                  xBrushes: [],
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
                  xBrushes: [],
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
                  xBrushes: [],
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
                  xBrushes: [],
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
                  xBrushes: [],
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
                  xBrushes: [],
                },
              },
            ],
          },
        ],
      });
    },

    selectRelatedTab: (statePath, selectedRelatedTabIndex) =>
      async (dispatch, getState) => {
        const state = Polymer.Path.get(getState(), statePath);
        if (selectedRelatedTabIndex === state.selectedRelatedTabIndex) {
          selectedRelatedTabIndex = -1;
        }
        dispatch(cp.ElementBase.actions.updateObjectAtPath(statePath, {
          selectedRelatedTabIndex,
        }));
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

        dispatch(cp.ElementBase.actions.updateObjectAtPath(
            statePath, {isLoading: true}));

        const section = Polymer.Path.get(getState(), statePath);

        dispatch({
          type: 'chart-section.receiveHistograms',
          statePath,
          histograms: await cp.dummyHistograms(section),
        });
      },

    dotMouseOver: (statePath, lineIndex) => async (dispatch, getState) => {
      statePath = `${statePath}.chartLayout.lines`;
      const lines = Polymer.Path.get(getState(), statePath);
      if (lines.length < 2) return;
      dispatch({
        type: 'chart-section.dotMouseOver',
        statePath,
        lineIndex,
      });
    },

    dotMouseOut: (statePath, lineIndex) => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObjectAtPath(
          `${statePath}.chartLayout.lines.${lineIndex}`, {strokeWidth: 1}));
    },

    legendMouseOver: (statePath, testPath) => async (dispatch, getState) => {
      const section = Polymer.Path.get(getState(), statePath);
      for (let i = 0; i < section.chartLayout.lines.length; ++i) {
        if (!ChartSection.testPathEqual(
            section.chartLayout.lines[i].testPath, testPath)) {
          continue;
        }
        dispatch(ChartSection.actions.dotMouseOver(statePath, i));
      }
    },

    legendMouseOut: (statePath, testPath) => async (dispatch, getState) => {
      const section = Polymer.Path.get(getState(), statePath);
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
    receiveHistograms: cp.ElementBase.statePathReducer((state, action) => {
      return {
        ...state,
        isLoading: false,
        histograms: action.histograms,
      };
    }),

    chartClick: cp.ElementBase.statePathReducer((state, action) => {
      return {
        ...state,
        chartLayout: {
          ...state.chartLayout,
          xBrushes: [],
        },
        histograms: undefined,
      };
    }),

    dotClick: cp.ElementBase.statePathReducer((state, action) => {
      const sequence = state.chartLayout.lines[action.lineIndex];
      const datumX = sequence.data[action.datumIndex].x;
      let prevX = 0;
      if (action.datumIndex > 0) prevX = sequence.data[action.datumIndex - 1].x;
      let nextX = 100;
      if (action.datumIndex < sequence.data.length - 1) {
        nextX = sequence.data[action.datumIndex + 1].x;
      }
      const xBrushes = [
        {normalized: 0.5 * (datumX + prevX)},
        {normalized: 0.5 * (datumX + nextX)},
      ];
      if (action.ctrlKey) {
        xBrushes.push.apply(xBrushes, state.chartLayout.xBrushes);
      }
      return {
        ...state,
        chartLayout: {
          ...state.chartLayout,
          xBrushes,
        },
      };
    }),

    dotMouseOver: cp.ElementBase.statePathReducer((lines, action) => {
      lines = Array.from(lines);
      // Set its strokeWidth:2
      const line = lines[action.lineIndex];
      lines.splice(action.lineIndex, 1, {
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

    layoutChart: cp.ElementBase.statePathReducer((state, action) => {
      return {
        ...state,
        isLoading: false,
        title: action.title,
        minimapLayout: action.minimapLayout,
        chartLayout: action.chartLayout,
        histograms: action.histograms,
        legend: action.legend,
      };
    }),

    clearTimeseries: cp.ElementBase.statePathReducer((state, action) => {
      return {
        ...state,
        chartLayout: {},
        minimapLayout: {},
        histograms: undefined,
        relatedTabs: [],
      };
    }),

    layoutRelatedTabs: cp.ElementBase.statePathReducer((state, action) => {
      // TODO call MultiChart static methods
      return {...state, relatedTabs: action.relatedTabs};
    }),
  };

  ChartSection.NEW_STATE = {
    isLoading: false,
    onlyChart: false,
    title: '',
    isTitleCustom: false,
    legend: [],
    chartLayout: {},
    minimapLayout: {},
    histograms: undefined,
    showHistogramsControls: false,
    relatedTabs: [],
    selectedRelatedTabIndex: -1,
    testPathComponents: [
      {
        placeholder: 'Test suites (100)',
        canAggregate: true,
        inputValue: '',
        selectedOptions: [],
        options: [
          'system_health.common_desktop',
          'system_health.common_mobile',
          'system_health.memory_desktop',
          'system_health.memory_mobile',
          {
            label: 'v8',
            isExpanded: false,
            options: [
              {label: 'AreWeFastYet', value: 'v8:AreWeFastYet'},
              {label: 'Compile', value: 'v8:Compile'},
              {label: 'Embenchen', value: 'v8:Embenchen'},
              {label: 'RuntimeStats', value: 'v8:RuntimeStats'},
            ],
          },
        ],
      },
      {
        placeholder: 'Bots',
        canAggregate: true,
        inputValue: '',
        selectedOptions: [],
        options: [],
      },
      {
        placeholder: 'Measurements',
        canAggregate: false,
        inputValue: '',
        selectedOptions: [],
        options: [],
      },
      {
        placeholder: 'Test cases',
        canAggregate: true,
        inputValue: '',
        selectedOptions: [],
        options: [],
        tags: {
          options: [],
          selectedOptions: [],
        },
      },
      {
        placeholder: 'Statistics',
        canAggregate: false,
        inputValue: 'avg',
        selectedOptions: ['avg'],
        options: [
          'avg',
          'std',
          'count',
          'min',
          'max',
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
