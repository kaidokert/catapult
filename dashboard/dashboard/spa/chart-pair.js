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
      if (event.detail.sourceEvent.detail.state !== 'end') return;
      this.dispatch('brushMinimap', this.statePath);
      if (this.isLinked) {
        this.dispatch('updateLinkedRevisions', this.linkedStatePath,
            this.minRevision, this.maxRevision);
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

    onToggleLinked_(event) {
      this.dispatch('toggleLinked', this.statePath, this.linkedStatePath);
    }

    onToggleZeroYAxis_(event) {
      this.dispatch('toggleZeroYAxis', this.statePath);
      if (this.isLinked) {
        this.dispatch('toggleLinkedZeroYAxis', this.linkedStatePath);
      }
    }

    onToggleFixedXAxis_(event) {
      this.dispatch('toggleFixedXAxis', this.statePath);
      if (this.isLinked) {
        this.dispatch('toggleLinkedFixedXAxis', this.linkedStatePath);
      }
    }

    observeLineDescriptors_(newLineDescriptors, oldLineDescriptors) {
      if (newLineDescriptors === oldLineDescriptors) return; // WTF, polymer
      this.dispatch('load', this.statePath);
    }

    observeLinkedCursorRevision_() {
      if (!this.isLinked) return;
      // TODO
    }

    observeLinkedRevisions_() {
      if (!this.isLinked) return;
      this.dispatch('updateRevisions', this.statePath,
          this.linkedMinRevision, this.linkedMaxRevision);
    }

    observeLinkedMode_() {
      if (!this.isLinked) return;
      if (this.mode === this.linkedMode) return;
      this.dispatch('mode', this.statePath, this.linkedMode);
    }

    observeLinkedZeroYAxis_() {
      if (!this.isLinked) return;
      if (this.zeroYAxis === this.linkedZeroYAxis) return;
      this.dispatch('toggleZeroYAxis', this.statePath);
    }

    observeLinkedFixedXAxis_() {
      if (!this.isLinked) return;
      if (this.fixedXAxis === this.linkedFixedXAxis) return;
      this.dispatch('toggleFixedXAxis', this.statePath);
    }

    onModeChange_(event) {
      this.dispatch('mode', this.statePath, event.detail.value);
      if (this.isLinked) {
        this.dispatch('linkedMode', this.linkedStatePath, event.detail.value);
      }
    }
  }

  ChartPair.properties = {
    ...cp.ElementBase.statePathProperties('statePath', {
      lineDescriptors: {
        type: Array,
        observer: 'observeLineDescriptors_',
      },
      isExpanded: {type: Boolean},
      minimapLayout: {type: Object},
      chartLayout: {type: Object},

      isShowingOptions: {type: Boolean},
      isLinked: {type: Boolean},
      cursorRevision: {type: Number },
      minRevision: {type: Number},
      maxRevision: {type: Number},
      mode: {type: String},
      zeroYAxis: {type: Boolean},
      fixedXAxis: {type: Boolean},
    }),
    ...cp.ElementBase.statePathProperties('linkedStatePath', {
      linkedCursorRevision: {
        type: Number,
        observer: 'observeLinkedCursorRevision_',
      },
      linkedMinRevision: {
        type: Number,
        observer: 'observeLinkedRevisions_',
      },
      linkedMaxRevision: {
        type: Number,
        observer: 'observeLinkedRevisions_',
      },
      linkedMode: {
        type: String,
        observer: 'observeLinkedMode_',
      },
      linkedZeroYAxis: {
        type: Boolean,
        observer: 'observeLinkedZeroYAxis_',
      },
      linkedFixedXAxis: {
        type: Boolean,
        observer: 'observeLinkedFixedXAxis_',
      },
    }),
  };

  ChartPair.actions = {
    updateRevisions: (statePath, minRevision, maxRevision) =>
      async(dispatch, getState) => {
        cp.ElementBase.actions.updateObject(statePath, {
          minRevision, maxRevision,
        })(dispatch, getState);
        ChartPair.actions.load(statePath)(dispatch, getState);
      },

    updateLinkedRevisions: (
        linkedStatePath, linkedMinRevision, linkedMaxRevision) =>
      async(dispatch, getState) => {
        cp.ElementBase.actions.updateObject(linkedStatePath, {
          linkedMinRevision, linkedMaxRevision,
        })(dispatch, getState);
      },

    toggleLinked: (statePath, linkedStatePath) => async(dispatch, getState) => {
      const linkedState = Polymer.Path.get(getState(), linkedStatePath);
      cp.ElementBase.actions.updateObject(statePath, {
        isLinked: true,
        cursorRevision: linkedState.linkedCursorRevision,
        minRevision: linkedState.linkedMinRevision,
        maxRevision: linkedState.linkedMaxRevision,
        mode: linkedState.mode,
        zeroYAxis: linkedState.linkedZeroYAxis,
        fixedXAxis: linkedState.linkedFixedXAxis,
      })(dispatch, getState);
      ChartPair.actions.load(statePath)(dispatch, getState);
    },

    toggleZeroYAxis: statePath => async(dispatch, getState) => {
      cp.ElementBase.actions.toggleBoolean(`${statePath}.zeroYAxis`)(
          dispatch, getState);
      ChartPair.actions.load(statePath)(dispatch, getState);
    },

    toggleLinkedZeroYAxis: linkedStatePath => async(dispatch, getState) => {
      cp.ElementBase.actions.toggleBoolean(
          `${linkedStatePath}.linkedZeroYAxis`)(dispatch, getState);
    },

    toggleFixedXAxis: statePath => async(dispatch, getState) => {
      cp.ElementBase.actions.toggleBoolean(
          `${statePath}.fixedXAxis`)(dispatch, getState);
      ChartPair.actions.load(statePath)(dispatch, getState);
    },

    toggleLinkedFixedXAxis: linkedStatePath => async(dispatch, getState) => {
      cp.ElementBase.actions.toggleBoolean(
          `${linkedStatePath}.linkedFixedXAxis`)(dispatch, getState);
    },

    showOptions: (statePath, isShowingOptions) =>
      async(dispatch, getState) => {
        cp.ElementBase.actions.updateObject(statePath, {
          isShowingOptions,
        })(dispatch, getState);
      },

    brushMinimap: statePath => async(dispatch, getState) => {
      dispatch({
        type: ChartPair.reducers.brushMinimap.typeName,
        statePath,
      });
      ChartPair.actions.load(statePath)(dispatch, getState);
    },

    brushChart: (statePath, brushIndex, value) =>
      async(dispatch, getState) => {
        const path = `${statePath}.chartLayout.xAxis.brushes.${brushIndex}`;
        cp.ElementBase.actions.updateObject(path, {
          xPct: value + '%',
        })(dispatch, getState);
      },

    load: statePath => async(dispatch, getState) => {
      const state = Polymer.Path.get(getState(), statePath);
      if (!state || !state.lineDescriptors ||
          state.lineDescriptors.length === 0) {
        cp.ElementBase.actions.updateObject(`${statePath}.minimapLayout`, {
          lineDescriptors: []
        })(dispatch, getState);
        cp.ElementBase.actions.updateObject(`${statePath}.chartLayout`, {
          lineDescriptors: []
        })(dispatch, getState);
        return;
      }

      const {firstRealLineDescriptor, timeserieses} =
        await ChartPair.findFirstRealLineDescriptor(
            state.lineDescriptors, dispatch, `${statePath}.minimapLayout`);

      let firstRevision = tr.b.math.Statistics.min(timeserieses.map(ts => {
        if (!ts || !ts.data) return Infinity;
        const hist = ts.data[0];
        if (hist === undefined) return Infinity;
        return cp.ChartTimeseries.getX(hist);
      }));
      if (firstRevision === Infinity) {
        firstRevision = undefined;
      }

      let lastRevision = tr.b.math.Statistics.max(timeserieses.map(ts => {
        if (!ts || !ts.data) return -Infinity;
        const hist = ts.data[ts.data.length - 1];
        if (hist === undefined) return -Infinity;
        return cp.ChartTimeseries.getX(hist);
      }));
      if (lastRevision === -Infinity) {
        lastRevision = undefined;
      }

      let minRevision = state.minRevision;
      if (minRevision === undefined ||
          minRevision >= lastRevision) {
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

      let maxRevision = state.maxRevision;
      if (maxRevision === undefined ||
          maxRevision <= firstRevision) {
        maxRevision = lastRevision;
        cp.ElementBase.actions.updateObject(statePath, {
          maxRevision,
        })(dispatch, getState);
      }

      const minimapLineDescriptors = [];
      if (firstRealLineDescriptor) {
        minimapLineDescriptors.push({
          ...firstRealLineDescriptor,
          icons: [],
        });
      }

      cp.ElementBase.actions.updateObject(`${statePath}.minimapLayout`, {
        lineDescriptors: minimapLineDescriptors,
        brushRevisions: [minRevision, maxRevision],
        fixedXAxis: state.fixedXAxis,
      })(dispatch, getState);

      let lineDescriptors = state.lineDescriptors;
      if (lineDescriptors.length === 1) {
        lineDescriptors = [...lineDescriptors];
        lineDescriptors.push({
          ...state.lineDescriptors[0],
          buildType: 'ref',
          icons: [],
        });
      }

      cp.ElementBase.actions.updateObject(`${statePath}.chartLayout`, {
        lineDescriptors,
        minRevision,
        maxRevision,
        brushRevisions: [],
        fixedXAxis: state.fixedXAxis,
        mode: state.mode,
        zeroYAxis: state.zeroYAxis,
      })(dispatch, getState);
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
      },

    dotMouseOver: (statePath, lineIndex) => async(dispatch, getState) => {
    },

    dotMouseOut: (statePath, lineIndex) => async(dispatch, getState) => {
    },

    mode: (statePath, mode) => async(dispatch, getState) => {
      cp.ElementBase.actions.updateObject(statePath, {
        mode,
      })(dispatch, getState);
      ChartPair.actions.load(statePath)(dispatch, getState);
    },

    linkedMode: (linkedStatePath, linkedMode) => async(dispatch, getState) => {
      cp.ElementBase.actions.updateObject(linkedStatePath, {
        linkedMode,
      })(dispatch, getState);
    }
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
      if (state.minimapLayout.lines.length === 0) return state;
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
      if (!sequence || !sequence.data[action.datumIndex]) return state;
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
      isLinked: true,
      isExpanded: true,
      mode: options.mode || 'normalizeUnit',
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

  ChartPair.findFirstRealLineDescriptor = async(
    lineDescriptors, dispatch, refStatePath) => {
    for (const firstRealLineDescriptor of lineDescriptors) {
      const timeserieses = await dispatch(
          cp.ChartTimeseries.actions.fetchLineDescriptor(
              refStatePath, firstRealLineDescriptor));
      for (const timeseries of timeserieses) {
        if (timeseries && timeseries.data.length) {
          return {firstRealLineDescriptor, timeserieses};
        }
      }
    }
    return {timeserieses: []};
  };

  cp.ElementBase.register(ChartPair);

  return {
    ChartPair,
  };
});
