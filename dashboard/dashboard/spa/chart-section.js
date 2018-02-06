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
      dispatch(cp.ChartParameter.actions.updateInputValue(
          `${statePath}.bot`));
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

    loadTimeseries: statePath => async (dispatch, getState) => {
      const state = Polymer.Path.get(getState(), statePath);

      dispatch({
        type: ChartSection.reducers.buildLegend.typeName,
        statePath,
      });

      const lineDescriptors = ChartSection.lineDescriptors(
          ChartSection.parameterMatrix(state));

      dispatch(cp.ChartTimeseries.actions.load(`${statePath}.minimapLayout`, [
        {
          ...lineDescriptors[0],
          minTimestamp: 0,
          maxTimestamp: Infinity,
        },
      ]));

      dispatch(cp.ChartTimeseries.actions.load(
          `${statePath}.chartLayout`, lineDescriptors));

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

    dotMouseOver: (statePath, line, datum) => async (dispatch, getState) => {
      // TODO bold legend
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
      dispatch({
        type: ChartSection.reducers.updateLegendColors.typeName,
        statePath,
      });
    },
  };

  ChartSection.reducers = {
    updateLegendColors: cp.ElementBase.statePathReducer((state, action) => {
      if (!state.legend) return state;
      const colorMap = new Map();
      for (const line of state.chartLayout.lines) {
        colorMap.set(JSON.stringify(line.descriptor), line.color);
      }
      function handleLegendEntry(entry) {
        if (entry.children) {
          return {...entry, children: entry.children.map(handleLegendEntry)};
        }
        const color = colorMap.get(JSON.stringify(entry.lineDescriptor));
        return {...entry, color};
      }
      const legend = state.legend.map(handleLegendEntry);
      return {...state, legend};
    }),

    buildLegend: cp.ElementBase.statePathReducer((state, action) => {
      const legend = ChartSection.buildLegend(
          ChartSection.parameterMatrix(state));
      return {...state, legend};
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
          selectedOptions: [[...action.bots][0]],
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
    const chartState = cp.ChartTimeseries.newState();
    return {
      isLoading: false,
      isExpanded: options.isExpanded || false,
      title: options.title || '',
      isTitleCustom: false,
      legend: undefined,
      minimapLayout: {
        ...chartState,
        brushSize: 0,
        dotCursor: '',
        dotRadius: 0,
        graphHeight: 40,
        xAxis: {
          ...chartState.xAxis,
          height: 0,
        },
        yAxis: {
          ...chartState.yAxis,
          width: 50,
        },
      },
      chartLayout: {
        ...chartState,
        xAxis: {
          ...chartState.xAxis,
          height: 15,
          showTickLines: true,
        },
        yAxis: {
          ...chartState.yAxis,
          width: 50,
          showTickLines: true,
        },
      },
      histograms: undefined,
      showHistogramsControls: false,
      relatedTabs: [],
      selectedRelatedTabName,
      selectedRelatedTabIndex: -1,
      testSuite: {
        label: 'Test suites (100)',
        canAggregate: true,
        isAggregated: parameters.testSuitesAggregated || false,
        inputValue: '',  // ChartParameter will update this
        selectedOptions: testSuites,
        options: cp.dummyTestSuites(),
      },
      bot: {
        label: 'Bots',
        canAggregate: true,
        isAggregated: parameters.botsAggregated !== false,
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
        isAggregated: parameters.testCasesAggregated !== false,
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

  ChartSection.lineDescriptors = ({
    testSuiteses, measurements, botses, testCaseses, statistics,
  }) => {
    const lineDescriptors = [];
    for (const testSuites of testSuiteses) {
      for (const measurement of measurements) {
        for (const bots of botses) {
          for (const testCases of testCaseses) {
            for (const statistic of statistics) {
              lineDescriptors.push({
                testSuites,
                measurement,
                bots,
                testCases,
                statistic,
              });
            }
          }
        }
      }
    }
    return lineDescriptors;
  };

  function legendEntry(label, children) {
    if (children.length === 1) {
      return {...children[0], label};
    }
    return {label, children};
  }

  ChartSection.buildLegend = ({
    testSuiteses, measurements, botses, testCaseses, statistics,
  }) => {
    // Return [{label, children: [{label, lineDescriptor, color}]}}]
    const legend = testSuiteses.map(testSuites =>
      legendEntry(testSuites[0], measurements.map(measurement =>
        legendEntry(measurement, botses.map(bots =>
          legendEntry(bots[0], testCaseses.map(testCases =>
            legendEntry(testCases[0], statistics.map(statistic => {
              const lineDescriptor = {
                testSuites,
                measurement,
                bots,
                testCases,
                statistic,
              };
              return {
                label: statistic,
                lineDescriptor,
                color: '',
              };
            })))))))));
    if (legend.length === 1) return legend[0].children;
    return legend;
  };

  ChartSection.parameterMatrix = state => {
    // Aggregated parameters look like [[a, b, c]].
    // Unaggregated parameters look like [[a], [b], [c]].
    let testSuiteses = state.testSuite.selectedOptions;
    if (state.testSuite.isAggregated) {
      testSuiteses = [testSuiteses];
    } else {
      testSuiteses = testSuiteses.map(testSuite => [testSuite]);
    }
    let botses = state.bot.selectedOptions;
    if (state.bot.isAggregated) {
      botses = [botses];
    } else {
      botses = botses.map(bot => [bot]);
    }
    let testCaseses = state.testCase.selectedOptions.filter(x => x);
    if (state.testCase.isAggregated) {
      testCaseses = [testCaseses];
    } else {
      testCaseses = testCaseses.map(testCase => [testCase]);
    }
    return {
      testSuiteses,
      measurements: state.measurement.selectedOptions,
      botses,
      testCaseses,
      statistics: state.statistic.selectedOptions,
    };
  };

  ChartSection.testPathEqual = (a, b) => {
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; ++i) {
      if (a[i] !== b[i]) return false;
    }
    return true;
  };

  ChartSection.getSessionState = state => {
    return {
      parameters: {
        testSuites: state.testSuite.selectedOptions,
        testSuitesAggregated: state.testSuite.isAggregated,
        measurements: state.measurement.selectedOptions,
        bots: state.bot.selectedOptions,
        botsAggregated: state.bot.isAggregated,
        testCases: state.testCase.selectedOptions,
        testCasesAggregated: state.testCase.isAggregated,
        statistics: state.statistic.selectedOptions,
      },
      isExpanded: state.isExpanded,
      title: state.title,
      // TODO brushes
    };
  };

  ChartSection.getQueryParams = state => {
    if (state.testSuite.selectedOptions.length > 2 ||
        state.testCase.selectedOptions.length > 2 ||
        state.measurement.selectedOptions.length > 2 ||
        state.bot.selectedOptions.length > 2) {
      return undefined;
    }

    const queryParams = {};
    if (state.testSuite.selectedOptions.length) {
      queryParams.s = state.testSuite.selectedOptions.join(',');
    }
    if (state.testSuite.isAggregated) {
      queryParams.S = '';
    }
    if (state.measurement.selectedOptions.length) {
      queryParams.m = state.measurement.selectedOptions.join(',');
    }
    if (state.bot.selectedOptions.length) {
      queryParams.b = state.bot.selectedOptions.join(',');
    }
    if (state.bot.isAggregated) {
      queryParams.B = '';
    }
    if (state.testCase.selectedOptions.length) {
      queryParams.c = state.testCase.selectedOptions.join(',');
    }
    if (state.testCase.isAggregated) {
      queryParams.C = '';
    }
    const statistics = state.statistic.selectedOptions;
    if (statistics.length > 1 || statistics[0] !== 'avg') {
      queryParams.t = statistics.join(',');
    }
    // TODO options, selectedRelatedTab
    return queryParams;
  };

  cp.ElementBase.register(ChartSection);

  return {
    ChartSection,
  };
});
