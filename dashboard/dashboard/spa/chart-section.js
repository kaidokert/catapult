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

    isLoading_(isLoading, minimapLayout, chartLayout) {
      if (isLoading) return true;
      if (minimapLayout && minimapLayout.isLoading) return true;
      if (chartLayout && chartLayout.isLoading) return true;
      return false;
    }

    hideOptions_(minimapLayout) {
      return this.$.minimap.showPlaceholder(
          (minimapLayout && minimapLayout.isLoading),
          (minimapLayout ? minimapLayout.lines : []));
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
      if (event.detail.sourceEvent.detail.state === 'end') {
        this.dispatch('brushMinimap', this.statePath);
      }
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
      this.dispatch('dotMouseOver', this.statePath, event.detail.lineIndex);
    }

    onDotMouseOut_(event) {
      this.dispatch('dotMouseOut', this.statePath);
    }

    onBrush_(event) {
      this.dispatch('brushChart', this.statePath,
          event.detail.brushIndex,
          event.detail.value);
    }

    onLegendMouseOver_(event) {
      this.dispatch('legendMouseOver', this.statePath,
          event.detail.lineDescriptor);
    }

    onLegendMouseOut_(event) {
      this.dispatch('legendMouseOut', this.statePath);
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

    onToggleReferenceBuild_(event) {
      this.dispatch('toggleReferenceBuild', this.statePath);
    }

    onToggleNormalize_(event) {
      this.dispatch('toggleNormalize', this.statePath);
    }

    onToggleCenter_(event) {
      this.dispatch('toggleCenter', this.statePath);
    }

    onToggleZeroYAxis_(event) {
      this.dispatch('toggleZeroYAxis', this.statePath);
    }

    onToggleFixedXAxis_(event) {
      this.dispatch('toggleFixedXAxis', this.statePath);
    }

    onAuthChanged_() {
      this.dispatch('authChange', this.statePath);
    }
  }

  ChartSection.properties = {
    ...cp.ElementBase.statePathProperties('statePath', {
      bot: {type: Object},
      chartLayout: {type: Object, observer: 'onChartChange_'},
      fixedXAxis: {type: Boolean},
      histograms: {type: Object},
      isExpanded: {type: Boolean},
      isLoading: {type: Boolean},
      isShowingOptions: {type: Boolean},
      legend: {type: Array},
      measurement: {type: Object},
      minimapLayout: {type: Object},
      normalize: {type: Boolean},
      center: {type: Boolean},
      referenceBuild: {type: Boolean},
      relatedTabs: {type: Array},
      sectionId: {type: String},
      selectedRelatedTabIndex: {type: Number},
      showHistogramsControls: {type: Boolean},
      statistic: {type: Object},
      testCase: {type: Object},
      testSuite: {type: Object},
      title: {type: String},
      zeroYAxis: {type: Boolean},
    }),
    xCursor: {
      type: Object,
      statePath: 'globalChartXCursor',
    },
    authHeaders: {
      type: Object,
      statePath: 'authHeaders',
      observer: 'onAuthChanged_',
    },
  };

  ChartSection.actions = {
    connected: statePath => async (dispatch, getState) => {
      let state = Polymer.Path.get(getState(), statePath);
      dispatch(ChartSection.actions.testSuites(statePath));
      if (state.testSuite.selectedOptions.length) {
        dispatch(cp.DropdownInput.actions.populateMagicOptions(
            `${statePath}.testSuite`));
        await dispatch(ChartSection.actions.testSuite(statePath));
      } else {
        dispatch(cp.DropdownInput.actions.focus(`${statePath}.testSuite`));
      }
      state = Polymer.Path.get(getState(), statePath);
      dispatch(ChartSection.actions.maybeLoadTimeseries(statePath));
      dispatch(cp.DropdownInput.actions.populateMagicOptions(
          `${statePath}.measurement`));
      dispatch(cp.DropdownInput.actions.populateMagicOptions(
          `${statePath}.bot`));
      dispatch(cp.DropdownInput.actions.populateMagicOptions(
          `${statePath}.testCase`));
    },

    authChange: statePath => async (dispatch, getState) => {
      dispatch(ChartSection.actions.testSuites(statePath));
    },

    testSuites: statePath => async (dispatch, getState) => {
      const {options, count} = await dispatch(
          cp.TimeseriesCache.actions.testSuites());
      dispatch(cp.ElementBase.actions.updateObject(`${statePath}.testSuite`, {
        options,
        label: `Test suites (${count})`,
      }));
    },

    toggleZeroYAxis: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.toggleBoolean(
          `${statePath}.zeroYAxis`));
      dispatch(ChartSection.actions.maybeLoadTimeseries(statePath));
    },

    toggleFixedXAxis: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.toggleBoolean(
          `${statePath}.fixedXAxis`));
      dispatch(ChartSection.actions.maybeLoadTimeseries(statePath));
    },

    toggleNormalize: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.toggleBoolean(
          `${statePath}.normalize`));
      dispatch(ChartSection.actions.maybeLoadTimeseries(statePath));
    },

    toggleCenter: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.toggleBoolean(
          `${statePath}.center`));
      dispatch(ChartSection.actions.maybeLoadTimeseries(statePath));
    },

    toggleReferenceBuild: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.toggleBoolean(
          `${statePath}.referenceBuild`));
      dispatch(ChartSection.actions.maybeLoadTimeseries(statePath));
    },

    testSuite: statePath => async (dispatch, getState) => {
      let state = Polymer.Path.get(getState(), statePath);
      if (state.testSuite.selectedOptions.length === 0) {
        dispatch({
          type: ChartSection.reducers.describe.typeName,
          statePath,
          measurements: new Set(),
          bots: new Set(),
          testCases: new Set(),
          testCaseTags: new Set(),
          complete: true,
        });
        return;
      }

      if (state.measurement.selectedOptions.length === 0) {
        dispatch(cp.DropdownInput.actions.focus(`${statePath}.measurement`));
      } else {
        dispatch(ChartSection.actions.maybeLoadTimeseries(statePath));
      }

      const measurements = new Set();
      const bots = new Set();
      const testCases = new Set();
      const testCaseTags = new Set();
      const describedTestSuites = new Set();
      const testSuites = new Set(state.testSuite.selectedOptions);
      await Promise.all([...testSuites].map(async testSuite => {
        // Test suite descriptors might already be in local memory, or it might
        // take the backend up to a minute to compute them, or it might take a
        // couple of seconds to serve them from memcache, so fetch them in
        // parallel.
        const testSuiteDescriptor = await dispatch(
            cp.TimeseriesCache.actions.describe(testSuite));

        state = Polymer.Path.get(getState(), statePath);
        if (!tr.b.setsEqual(
            testSuites, new Set(state.testSuite.selectedOptions))) {
          // The user changed the set of selected testSuites, so stop handling
          // the old set of testSuites. The new set of testSuites will be
          // handled by a new dispatch of this action creator.
          return;
        }

        for (const bot of testSuiteDescriptor.bots) bots.add(bot);
        for (const measurement of testSuiteDescriptor.measurements) {
          measurements.add(measurement);
        }
        for (const testCase of testSuiteDescriptor.testCases) {
          testCases.add(testCase);
        }

        describedTestSuites.add(testSuite);
        const describedTestSuiteCount = describedTestSuites.size;
        if (describedTestSuiteCount < testSuites.size) {
          // Creating dom elements for these options can be costly. Try not to
          // dispatch reducers.describe more often than necessary.
          await cp.ElementBase.timeout(500);
        }
        if (describedTestSuiteCount < describedTestSuites.size) {
          // Another testSuiteDescriptor was loaded while waiting for the
          // timeout.
          return;
        }

        dispatch({
          type: ChartSection.reducers.describe.typeName,
          statePath,
          measurements,
          bots,
          testCases,
          testCaseTags,
          complete: (testSuites.size === describedTestSuites.size),
        });

        // reducers.describe might change these selectedOptions:
        dispatch(cp.DropdownInput.actions.populateMagicOptions(
            `${statePath}.measurement`));
        dispatch(cp.DropdownInput.actions.populateMagicOptions(
            `${statePath}.bot`));
        dispatch(cp.DropdownInput.actions.populateMagicOptions(
            `${statePath}.testCase`));
      }));
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

    brushMinimap: statePath => async (dispatch, getState) => {
      dispatch({
        type: ChartSection.reducers.brushMinimap.typeName,
        statePath,
      });
      dispatch(ChartSection.actions.loadTimeseries(statePath));
    },

    brushChart: (statePath, brushIndex, value) =>
      async (dispatch, getState) => {
        dispatch(cp.ElementBase.actions.updateObject(
            `${statePath}.chartLayout.xAxis.brushes.${brushIndex}`,
            {xPct: value + '%'}));
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
      const state = Polymer.Path.get(getState(), statePath);
      if (state.minimapLayout.lines.length) {
        dispatch(cp.ChartTimeseries.actions.load(
            `${statePath}.minimapLayout`, []));
      }
      if (state.chartLayout.lines.length) {
        dispatch(cp.ChartTimeseries.actions.load(
            `${statePath}.chartLayout`, []));
      }
      if (state.relatedTabs.length) {
        dispatch({
          type: ChartSection.reducers.clearTimeseries.typeName,
          statePath,
        });
      }
    },

    loadTimeseries: statePath => async (dispatch, getState) => {
      dispatch({
        type: ChartSection.reducers.buildLegend.typeName,
        statePath,
      });

      let state = Polymer.Path.get(getState(), statePath);
      let lineDescriptors = ChartSection.createLineDescriptors(
          ChartSection.parameterMatrix(state));

      const minimapPath = `${statePath}.minimapLayout`;
      await dispatch(cp.ChartTimeseries.actions.load(minimapPath, [
        lineDescriptors[0],
      ], {
        fixedXAxis: state.fixedXAxis,
      }));
      // TODO return if this load has been preempted

      state = Polymer.Path.get(getState(), statePath);
      const minimapData = state.minimapLayout.lines[0].data;
      let minRevision = state.minRevision;
      let maxRevision = state.maxRevision;
      const brushes = [];
      if (minimapData.length) {
        let minDatum;
        if (minRevision === undefined) {
          minDatum = minimapData[Math.max(0, minimapData.length - 100)];
          minRevision = minDatum.x;
        } else {
          minDatum = tr.b.findClosestElementInSortedArray(
              minimapData, datum => datum.x, minRevision);
        }
        let maxDatum;
        if (maxRevision === undefined) {
          maxDatum = minimapData[minimapData.length - 1];
          maxRevision = maxDatum.x;
        } else {
          maxDatum = tr.b.findClosestElementInSortedArray(
              minimapData, datum => datum.x, maxRevision);
        }
        brushes.push({
          x: minDatum.x,
          xFixed: minDatum.xFixed,
          xPct: minDatum.xPct,
        });
        brushes.push({
          x: maxDatum.x,
          xFixed: maxDatum.xFixed,
          xPct: maxDatum.xPct,
        });
      }
      dispatch(cp.ElementBase.actions.updateObject(
          `${minimapPath}.xAxis`, {brushes}));

      lineDescriptors = lineDescriptors.map(d => {
        return {...d, minRevision, maxRevision};
      });
      dispatch(cp.ChartTimeseries.actions.load(
          `${statePath}.chartLayout`, lineDescriptors, {
            fixedXAxis: state.fixedXAxis,
            normalize: state.normalize,
            center: state.center,
            zeroYAxis: state.zeroYAxis,
          }));
      dispatch({
        type: ChartSection.reducers.buildRelatedTabs.typeName,
        statePath,
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

    dotMouseOver: (statePath, lineIndex) => async (dispatch, getState) => {
    },

    dotMouseOut: (statePath, lineIndex) => async (dispatch, getState) => {
    },

    legendMouseOver: (statePath, lineDescriptor) =>
      async (dispatch, getState) => {
        const state = Polymer.Path.get(getState(), statePath);
        lineDescriptor = JSON.stringify(lineDescriptor);
        for (let lineIndex = 0; lineIndex < state.chartLayout.lines.length;
             ++lineIndex) {
          if (JSON.stringify(state.chartLayout.lines[lineIndex].descriptor) ===
              lineDescriptor) {
            dispatch(cp.ChartBase.actions.boldLine(
                statePath + '.chartLayout', lineIndex));
            break;
          }
        }
      },

    legendMouseOut: statePath => async (dispatch, getState) => {
      dispatch(cp.ChartBase.actions.unboldLines(statePath + '.chartLayout'));
    },

    updateLegendColors: statePath => async (dispatch, getState) => {
      const state = Polymer.Path.get(getState(), statePath);
      if (!state || !state.legend) return;
      dispatch({
        type: ChartSection.reducers.updateLegendColors.typeName,
        statePath,
      });
    },
  };

  ChartSection.reducers = {
    brushMinimap: cp.ElementBase.statePathReducer((state, action) => {
      const range = new tr.b.math.Range();
      for (const brush of state.minimapLayout.xAxis.brushes) {
        const index = tr.b.findLowIndexInSortedArray(
            state.minimapLayout.lines[0].data,
            datum => parseFloat(datum.xPct),
            parseFloat(brush.xPct));
        const datum = state.minimapLayout.lines[0].data[index];
        range.addValue(datum.x);
      }
      return {...state, minRevision: range.min, maxRevision: range.max};
    }),

    updateLegendColors: cp.ElementBase.statePathReducer((state, action) => {
      if (!state.legend) return state;
      const colorMap = new Map();
      for (const line of state.chartLayout.lines) {
        colorMap.set(cp.ChartTimeseries.stringifyDescriptor(
            line.descriptor), line.color);
      }
      function handleLegendEntry(entry) {
        if (entry.children) {
          return {...entry, children: entry.children.map(handleLegendEntry)};
        }
        const color = colorMap.get(cp.ChartTimeseries.stringifyDescriptor(
            entry.lineDescriptor));
        return {...entry, color};
      }
      return {...state, legend: state.legend.map(handleLegendEntry)};
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

    describe: cp.ElementBase.statePathReducer((state, action) => {
      let measurement = {
        ...state.measurement,
        options: cp.OptionGroup.groupValues(action.measurements),
        label: `Measurements (${action.measurements.size})`,
      };

      const bot = {
        ...state.bot,
        options: cp.OptionGroup.groupValues(action.bots).map(option => {
          return {...option, isExpanded: true};
        }),
        label: `Bots (${action.bots.size})`,
      };

      const testCaseOptions = [];
      if (action.testCases.size) {
        testCaseOptions.push({
          label: `All ${action.testCases.size} test cases`,
          isExpanded: true,
          value: '*',
          options: cp.OptionGroup.groupValues(action.testCases),
        });
      }

      let testCase = {
        ...state.testCase,
        options: testCaseOptions,
        label: `Test cases (${action.testCases.size})`,
        tags: {
          ...state.testCase.tags,
          options: cp.OptionGroup.groupValues(action.testCaseTags),
        },
      };

      if (action.complete) {
        measurement = {
          ...measurement,
          selectedOptions: measurement.selectedOptions.filter(m =>
            action.measurements.has(m)),
        };

        const allBots = [];
        for (const masterOption of bot.options) {
          for (const botOption of masterOption.options) {
            allBots.push(botOption.value);
          }
        }
        if (bot.selectedOptions.length === 0 ||
            ((bot.selectedOptions.length === 1) &&
            (bot.selectedOptions[0] === '*'))) {
          bot.selectedOptions = allBots;
        } else {
          bot.selectedOptions = bot.selectedOptions.filter(b =>
            allBots.includes(b));
        }

        testCase = {
          ...testCase,
          selectedOptions: testCase.selectedOptions.filter(testCase =>
            action.testCases.has(testCase)),
        };
      }

      return {...state, measurement, bot, testCase};
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
          xAxis: {
            ...state.chartLayout.xAxis,
            brushes: [],
          },
        },
        histograms: undefined,
      };
    }),

    dotClick: cp.ElementBase.statePathReducer((state, action) => {
      const sequence = state.chartLayout.lines[action.lineIndex];
      const datumX = parseFloat(sequence.data[action.datumIndex].xPct);
      let prevX = 0;
      if (action.datumIndex > 0) {
        prevX = parseFloat(sequence.data[action.datumIndex - 1].xPct);
      }
      let nextX = 100;
      if (action.datumIndex < sequence.data.length - 1) {
        nextX = parseFloat(sequence.data[action.datumIndex + 1].xPct);
      }
      const brushes = [
        {xPct: ((datumX + prevX) / 2) + '%'},
        {xPct: ((datumX + nextX) / 2) + '%'},
      ];
      if (action.ctrlKey) {
        brushes.push.apply(brushes, state.chartLayout.xAxis.brushes);
      }
      return {
        ...state,
        chartLayout: {
          ...state.chartLayout,
          xAxis: {
            ...state.chartLayout.xAxis,
            brushes,
          },
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

    buildRelatedTabs: cp.ElementBase.statePathReducer((state, action) => {
      const parameterMatrix = ChartSection.parameterMatrix({
        ...state,
        referenceBuild: false,
      });
      const relatedTabs = [];
      function maybeAddParameterTab(propertyName, tabName, matrixName) {
        if (state[propertyName].selectedOptions.length <= 1) return;
        if (!state[propertyName].isAggregated) return;
        relatedTabs.push({
          name: tabName,
          sparklines: state[propertyName].selectedOptions.map(option => {
            return {
              name: option,
              lineDescriptors: ChartSection.createLineDescriptors({
                ...parameterMatrix,
                [matrixName]: [[option]],
              }),
            };
          }),
        });
      }
      maybeAddParameterTab('testSuite', 'Test suites', 'testSuiteses');
      maybeAddParameterTab('bot', 'Bots', 'botses');
      maybeAddParameterTab('testCase', 'Test cases', 'testCaseses');

      const processSparklines = [];
      const componentSparklines = [];
      for (const measurement of state.measurement.selectedOptions) {
        if (d.MEMORY_PROCESS_RELATED_NAMES.has(measurement)) {
          for (const relatedMeasurement of d.MEMORY_PROCESS_RELATED_NAMES.get(
              measurement)) {
            if (relatedMeasurement === measurement) continue;
            const relatedParts = relatedMeasurement.split(':');
            const name = relatedParts[2];
            processSparklines.push({
              name,
              lineDescriptors: ChartSection.createLineDescriptors({
                ...parameterMatrix,
                measurements: [relatedMeasurement],
              }),
            });
          }
        }
        if (d.MEMORY_COMPONENT_RELATED_NAMES.has(measurement)) {
          for (const relatedMeasurement of d.MEMORY_COMPONENT_RELATED_NAMES.get(
              measurement)) {
            if (relatedMeasurement === measurement) continue;
            const relatedParts = relatedMeasurement.split(':');
            const name = relatedParts.slice(
                4, relatedParts.length - 1).join(':');
            componentSparklines.push({
              name,
              lineDescriptors: ChartSection.createLineDescriptors({
                ...parameterMatrix,
                measurements: [relatedMeasurement],
              }),
            });
          }
        }
      }
      if (processSparklines.length) {
        relatedTabs.push({
          name: 'Process',
          sparklines: processSparklines,
        });
      }
      if (componentSparklines.length) {
        relatedTabs.push({
          name: 'Component',
          sparklines: componentSparklines,
        });
      }

      return {...state, relatedTabs};
    }),
  };

  ChartSection.newStateOptionsFromQueryParams = routeParams => {
    return {
      parameters: {
        testSuites: routeParams.getAll('testSuite'),
        testSuitesAggregated: routeParams.get('aggSuites') !== null,
        measurements: routeParams.getAll('measurement'),
        bots: routeParams.getAll('bot'),
        botsAggregated: routeParams.get('splitBots') === null,
        testCases: routeParams.getAll('testCase'),
        testCasesAggregated: routeParams.get('splitCases') === null,
        statistics: routeParams.get('stat') ? routeParams.getAll('stat') :
          ['avg'],
      },
      minRevision: parseInt(routeParams.get('minRev')) || undefined,
      maxRevision: parseInt(routeParams.get('maxRev')) || undefined,
      relatedTabName: routeParams.get('rel') || '',
      normalize: routeParams.get('norm') !== null,
      center: routeParams.get('center') !== null,
      fixedXAxis: routeParams.get('natural') === null,
      zeroYAxis: routeParams.get('zeroY') !== null,
      referenceBuild: routeParams.get('test') === null,
    };
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
      minRevision: options.minRevision,
      maxRevision: options.maxRevision,
      referenceBuild: options.referenceBuild !== false,
      normalize: options.normalize || false,
      center: options.center || false,
      zeroYAxis: options.zeroYAxis || false,
      fixedXAxis: options.fixedXAxis !== false,
      minimapLayout: {
        ...chartState,
        dotCursor: '',
        dotRadius: 0,
        graphHeight: 40,
        xAxis: {
          ...chartState.xAxis,
          height: 15,
        },
        yAxis: {
          ...chartState.yAxis,
          width: 50,
          generateTicks: false,
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
        label: 'Test suites (loading)',
        canAggregate: true,
        isAggregated: parameters.testSuitesAggregated || false,
        query: '',
        selectedOptions: testSuites,
        options: [],
      },
      bot: {
        label: 'Bots',
        canAggregate: true,
        isAggregated: parameters.botsAggregated !== false,
        query: '',
        selectedOptions: bots,
        options: [],
      },
      measurement: {
        label: 'Measurements',
        canAggregate: false,
        query: '',
        selectedOptions: measurements,
        options: [],
      },
      testCase: {
        label: 'Test cases',
        canAggregate: true,
        isAggregated: parameters.testCasesAggregated !== false,
        query: '',
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
        query: '',
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

  ChartSection.createLineDescriptors = ({
    testSuiteses, measurements, botses, testCaseses, statistics,
    buildTypes,
  }) => {
    const lineDescriptors = [];
    for (const testSuites of testSuiteses) {
      for (const measurement of measurements) {
        for (const bots of botses) {
          for (const testCases of testCaseses) {
            for (const statistic of statistics) {
              for (const buildType of buildTypes) {
                lineDescriptors.push({
                  testSuites,
                  measurement,
                  bots,
                  testCases,
                  statistic,
                  buildType,
                });
              }
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
    buildTypes,
  }) => {
    // Return [{label, children: [{label, lineDescriptor, color}]}}]
    const legend = testSuiteses.map(testSuites =>
      legendEntry(testSuites[0], measurements.map(measurement =>
        legendEntry(measurement, botses.map(bots =>
          legendEntry(bots[0], testCaseses.map(testCases =>
            legendEntry(testCases[0], statistics.map(statistic =>
              legendEntry(statistic, buildTypes.map(buildType => {
                const lineDescriptor = {
                  testSuites,
                  measurement,
                  bots,
                  testCases,
                  statistic,
                  buildType,
                };
                return {
                  label: buildType,
                  lineDescriptor,
                  color: '',
                };
              })))))))))));
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
    const buildTypes = ['test'];
    if (state.referenceBuild) buildTypes.push('reference');
    return {
      testSuiteses,
      measurements: state.measurement.selectedOptions,
      botses,
      testCaseses,
      statistics: state.statistic.selectedOptions,
      buildTypes,
    };
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
      minRevision: state.minRevision,
      maxRevision: state.maxRevision,
      zeroYAxis: state.zeroYAxis,
      referenceBuild: state.referenceBuild,
      normalize: state.normalize,
      center: state.center,
      fixedXAxis: state.fixedXAxis,
    };
  };

  ChartSection.getRouteParams = state => {
    const allBotsSelected = state.bot.selectedOptions.length ===
        cp.OptionGroup.countDescendents(state.bot.options);

    if (state.testSuite.selectedOptions.length > 2 ||
        state.testCase.selectedOptions.length > 2 ||
        state.measurement.selectedOptions.length > 2 ||
        ((state.bot.selectedOptions.length > 2) && !allBotsSelected)) {
      return undefined;
    }

    const routeParams = new URLSearchParams();
    for (const testSuite of state.testSuite.selectedOptions) {
      routeParams.append('testSuite', testSuite);
    }
    if (state.testSuite.isAggregated) {
      routeParams.set('aggSuites', '');
    }
    for (const measurement of state.measurement.selectedOptions) {
      routeParams.append('measurement', measurement);
    }
    if (allBotsSelected) {
      routeParams.set('bot', '*');
    } else {
      for (const bot of state.bot.selectedOptions) {
        routeParams.append('bot', bot);
      }
    }
    if (!state.bot.isAggregated) {
      routeParams.set('splitBots', '');
    }
    for (const testCase of state.testCase.selectedOptions) {
      routeParams.append('testCase', testCase);
    }
    if (!state.testCase.isAggregated) {
      routeParams.set('splitCases', '');
    }
    const statistics = state.statistic.selectedOptions;
    if (statistics.length > 1 || statistics[0] !== 'avg') {
      for (const statistic of statistics) {
        routeParams.append('stat', statistic);
      }
    }
    if (state.minRevision !== undefined) {
      routeParams.set('minRev', state.minRevision);
    }
    if (state.maxRevision !== undefined) {
      routeParams.set('maxRev', state.maxRevision);
    }
    if (state.normalize) {
      routeParams.set('norm', '');
    }
    if (state.center) {
      routeParams.set('center', '');
    }
    if (!state.fixedXAxis) {
      routeParams.set('natural', '');
    }
    if (state.zeroYAxis) {
      routeParams.set('zeroY', '');
    }
    if (!state.referenceBuild) {
      routeParams.set('test', '');
    }
    // TODO selectedRelatedTab
    return routeParams;
  };

  ChartSection.isEmpty = state => (
    state.testSuite.selectedOptions.length === 0 &&
    state.measurement.selectedOptions.length === 0 &&
    state.bot.selectedOptions.length === 0 &&
    state.testCase.selectedOptions.length === 0);

  cp.ElementBase.register(ChartSection);

  return {
    ChartSection,
  };
});
