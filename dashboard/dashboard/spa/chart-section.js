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
  }

  ChartSection.properties = {
    ...cp.ElementBase.statePathProperties('statePath', {
      bot: {type: Object},
      chartLayout: {type: Object},
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
      dispatch(ChartSection.actions.maybeLoadTimeseries(statePath));
    },

    bot: statePath => async (dispatch, getState) => {
      dispatch(ChartSection.actions.maybeLoadTimeseries(statePath));
    },

    aggregateBot: statePath => async (dispatch, getState) => {
      dispatch(ChartSection.actions.maybeLoadTimeseries(statePath));
    },

    testCase: statePath => async (dispatch, getState) => {
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
      dispatch({
        type: ChartSection.reducers.measurementOptions.typeName,
        statePath,
        measurements: cp.dummyMeasurements(state.testSuite.selectedOptions),
      });
    },

    botOptions: statePath => async (dispatch, getState) => {
      const state = Polymer.Path.get(getState(), statePath);
      dispatch({
        type: ChartSection.reducers.botOptions.typeName,
        statePath,
        bots: cp.dummyBots(state.testSuite.selectedOptions),
      });
    },

    testCaseOptions: statePath => async (dispatch, getState) => {
      const state = Polymer.Path.get(getState(), statePath);
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
      dispatch(cp.ElementBase.actions.updateObject(
          statePath, {isLoading: true}));

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
      let title = state.title;
      if (!state.isTitleCustom) {
        title = state.measurement.selectedOptions.join(', ');
        if (state.bot.selectedOptions.length > 0 &&
            state.bot.selectedOptions.length < 4) {
          title += ' on ' + state.bot.selectedOptions.join(', ');
        }
        if (state.testCase.selectedOptions.length > 0 &&
            state.testCase.selectedOptions.length < 4) {
          title += ' for ' + state.testCase.selectedOptions.join(', ');
        }
      }
      const parameterProducts = ChartSection.cartesianProduct(
          parameters);

      const fetchMark = tr.b.Timing.mark('fetch', 'timeseries');
      cp.todo('fetch Rows from backend via cache');
      await tr.b.timeout(500);
      fetchMark.end();

      let brightnessRange;
      if (parameterProducts.length > 15) {
        cp.todo('brightnessRange');
      }
      const colors = tr.b.generateFixedColorScheme(
          parameterProducts.length, {hueOffset: 0.64});

      cp.todo('refactor to call cp.MultiChart.layout()');

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
          x: (100 * (index + 0.5) / texts.length) + '%',
        };
      });

      const minimapLines = [{
        color: '' + colors[0],
        data: [{x: 1, y: 50}],
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
      cp.MultiChart.normalizeLinesInPlace(minimapLines);

      const chartLines = [];
      for (let tpi = 0; tpi < colors.length; ++tpi) {
        const testPath = parameterProducts[tpi];
        const color = colors[tpi];
        const y0 = 1 + parseInt(98 * Math.random());
        const sequence = {
          color: '' + color,
          testPath,
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
      cp.MultiChart.normalizeLinesInPlace(chartLines);

      const chartXAxisTicks = [
        'Dec', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13',
        '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24',
        '25', '26', '27', '28', '29', '30', '31', '2018', '2', '3',
      ].map((text, index, texts) => {
        return {
          text,
          x: (100 * (index + 0.5) / texts.length) + '%',
        };
      });

      const chartYAxisTicks = [
        '9MB', '8MB', '7MB', '6MB', '5MB', '4MB', '3MB', '2MB', '1MB',
      ].map((text, index, texts) => {
        return {
          text,
          x: '0%',
          y: (20 + (chartHeight - textHeight - 20) * index / texts.length) +
          '%',
        };
      });

      const minimapBrushes = [
        {x: '60%', revision: 60},
        {x: '90%', revision: 90},
      ];
      const chartBrushes = [];

      cp.todo('pass innerHeight - rect.height to histograms');

      let legend = [];
      if (chartBrushes.length === 0) {
        legend = ChartSection.buildLegend(
            parameters, parameterProducts, colors);
      }

      dispatch({
        type: ChartSection.reducers.layoutChart.typeName,
        statePath,
        title,
        legend,

        minimapLayout: {
          dotCursor: '',
          dotRadius: 0,
          showYAxisTickLines: false,
          graphHeight: minimapHeight - textHeight - 15,
          height: minimapHeight,
          lines: minimapLines,
          showXAxisTickLines: true,
          tooltip: {isVisible: false},
          xAxisHeight: textHeight,
          xAxisTicks: minimapXAxisTicks,
          xBrushes: minimapBrushes,
          yAxisWidth: maxYAxisTickWidth,
        },

        chartLayout: {
          dotCursor: 'pointer',
          dotRadius: 6,
          graphHeight: chartHeight - textHeight - 15,
          height: chartHeight,
          lines: chartLines,
          showXAxisTickLines: true,
          showYAxisTickLines: true,
          tooltip: {isVisible: false},
          xAxisHeight: textHeight,
          xAxisTicks: chartXAxisTicks,
          xBrushes: chartBrushes,
          yAxisTicks: chartYAxisTicks,
          yAxisWidth: maxYAxisTickWidth,
        },
      });

      cp.todo('fetch RelatedNameMaps via cache');
      cp.todo('build tabs of related sparklines');

      dispatch({
        type: ChartSection.reducers.layoutRelatedTabs.typeName,
        statePath,

        relatedTabs: [
          {
            name: 'Processes',
            sparklines: [
              {
                name: 'browser process',
                layout: {
                  dotCursor: 'pointer',
                  dotRadius: 0,
                  graphHeight: 100 - 15,
                  height: 100,
                  lines: chartLines,
                  showXAxisTickLines: false,
                  showYAxisTickLines: false,
                  tooltip: {isVisible: false},
                  xAxisHeight: 0,
                  xAxisTicks: [],
                  xBrushes: [],
                  yAxisTicks: [],
                  yAxisWidth: 0,
                },
              },
              {
                name: 'gpu process',
                layout: {
                  dotCursor: 'pointer',
                  dotRadius: 0,
                  graphHeight: 100 - 15,
                  height: 100,
                  lines: chartLines,
                  showXAxisTickLines: false,
                  showYAxisTickLines: false,
                  tooltip: {isVisible: false},
                  xAxisHeight: 0,
                  xAxisTicks: [],
                  xBrushes: [],
                  yAxisTicks: [],
                  yAxisWidth: 0,
                },
              },
              {
                name: 'renderer processes',
                layout: {
                  dotCursor: 'pointer',
                  dotRadius: 0,
                  graphHeight: 100 - 15,
                  height: 100,
                  lines: chartLines,
                  showXAxisTickLines: false,
                  showYAxisTickLines: false,
                  tooltip: {isVisible: false},
                  xAxisHeight: 0,
                  xAxisTicks: [],
                  xBrushes: [],
                  yAxisTicks: [],
                  yAxisWidth: 0,
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
                  dotCursor: 'pointer',
                  dotRadius: 0,
                  graphHeight: 100 - 15,
                  height: 100,
                  lines: chartLines,
                  showXAxisTickLines: false,
                  showYAxisTickLines: false,
                  tooltip: {isVisible: false},
                  xAxisHeight: 0,
                  xAxisTicks: [],
                  xBrushes: [],
                  yAxisTicks: [],
                  yAxisWidth: 0,
                },
              },
              {
                name: 'gpu process',
                layout: {
                  dotCursor: 'pointer',
                  dotRadius: 0,
                  graphHeight: 100 - 15,
                  height: 100,
                  lines: chartLines,
                  showXAxisTickLines: false,
                  showYAxisTickLines: false,
                  tooltip: {isVisible: false},
                  xAxisHeight: 0,
                  xAxisTicks: [],
                  xBrushes: [],
                  yAxisTicks: [],
                  yAxisWidth: 0,
                },
              },
              {
                name: 'renderer processes',
                layout: {
                  dotCursor: 'pointer',
                  dotRadius: 0,
                  graphHeight: 100 - 15,
                  height: 100,
                  lines: chartLines,
                  showXAxisTickLines: false,
                  showYAxisTickLines: false,
                  tooltip: {isVisible: false},
                  xAxisHeight: 0,
                  xAxisTicks: [],
                  xBrushes: [],
                  yAxisTicks: [],
                  yAxisWidth: 0,
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
        dispatch(cp.MultiChart.actions.tooltip(`${statePath}.chartLayout`, [
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
        dispatch(cp.MultiChart.actions.dotMouseOut(
            statePath + '.chartLayout', i));
      }
    },
  };

  ChartSection.reducers = {
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
      chartLayout: {},
      minimapLayout: {},
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

  ChartSection.buildLegend = (components, parameterProducts, colors) => {
    const items = [];
    if (parameterProducts.length < 2) return items;
    const colorMap = new Map();
    for (let i = 0; i < colors.length; ++i) {
      colorMap.set(JSON.stringify(parameterProducts[i]), colors[i]);
    }
    return ChartSection.buildLegendInternal_([], components, colorMap);
  };

  ChartSection.buildLegendInternal_ = (prefix, components, colorMap) => {
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
