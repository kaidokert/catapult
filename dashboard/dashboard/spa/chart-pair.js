/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class ChartPair extends cp.ElementBase {
    hideOptions_(minimapLayout) {
      return this.$.minimap.showPlaceholder(
          (minimapLayout && minimapLayout.isLoading),
          (minimapLayout ? minimapLayout.lines : []));
    }

    onOptionsToggle_(event) {
      this.dispatch('showOptions', this.statePath, !this.isShowingOptions);
    }

    onMinimapBrush_(event) {
      if (event.detail.sourceEvent.detail.state === 'end') {
        this.dispatch('brushMinimap', this.statePath);
      }
      // TODO if isLinked dispatchEvent to ChromeperfApp
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

    onToggleNormalize_(event) {
      this.dispatch('toggleNormalize', this.statePath);
      // TODO if isLinked dispatchEvent to ChromeperfApp
    }

    onToggleCenter_(event) {
      this.dispatch('toggleCenter', this.statePath);
      // TODO if isLinked dispatchEvent to ChromeperfApp
    }

    onToggleZeroYAxis_(event) {
      this.dispatch('toggleZeroYAxis', this.statePath);
      // TODO if isLinked dispatchEvent to ChromeperfApp
    }

    onToggleFixedXAxis_(event) {
      this.dispatch('toggleFixedXAxis', this.statePath);
      // TODO if isLinked dispatchEvent to ChromeperfApp
    }

    onLineDescriptorsChange_(newLineDescriptors, oldLineDescriptors) {
      if (newLineDescriptors === oldLineDescriptors) return; // WTF, polymer
      this.dispatch('load', this.statePath);
    }
  }

  ChartPair.properties = {
    ...cp.ElementBase.statePathProperties('statePath', {
      chartLayout: {type: Object},
      fixedXAxis: {type: Boolean},
      isExpanded: {type: Boolean},
      isShowingOptions: {type: Boolean},
      lineDescriptors: {
        type: Array,
        observer: 'onLineDescriptorsChange_',
      },
      minimapLayout: {type: Object},
      normalize: {type: Boolean},
      center: {type: Boolean},
      zeroYAxis: {type: Boolean},
    }),
    xCursor: {
      type: Object,
      statePath: 'globalChartXCursor',
    },
  };

  ChartPair.actions = {
    toggleZeroYAxis: statePath => async(dispatch, getState) => {
      dispatch(cp.ElementBase.actions.toggleBoolean(
          `${statePath}.zeroYAxis`));
      dispatch(ChartPair.actions.load(statePath));
    },

    toggleFixedXAxis: statePath => async(dispatch, getState) => {
      dispatch(cp.ElementBase.actions.toggleBoolean(
          `${statePath}.fixedXAxis`));
      dispatch(ChartPair.actions.load(statePath));
    },

    toggleNormalize: statePath => async(dispatch, getState) => {
      dispatch(cp.ElementBase.actions.toggleBoolean(
          `${statePath}.normalize`));
      dispatch(ChartPair.actions.load(statePath));
    },

    toggleCenter: statePath => async(dispatch, getState) => {
      dispatch(cp.ElementBase.actions.toggleBoolean(
          `${statePath}.center`));
      dispatch(ChartPair.actions.load(statePath));
    },

    showOptions: (statePath, isShowingOptions) =>
      async(dispatch, getState) => {
        dispatch(cp.ElementBase.actions.updateObject(statePath, {
          isShowingOptions,
        }));
      },

    brushMinimap: statePath => async(dispatch, getState) => {
      dispatch({
        type: ChartPair.reducers.brushMinimap.typeName,
        statePath,
      });
      dispatch(ChartPair.actions.load(statePath));
    },

    brushChart: (statePath, brushIndex, value) =>
      async(dispatch, getState) => {
        dispatch(cp.ElementBase.actions.updateObject(
            `${statePath}.chartLayout.xAxis.brushes.${brushIndex}`,
            {xPct: value + '%'}));
      },

    load: statePath => async(dispatch, getState) => {
      const state = Polymer.Path.get(getState(), statePath);
      if (state.lineDescriptors.length === 0) {
        dispatch(cp.ElementBase.actions.updateObject(
            `${statePath}.minimapLayout`, {lineDescriptors: []}));
        dispatch(cp.ElementBase.actions.updateObject(
            `${statePath}.chartLayout`, {lineDescriptors: []}));
        return;
      }

      let minRevision = state.minRevision;
      let maxRevision = state.maxRevision;
      if (minRevision === undefined ||
          maxRevision === undefined) {
        const timeserieses = await dispatch(
            cp.ChartTimeseries.actions.fetchLineDescriptor(
                `${statePath}.minimapLayout`, state.lineDescriptors[0]));
        if (maxRevision === undefined) {
          maxRevision = tr.b.math.Statistics.max(timeserieses.map(ts => {
            const hist = ts.data[ts.data.length - 1];
            if (hist === undefined) return -Infinity;
            return cp.ChartTimeseries.getX(hist);
          }));
        }
        if (minRevision === undefined) {
          let closestTimestamp = Infinity;
          const minTimestampMs = new Date() - cp.MS_PER_MONTH;
          for (const timeseries of timeserieses) {
            const hist = tr.b.findClosestElementInSortedArray(
                timeseries.data,
                cp.ChartTimeseries.getTimestamp,
                minTimestampMs);
            if (hist) {
              const timestamp = cp.ChartTimeseries.getTimestamp(hist);
              if (Math.abs(timestamp - minTimestampMs) <
                  Math.abs(closestTimestamp - minTimestampMs)) {
                minRevision = cp.ChartTimeseries.getX(hist);
                closestTimestamp = timestamp;
              }
            }
          }
        }
        dispatch(cp.ElementBase.actions.updateObject(statePath, {
          minRevision, maxRevision,
        }));
      }

      dispatch(cp.ElementBase.actions.updateObject(
          `${statePath}.minimapLayout`, {
            lineDescriptors: [state.lineDescriptors[0]],
            brushRevisions: [minRevision, maxRevision],
            fixedXAxis: state.fixedXAxis,
          }));
      dispatch(cp.ElementBase.actions.updateObject(`${statePath}.chartLayout`, {
        lineDescriptors: state.lineDescriptors,
        minRevision,
        maxRevision,
        brushRevisions: [], // TODO routeParams
        fixedXAxis: state.fixedXAxis,
        normalize: state.normalize,
        center: state.center,
        zeroYAxis: state.zeroYAxis,
      }));
    },

    chartClick: statePath => async(dispatch, getState) => {
      dispatch({
        type: ChartPair.reducers.chartClick.typeName,
        statePath,
      });
    },

    dotClick: (statePath, ctrlKey, lineIndex, datumIndex) =>
      async(dispatch, getState) => {
        dispatch({
          type: ChartPair.reducers.dotClick.typeName,
          statePath,
          ctrlKey,
          lineIndex,
          datumIndex,
        });

        dispatch(cp.ElementBase.actions.updateObject(
            statePath, {isLoading: true}));

        const section = Polymer.Path.get(getState(), statePath);

        dispatch({
          type: ChartPair.reducers.receiveHistograms.typeName,
          statePath,
          histograms: await cp.dummyHistograms(section),
        });
      },

    dotMouseOver: (statePath, lineIndex) => async(dispatch, getState) => {
    },

    dotMouseOut: (statePath, lineIndex) => async(dispatch, getState) => {
    },
  };

  ChartPair.reducers = {
    receiveTestSuites: (state, action, rootState) => {
      if (rootState.userEmail &&
          (action.options.length < state.testSuite.options.length)) {
        // The loadTestSuites() in actions.connected might race with the
        // loadTestSuites() in actions.authChange. If the internal test suites
        // load first then the public test suites load, ignore the public test
        // suites. If the user signs out, then userEmail will become
        // the empty string, so load the public test suites.
        return state;
      }
      const testSuite = {
        ...state.testSuite,
        options: action.options,
        label: `Test suites (${action.count})`,
      };
      return {...state, testSuite};
    },

    brushMinimap: (state, action, rootState) => {
      const range = new tr.b.math.Range();
      for (const brush of state.minimapLayout.xAxis.brushes) {
        const index = tr.b.findLowIndexInSortedArray(
            state.minimapLayout.lines[0].data,
            datum => parseFloat(datum.xPct),
            parseFloat(brush.xPct));
        const datum = state.minimapLayout.lines[0].data[index];
        range.addValue(datum.x);
      }
      const minRevision = range.min;
      const maxRevision = range.max;
      return {
        ...state,
        minRevision,
        maxRevision,
        chartLayout: {
          ...state.chartLayout,
          minRevision,
          maxRevision,
        },
      };
    },

    updateLegendColors: (state, action, rootState) => {
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
    },

    buildLegend: (state, action, rootState) => {
      const legend = ChartPair.buildLegend(
          ChartPair.parameterMatrix(state));
      return {...state, legend};
    },

    updateTitle: (state, action, rootState) => {
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
    },

    receiveDescriptor: (state, action, rootState) => {
      const measurement = {
        ...state.measurement,
        optionValues: action.descriptor.measurements,
        options: cp.OptionGroup.groupValues(action.descriptor.measurements),
        label: `Measurements (${action.descriptor.measurements.size})`,
      };

      const botOptions = cp.OptionGroup.groupValues(action.descriptor.bots);
      const bot = {
        ...state.bot,
        optionValues: action.descriptor.bots,
        options: botOptions.map(option => {
          return {...option, isExpanded: true};
        }),
        label: `Bots (${action.descriptor.bots.size})`,
      };

      const testCaseOptions = [];
      if (action.descriptor.testCases.size) {
        testCaseOptions.push({
          label: `All ${action.descriptor.testCases.size} test cases`,
          isExpanded: true,
          value: '*',
          options: cp.OptionGroup.groupValues(action.descriptor.testCases),
        });
      }

      const testCase = {
        ...state.testCase,
        optionValues: action.descriptor.testCases,
        options: testCaseOptions,
        label: `Test cases (${action.descriptor.testCases.size})`,
        tags: {
          ...state.testCase.tags,
          options: cp.OptionGroup.groupValues(action.descriptor.testCaseTags),
        },
      };

      return {...state, measurement, bot, testCase};
    },

    finalizeParameters: (state, action, rootState) => {
      const measurement = {
        ...state.measurement,
        selectedOptions: state.measurement.selectedOptions.filter(m =>
          state.measurement.optionValues.has(m)),
      };

      const bot = {...state.bot};

      if (bot.selectedOptions.length === 0 ||
          ((bot.selectedOptions.length === 1) &&
          (bot.selectedOptions[0] === '*'))) {
        bot.selectedOptions = [...bot.optionValues];
      } else {
        bot.selectedOptions = bot.selectedOptions.filter(b =>
          bot.optionValues.has(b));
      }

      const testCase = {
        ...state.testCase,
        selectedOptions: state.testCase.selectedOptions.filter(t =>
          state.testCase.optionValues.has(t)),
      };

      return {...state, measurement, bot, testCase};
    },

    receiveHistograms: (state, action, rootState) => {
      return {
        ...state,
        isLoading: false,
        histograms: action.histograms,
      };
    },

    chartClick: (state, action, rootState) => {
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
    },

    dotClick: (state, action, rootState) => {
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
    },
  };

  ChartPair.newState = options => {
    const chartState = cp.ChartTimeseries.newState();
    return {
      isExpanded: true,
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
    };
  };

  cp.ElementBase.register(ChartPair);

  return {
    ChartPair,
  };
});
