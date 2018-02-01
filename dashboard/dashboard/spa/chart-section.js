/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class ChartSection extends cp.ElementBase {
    ready() {
      super.ready();
      this.scrollIntoView(true);
    }

    connectedCallback() {
      super.connectedCallback();
      this.dispatch('connected', this.statePath);
    }

    isLegendOpen_(isExpanded, legend, histograms) {
      return !isExpanded && !this._empty(legend) && this._empty(histograms);
    }

    testSuiteHref_(testSuites) {
      return 'go/chrome-speed';
    }

    onTestSuiteSelect_(event) {
      event.cancelBubble = true;
      this.dispatch('testSuite', this.statePath);
    }

    onTestSuiteAggregate_(event) {
      this.dispatch('aggregateTestSuite', this.statePath);
    }

    onMeasurementSelect_(event) {
      event.cancelBubble = true;
      this.dispatch('measurement', this.statePath);
    }

    onBotSelect_(event) {
      event.cancelBubble = true;
      this.dispatch('bot', this.statePath);
    }

    onBotAggregate_(event) {
      this.dispatch('aggregateBot', this.statePath);
    }

    onTestCaseSelect_(event) {
      event.cancelBubble = true;
      this.dispatch('testCase', this.statePath);
    }

    onTestCaseAggregate_(event) {
      this.dispatch('aggregateTestCase', this.statePath);
    }

    onStatisticSelect_(event) {
      event.cancelBubble = true;
      this.dispatch('statistic', this.statePath);
    }

    onTitleKeyup_(event) {
      this.dispatch('setTitle', this.statePath, event.target.value);
    }

    onClose_(event) {
      this.dispatchEvent(new CustomEvent('close-section', {
        bubbles: true,
        composed: true,
        detail: {sectionId: this.sectionId},
      }));
    }

    onOptionsToggle_(event) {
      this.dispatch('showOptions', this.statePath, !this.isShowingOptions);
    }

    onMinimapBrush_(event) {
      this.dispatch('brushMinimap', this.statePath,
          event.detail.brushIndex,
          event.detail.value);
    }

    onChartClick_(event) {
      this.dispatch('chartClick', this.statePath);
    }

    onDotClick_(event) {
      this.dispatch('dotClick', this.statePath,
          event.detail.ctrlKey,
          event.detail.lineIndex,
          event.detail.datumIndex);
    }

    onDotMouseOver_(event) {
      this.dispatch('dotMouseOver', this.statePath,
          event.detail.line,
          event.detail.datum);
    }

    onBrush_(event) {
      this.dispatch('brushChart', this.statePath,
          event.detail.brushIndex,
          event.detail.value);
    }

    onLegendMouseOver_(event) {
      this.dispatch('legendMouseOver', this.statePath, event.detail.testPath);
    }

    onLegendMouseOut_(event) {
      this.dispatch('legendMouseOut', this.statePath, event.detail.testPath);
    }

    onRelatedTabTap_(event) {
      event.cancelBubble = true;
      this.dispatch('selectRelatedTab', this.statePath, event.model.tabIndex);
    }

    onSparklineTap_(event) {
      this.dispatchEvent(new CustomEvent('new-section', {
        bubbles: true,
        composed: true,
        detail: {
          type: cp.ChartSection.is,
          options: {
            parameters: event.model.sparkline.chartParameters,
          },
        },
      }));
    }

    onChartChange_() {
      this.dispatch('updateLegendColors', this.statePath);
    }
  }

  ChartSection.properties = {
    ...cp.ElementBase.statePathProperties('statePath', {
      bot: {type: Object},
      chartLayout: {
        type: Object,
        observer: 'onChartChange_',
      },
      histograms: {type: Object},
      isExpanded: {type: Boolean},
      isLoading: {type: Boolean},
      isShowingOptions: {type: Boolean},
      legend: {type: Array},
      measurement: {type: Object},
      minimapLayout: {type: Object},
      relatedTabs: {type: Array},
      sectionId: {type: String},
      selectedRelatedTabIndex: {type: Number},
      showHistogramsControls: {type: Boolean},
      statistic: {type: Object},
      testCase: {type: Object},
      testSuite: {type: Object},
      title: {type: String},
    }),
    ...cp.ElementBase.statePathProperties('sharedStatePath', {
      xCursor: {type: Number},
    }),
  };

  ChartSection.actions = {
    connected: statePath => async (dispatch, getState) => {
      const state = Polymer.Path.get(getState(), statePath);

      dispatch(cp.ChartParameter.actions.updateInputValue(
          `${statePath}.testSuite`));
      dispatch(cp.ChartParameter.actions.updateInputValue(
          `${statePath}.measurement`));
      dispatch(cp.ChartParameter.actions.updateInputValue(
          `${statePath}.bot`));
      dispatch(cp.ChartParameter.actions.updateInputValue(
          `${statePath}.testCase`));
      dispatch(cp.ChartParameter.actions.updateInputValue(
          `${statePath}.statistic`));

      if (state.testSuite.selectedOptions.length) {
        dispatch(ChartSection.actions.measurementOptions(statePath));
        dispatch(ChartSection.actions.botOptions(statePath));
        dispatch(ChartSection.actions.testCaseOptions(statePath));
        if (state.measurement.selectedOptions.length === 0) {
          dispatch(cp.DropdownInput.actions.focus(`${statePath}.measurement`));
        }
      } else {
        dispatch(cp.DropdownInput.actions.focus(`${statePath}.testSuite`));
      }
      dispatch(ChartSection.actions.maybeLoadTimeseries(statePath));
    },

    testSuite: statePath => async (dispatch, getState) => {
      const state = Polymer.Path.get(getState(), statePath);
      dispatch(ChartSection.actions.measurementOptions(statePath));
      dispatch(ChartSection.actions.maybeLoadTimeseries(statePath));
      if (state.measurement.selectedOptions.length === 0) {
        dispatch(cp.DropdownInput.actions.focus(`${statePath}.measurement`));
      }

      // Bot and Test case are optional parameters, so here's an opportunity to
      // improve responsiveness by waiting for Polymer to render measurement
      // options and/or the loading spinner to give the user something to look
      // at while we load the options for the optional parameters.
      await cp.ElementBase.afterRender();
      dispatch(ChartSection.actions.botOptions(statePath));
      dispatch(ChartSection.actions.testCaseOptions(statePath));
    },

    aggregateTestSuite: statePath => async (dispatch, getState) => {
      dispatch(ChartSection.actions.maybeLoadTimeseries(statePath));
    },

    measurement: statePath => async (dispatch, getState) => {
      dispatch({
        type: ChartSection.reducers.updateTitle.typeName,
        statePath,
      });
      dispatch(ChartSection.actions.maybeLoadTimeseries(statePath));
    },

    bot: statePath => async (dispatch, getState) => {
      dispatch({
        type: ChartSection.reducers.updateTitle.typeName,
        statePath,
      });
      dispatch(ChartSection.actions.maybeLoadTimeseries(statePath));
    },

    aggregateBot: statePath => async (dispatch, getState) => {
      dispatch(ChartSection.actions.maybeLoadTimeseries(statePath));
    },

    testCase: statePath => async (dispatch, getState) => {
      dispatch({
        type: ChartSection.reducers.updateTitle.typeName,
        statePath,
      });
      dispatch(ChartSection.actions.maybeLoadTimeseries(statePath));
    },

    aggregateTestCase: statePath => async (dispatch, getState) => {
      dispatch(ChartSection.actions.maybeLoadTimeseries(statePath));
    },

    statistic: statePath => async (dispatch, getState) => {
      dispatch(ChartSection.actions.maybeLoadTimeseries(statePath));
    },

    measurementOptions: statePath => async (dispatch, getState) => {
      const state = Polymer.Path.get(getState(), statePath);
      // TODO This may need to fetch.
      dispatch({
        type: ChartSection.reducers.measurementOptions.typeName,
        statePath,
        measurements: cp.dummyMeasurements(state.testSuite.selectedOptions),
      });
    },

    botOptions: statePath => async (dispatch, getState) => {
      const state = Polymer.Path.get(getState(), statePath);
      // TODO This may need to fetch.
      dispatch({
        type: ChartSection.reducers.botOptions.typeName,
        statePath,
        bots: cp.dummyBots(state.testSuite.selectedOptions),
      });
    },

    testCaseOptions: statePath => async (dispatch, getState) => {
      const state = Polymer.Path.get(getState(), statePath);
      // TODO This may need to fetch.
      dispatch({
        type: ChartSection.reducers.testCaseOptions.typeName,
        statePath,
        testCases: cp.dummyTestCases(state.testSuite.selectedOptions),
        tags: cp.dummyStoryTags(state.testSuite.selectedOptions),
      });
    },

    setTitle: (statePath, title) => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(statePath, {
        title,
        isTitleCustom: true,
      }));
    },

    showOptions: (statePath, isShowingOptions) =>
      async (dispatch, getState) => {
        dispatch(cp.ElementBase.actions.updateObject(statePath, {
          isShowingOptions,
        }));
      },

    brushMinimap: (statePath, brushIndex, value) =>
      async (dispatch, getState) => {
        dispatch(cp.ElementBase.actions.updateObject(
            `${statePath}.minimapLayout.xBrushes.${brushIndex}`,
            {x: value + '%'}));
      },

    brushChart: (statePath, brushIndex, value) =>
      async (dispatch, getState) => {
        dispatch(cp.ElementBase.actions.updateObject(
            `${statePath}.chartLayout.xBrushes.${brushIndex}`,
            {x: value + '%'}));
      },

    maybeLoadTimeseries: statePath => async (dispatch, getState) => {
      // If the first 3 components are filled, then load the timeseries.
      const state = Polymer.Path.get(getState(), statePath);
      if (state.testSuite.selectedOptions.length &&
          state.measurement.selectedOptions.length &&
          state.statistic.selectedOptions.length) {
        dispatch(ChartSection.actions.loadTimeseries(statePath));
      } else {
        dispatch(ChartSection.actions.clearTimeseries(statePath));
      }
      dispatch(cp.ChromeperfApp.actions.updateLocation());
    },

    clearTimeseries: statePath => async (dispatch, getState) => {
      dispatch(cp.ChartTimeseries.actions.load(
          `${statePath}.minimapLayout`, []));
      dispatch(cp.ChartTimeseries.actions.load(
          `${statePath}.chartLayout`, []));
      dispatch({
        type: ChartSection.reducers.clearTimeseries.typeName,
        statePath,
      });
    },

    updateLocation: state => async (dispatch, getState) => {
      if (state.testCase.selectedOptions.length > 1) {
        dispatch(cp.ChromeperfApp.actions.saveSession());
        return;
      }
      if (state.testSuite.selectedOptions.length === 0 ||
          state.measurement.selectedOptions.length === 0 ||
          state.statistic.selectedOptions.length === 0) {
        dispatch(cp.ChromeperfApp.actions.updateRoute('', {}));
        return;
      }

      const queryParams = {
        testSuites: state.testSuite.selectedOptions.join(','),
        measurements: state.measurement.selectedOptions.join(','),
      };
      if (state.bot.selectedOptions.length) {
        queryParams.bots = state.bot.selectedOptions.join(',');
      }
      if (state.testCase.selectedOptions.length === 1) {
        queryParams.testCases = state.testCase.selectedOptions[0];
      }
      const statistics = state.statistic.selectedOptions;
      if (statistics.length > 1 || statistics[0] !== 'avg') {
        queryParams.statistics = statistics.join(',');
      }

      cp.todo('store options, isExpanded, selectedRelatedTab');

      dispatch(cp.ChromeperfApp.actions.updateRoute('chart', queryParams));
    },

    fetchTimeseries: (statePath, testSuite, measurement, bot, testCase,
      statistic) => async (dispatch, getState) => {
      },

    loadTimeseries: statePath => async (dispatch, getState) => {
      const state = Polymer.Path.get(getState(), statePath);
      const parameters = [];
      if (state.testSuite.isAggregated) {
        parameters.push([state.testSuite.selectedOptions]);
      } else {
        parameters.push(state.testSuite.selectedOptions);
      }
      parameters.push(state.measurement.selectedOptions);
      if (state.bot.isAggregated) {
        parameters.push([state.bot.selectedOptions]);
      } else {
        parameters.push(state.bot.selectedOptions);
      }
      if (state.testCase.isAggregated) {
        parameters.push([state.testCase.selectedOptions]);
      } else {
        parameters.push(state.testCase.selectedOptions);
      }
      parameters.push(state.statistic.selectedOptions);

      const parameterProducts = ChartSection.cartesianProduct(parameters);

      dispatch({
        type: ChartSection.reducers.buildLegend.typeName,
        statePath,
        parameters,
      });

      dispatch(cp.ChartTimeseries.load(`${statePath}.minimapLayout`, [
        {
          ...parameterProducts[0],
          minimap: true,
        },
      ]));

      dispatch(cp.ChartTimeseries.load(
          `${statePath}.chartLayout`, parameterProducts));

      cp.todo('minimap brushes');
      cp.todo('fetch RelatedNameMaps via cache');
      cp.todo('build tabs of related sparklines');
    },

    selectRelatedTab: (statePath, selectedRelatedTabIndex) =>
      async (dispatch, getState) => {
        const state = Polymer.Path.get(getState(), statePath);
        if (selectedRelatedTabIndex === state.selectedRelatedTabIndex) {
          selectedRelatedTabIndex = -1;
        }
        dispatch(cp.ElementBase.actions.updateObject(statePath, {
          selectedRelatedTabIndex,
        }));
      },

    chartClick: statePath => async (dispatch, getState) => {
      dispatch({
        type: ChartSection.reducers.chartClick.typeName,
        statePath,
      });
    },

    dotClick: (statePath, ctrlKey, lineIndex, datumIndex) =>
      async (dispatch, getState) => {
        dispatch({
          type: ChartSection.reducers.dotClick.typeName,
          statePath,
          ctrlKey,
          lineIndex,
          datumIndex,
        });

        dispatch(cp.ElementBase.actions.updateObject(
            statePath, {isLoading: true}));

        const section = Polymer.Path.get(getState(), statePath);

        dispatch({
          type: ChartSection.reducers.receiveHistograms.typeName,
          statePath,
          histograms: await cp.dummyHistograms(section),
        });
      },

    dotMouseOver: (statePath, line, datum) =>
      async (dispatch, getState) => {
        dispatch(cp.ChartBase.actions.tooltip(`${statePath}.chartLayout`, [
          {name: 'value', value: '9.99MB'},
          {name: 'chromium', value: '123456-234567'},
        ]));
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
        dispatch(cp.ChartBase.actions.dotMouseOut(
            statePath + '.chartLayout', i));
      }
    },

    updateLegendColors: statePath => async (dispatch, getState) => {
      cp.todo('update legend colors');
    },
  };

  ChartSection.reducers = {
    buildLegend: cp.ElementBase.statePathReducer((state, action) => {
      return {
        ...state,
        legend: ChartSection.buildLegend(action.parameters),
      };
    }),

    updateTitle: cp.ElementBase.statePathReducer((state, action) => {
      if (state.isTitleCustom) return state;
      let title = state.measurement.selectedOptions.join(', ');
      if (state.bot.selectedOptions.length > 0 &&
          state.bot.selectedOptions.length < 4) {
        title += ' on ' + state.bot.selectedOptions.join(', ');
      }
      if (state.testCase.selectedOptions.length > 0 &&
          state.testCase.selectedOptions.length < 4) {
        title += ' for ' + state.testCase.selectedOptions.join(', ');
      }
      return {
        ...state,
        title,
      };
    }),

    measurementOptions: cp.ElementBase.statePathReducer((state, action) => {
      return {
        ...state,
        measurement: {
          ...state.measurement,
          options: cp.OptionGroup.groupValues(action.measurements),
          label: `Measurements (${action.measurements.size})`,
        },
      };
    }),

    botOptions: cp.ElementBase.statePathReducer((state, action) => {
      return {
        ...state,
        bot: {
          ...state.bot,
          options: cp.OptionGroup.groupValues(action.bots).map(option => {
            return {...option, isExpanded: true};
          }),
          label: `Bots (${action.bots.size})`,
        },
      };
    }),

    testCaseOptions: cp.ElementBase.statePathReducer((state, action) => {
      return {
        ...state,
        testCase: {
          ...state.testCase,
          options: [
            {
              label: `All ${action.testCases.size} test cases`,
              isExpanded: true,
              value: '*',
              options: cp.OptionGroup.groupValues(action.testCases),
            },
          ],
          label: `Test cases (${action.testCases.size})`,
          tags: {
            ...state.testCase.tags,
            options: cp.OptionGroup.groupValues(action.tags),
          },
        },
      };
    }),

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
      const datumX = parseFloat(sequence.data[action.datumIndex].x);
      let prevX = 0;
      if (action.datumIndex > 0) {
        prevX = parseFloat(sequence.data[action.datumIndex - 1].x);
      }
      let nextX = 100;
      if (action.datumIndex < sequence.data.length - 1) {
        nextX = parseFloat(sequence.data[action.datumIndex + 1].x);
      }
      const xBrushes = [
        {x: ((datumX + prevX) / 2) + '%', revision: 123},
        {x: ((datumX + nextX) / 2) + '%', revision: 123},
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

    clearTimeseries: cp.ElementBase.statePathReducer((state, action) => {
      return {
        ...state,
        histograms: undefined,
        relatedTabs: [],
      };
    }),

    layoutRelatedTabs: cp.ElementBase.statePathReducer((state, action) => {
      return {...state, relatedTabs: action.relatedTabs};
    }),
  };

  ChartSection.newStateOptionsFromQueryParams = queryParams => {
    const options = {parameters: {}};
    for (const [name, value] of Object.entries(queryParams)) {
      if (name === 'testSuites') {
        options.parameters.testSuites = value.split(',');
      } else if (name === 'measurements') {
        options.parameters.measurements = value.split(',');
      } else if (name === 'bots') {
        options.parameters.bots = value.split(',');
      } else if (name === 'testCases') {
        options.parameters.testCases = value.split(',');
      } else if (name === 'statistics') {
        options.parameters.statistics = value.split(',');
      } else if (name === 'rel') {
        options.relatedTabName = value;
      }
    }
    return options;
  };

  ChartSection.newState = options => {
    const parameters = options.parameters || {};
    const testSuites = parameters.testSuites || [];
    const measurements = parameters.measurements || [];
    const bots = parameters.bots || [];
    const testCases = parameters.testCases || [];
    const statistics = parameters.statistics || ['avg'];
    const selectedRelatedTabName = options.relatedTabName || undefined;
    return {
      isLoading: false,
      isExpanded: false,
      title: '',
      isTitleCustom: false,
      legend: [],
      minimapLayout: {
        ...cp.ChartTimeseries.newState(),
        dotCursor: '',
        dotRadius: 0,
        height: 60,
        showXAxisTickLines: true,
        xAxisHeight: 15,
      },
      chartLayout: {
        ...cp.ChartTimeseries.newState(),
        showXAxisTickLines: true,
        showYAxisTickLines: true,
        xAxisHeight: 15,
      },
      histograms: undefined,
      showHistogramsControls: false,
      relatedTabs: [],
      selectedRelatedTabName,
      selectedRelatedTabIndex: -1,
      testSuite: {
        label: 'Test suites (100)',
        canAggregate: true,
        isAggregated: false,
        inputValue: '',  // ChartParameter will update this
        selectedOptions: testSuites,
        options: cp.dummyTestSuites(),
      },
      bot: {
        label: 'Bots',
        canAggregate: true,
        isAggregated: true,
        inputValue: '',  // ChartParameter will update this
        selectedOptions: bots,
        options: [],
      },
      measurement: {
        label: 'Measurements',
        canAggregate: false,
        inputValue: '',  // ChartParameter will update this
        selectedOptions: measurements,
        options: [],
      },
      testCase: {
        label: 'Test cases',
        canAggregate: true,
        isAggregated: true,
        inputValue: '',  // ChartParameter will update this
        selectedOptions: testCases,
        options: [],
        tags: {
          options: [],
          selectedOptions: [],
        },
      },
      statistic: {
        label: 'Statistics',
        canAggregate: false,
        inputValue: statistics.join(', '),
        selectedOptions: statistics,
        options: [
          'avg',
          'std',
          'count',
          'min',
          'max',
          'median',
          'iqr',
          '90%',
          '95%',
          '99%',
        ],
      },
    };
  };

  ChartSection.cartesianProduct = components => {
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
  };

  ChartSection.buildLegend = (parameters, parameterProducts) => {
    if (parameterProducts.length < 2) return [];
    return ChartSection.buildLegendInternal_([], parameters);
  };

  ChartSection.buildLegendInternal_ = (prefix, parameters) => {
    if (parameters.length === 1) {
      // Recursion base case.

      if (parameters[0].length === 1) {
        const testPath = prefix.concat([parameters[0][0]]);
        return [{
          label: parameters[0][0],
          testPath,
          color: '',
        }];
      }

      const items = [];
      for (const label of parameters[0]) {
        const testPath = prefix.concat([label]);
        items.push({
          label,
          testPath,
          color: '',
        });
      }
      return items;
    }

    if (parameters[0].length === 1) {
      // Skip this grouping level.
      return ChartSection.buildLegendInternal_(
          prefix.concat([parameters[0][0]]), parameters.slice(1));
    }

    // Recursive case.
    const items = [];
    parameters[0].sort((a, b) => a.localeCompare(b));
    for (const label of parameters[0]) {
      const children = ChartSection.buildLegendInternal_(
          prefix.concat([label]), parameters.slice(1));
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
  };

  ChartSection.testPathEqual = (a, b) => {
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; ++i) {
      if (a[i] !== b[i]) return false;
    }
    return true;
  };

  cp.ElementBase.register(ChartSection);

  return {
    ChartSection,
  };
});
