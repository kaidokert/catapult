/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  const SQRT2 = Math.sqrt(2);

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
          isExpanded: {type: Boolean},
          relatedTabs: {type: Array},
          sectionId: {type: String},
          selectedRelatedTabIndex: {type: Number},
          showHistogramsControls: {type: Boolean},
          testPathComponents: {
            type: Array,
          },
          title: {type: String},
          tooltip: {type: Object},
        }),
        ...cp.ElementBase.statePathProperties('sharedStatePath', {
          xCursor: {type: Number},
        }),
      };
    }

    showLegend_(isExpanded, legend, histograms) {
      return !isExpanded && !this._empty(legend) && this._empty(histograms);
    }

    ready() {
      super.ready();
      this.scrollIntoView(true);
    }

    connectedCallback() {
      super.connectedCallback();
      this.dispatch('connected', this.statePath);
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
      this.dispatch('dotClick', this.statePath,
          e.detail.ctrlKey, e.detail.lineIndex, e.detail.datumIndex);
    }

    onDotMouseOver_(e) {
      this.dispatch('dotMouseOver', this.statePath,
          e.detail.lineIndex, e.detail.datumIndex, e.detail.dotRect);
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

    onSelectRelatedTab_(e) {
      this.dispatch('selectRelatedTab', this.statePath, e.target.selected);
    }

    onSparklineTap_(e) {
      cp.todo('promote sparkline to chart');
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
  }

  ChartSection.actions = {
    connected: statePath => async (dispatch, getState) => {
      const state = Polymer.Path.get(getState(), statePath);
      for (let i = 0; i < 4; ++i) {
        dispatch(cp.TestPathComponent.actions.updateInputValue(
            `${statePath}.testPathComponents.${i}`));
      }
      if (state.testPathComponents[0].selectedOptions) {
        dispatch(ChartSection.actions.loadParameters(statePath));
      }
      dispatch(ChartSection.actions.maybeLoadTimeseries(statePath));
      dispatch(ChartSection.actions.focusNextComponent(statePath));
    },

    loadParameters: statePath => async (dispatch, getState) => {
      const testSuites = Polymer.Path.get(
          getState(), `${statePath}.testPathComponents.0.selectedOptions`);
      const bots = cp.dummyBots(testSuites);
      dispatch(cp.ElementBase.actions.updateObject(
          `${statePath}.testPathComponents.1`, {
            options: cp.OptionGroup.groupValues(bots).map(option => {
              return {...option, isExpanded: true};
            }),
            placeholder: `Bots (${bots.length})`,
          }));

      const measurements = cp.dummyMeasurements(testSuites);
      dispatch(cp.ElementBase.actions.updateObject(
          `${statePath}.testPathComponents.2`, {
            options: cp.OptionGroup.groupValues(measurements),
            placeholder: `Measurements (${measurements.length})`,
          }));

      const testCases = cp.dummyTestCases(testSuites);
      dispatch(cp.ElementBase.actions.updateObject(
          `${statePath}.testPathComponents.3`, {
            options: [{
              label: `All ${testCases.length} test cases`,
              isExpanded: true,
              value: '*',
              options: cp.OptionGroup.groupValues(testCases),
            }],
            placeholder: `Test cases (${testCases.length})`,
          }));
      dispatch(cp.ElementBase.actions.updateObject(
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
            {normalized: value}));
      },

    brushChart: (statePath, brushIndex, value) =>
      async (dispatch, getState) => {
        dispatch(cp.ElementBase.actions.updateObject(
            `${statePath}.chartLayout.xBrushes.${brushIndex}`,
            {normalized: value}));
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
        type: ChartSection.reducers.clearTimeseries.typeName,
        statePath,
      });
    },

    updateLocation: sectionState => async (dispatch, getState) => {
      const components = sectionState.testPathComponents;
      if (components[3].selectedOptions.length > 1) {
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

      const queryParams = {
        testSuites: components[0].selectedOptions.join(','),
        measurements: components[2].selectedOptions.join(','),
        bots: components[1].selectedOptions.join(','),
      };
      if (components[3].selectedOptions.length === 1) {
        queryParams.testCases = components[3].selectedOptions[0];
      }
      const statistics = components[4].selectedOptions;
      if (statistics.length > 1 || statistics[0] !== 'avg') {
        queryParams.statistics = statistics.join(',');
      }

      cp.todo('store options, isExpanded, selectedRelatedTab');

      dispatch(cp.ChromeperfApp.actions.updateRoute('chart', queryParams));
    },

    loadTimeseries: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(
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

      const fetchMark = tr.b.Timing.mark('fetch', 'timeseries');
      cp.todo('fetch Rows from backend via cache');
      await tr.b.timeout(500);
      fetchMark.end();

      let brightnessRange;
      if (testPathCartesianProduct.length > 15) {
        cp.todo('brightnessRange');
      }
      const colors = tr.b.generateFixedColorScheme(
          testPathCartesianProduct.length, {hueOffset: 0.64});

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

      cp.todo('pass innerHeight - rect.height to histograms');

      let legend = [];
      if (chartBrushes.length === 0) {
        legend = ChartSection.buildLegend(
            selectedTestPathComponents, testPathCartesianProduct, colors);
      }

      dispatch({
        type: ChartSection.reducers.layoutChart.typeName,
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

    dotMouseOver: (statePath, lineIndex, datumIndex, dotRect) =>
      async (dispatch, getState) => {
        dispatch({
          type: ChartSection.reducers.showTooltip.typeName,
          statePath,
          lineIndex,
          dotRect,
        });

        statePath = `${statePath}.chartLayout.lines`;
        const lines = Polymer.Path.get(getState(), statePath);
        if (lines.length < 2) return;
        dispatch({
          type: ChartSection.reducers.dotMouseOver.typeName,
          statePath,
          lineIndex,
        });
      },

    dotMouseOut: (statePath, lineIndex) =>
      async (dispatch, getState) => {
        // Thou shalt always hide the tooltip whenever the mouse is not on the
        // dot.
        dispatch(cp.ElementBase.actions.updateObject(
            `${statePath}.tooltip`,
            {isVisible: false}));
        dispatch(cp.ElementBase.actions.updateObject(
            `${statePath}.chartLayout.lines.${lineIndex}`,
            {strokeWidth: 1}));
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

    showTooltip: cp.ElementBase.statePathReducer((state, action) => {
      const borderColor = state.chartLayout.lines[action.lineIndex].color;
      const dotRadius = state.chartLayout.dotRadius;
      // dotRect contains the top and left coordinates of the dot, which is a
      // geometric circle. Offset the tooltip such that its own top left corner
      // is tangent to the bottom-right edge of the dot circle. Do not allow the
      // tooltip to overlap the dot, which can cause flickering via rapid
      // mouseover/mouseout events.
      const offset = Math.ceil(dotRadius + (dotRadius / SQRT2));

      return {
        ...state,
        tooltip: {
          x: action.dotRect.x + offset,
          y: action.dotRect.y + offset,
          borderColor,
          rows: [
            {name: 'value', value: '9.99MB'},
            {name: 'chromium', value: '123456-234567'},
          ],
          isVisible: true,
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
      return {...state, relatedTabs: action.relatedTabs};
    }),
  };

  ChartSection.newStateOptionsFromQueryParams = queryParams => {
    const options = {
      parameters: {
        testSuites: [],
        measurements: [],
        bots: [],
        testCases: [],
        statistics: [],
      },
      relatedTabName: undefined,
    };
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
      tooltip: {
        isVisible: false,
        x: 0,
        y: 0,
        rows: [],
      },
      testPathComponents: [
        {
          placeholder: 'Test suites (100)',
          canAggregate: true,
          inputValue: '',  // TestPathComponent will update this
          selectedOptions: testSuites,
          options: cp.dummyTestSuites(),
        },
        {
          placeholder: 'Bots',
          canAggregate: true,
          inputValue: '',  // TestPathComponent will update this
          selectedOptions: bots,
          options: [],
        },
        {
          placeholder: 'Measurements',
          canAggregate: false,
          inputValue: '',  // TestPathComponent will update this
          selectedOptions: measurements,
          options: [],
        },
        {
          placeholder: 'Test cases',
          canAggregate: true,
          inputValue: '',  // TestPathComponent will update this
          selectedOptions: testCases,
          options: [],
          tags: {
            options: [],
            selectedOptions: [],
          },
        },
        {
          placeholder: 'Statistics',
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
      ],
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

  ChartSection.buildLegend = (components, testPathCartesianProduct, colors) => {
    const items = [];
    if (testPathCartesianProduct.length < 2) return items;
    const colorMap = new Map();
    for (let i = 0; i < colors.length; ++i) {
      colorMap.set(JSON.stringify(testPathCartesianProduct[i]), colors[i]);
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
