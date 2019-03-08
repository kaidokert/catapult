/* Copyright 2019 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class SparklineCompound extends cp.ElementBase {
    async onRelatedTabClick_(event) {
      this.dispatch('selectRelatedTab', this.statePath, event.model.tab.name);
    }

    hideTile_(sparkline) {
      return !sparkline.isLoading && this.isEmpty_(sparkline.layout.lines);
    }

    async onSparklineClick_(event) {
      this.dispatchEvent(new CustomEvent('new-chart', {
        bubbles: true,
        composed: true,
        detail: {options: event.model.sparkline.chartOptions},
      }));
    }

    observeRevisions_() {
      this.dispatch({
        type: SparklineCompound.reducers.updateSparklineRevisions.name,
        statePath: this.statePath,
      });
    }

    observeCursor_(cursorRevision, cursorScalar) {
      this.dispatch({
        type: SparklineCompound.reducers.setCursors.name,
        statePath: this.statePath,
      });
    }
  }

  SparklineCompound.State = {
    relatedTabs: options => [],
    selectedRelatedTabName: options => options.selectedRelatedTabName || '',
    cursorRevision: options => 0,
    cursorScalar: options => undefined,
    minRevision: options => options.minRevision,
    maxRevision: options => options.maxRevision,
  };

  SparklineCompound.buildState = options => cp.buildState(
      SparklineCompound.State, options);
  SparklineCompound.properties = cp.buildProperties(
      'state', SparklineCompound.State);
  SparklineCompound.observers = [
    'observeRevisions_(minRevision, maxRevision)',
    'observeCursor_(cursorRevision, cursorScalar)',
  ];

  SparklineCompound.actions = {
    selectRelatedTab: (statePath, selectedRelatedTabName) =>
      async(dispatch, getState) => {
        const state = Polymer.Path.get(getState(), statePath);
        if (selectedRelatedTabName === state.selectedRelatedTabName) {
          selectedRelatedTabName = '';
        }

        const selectedRelatedTabIndex = state.relatedTabs.findIndex(tab =>
          tab.name === selectedRelatedTabName);
        if (selectedRelatedTabIndex >= 0 &&
            state.relatedTabs[selectedRelatedTabIndex].renderedSparklines ===
            undefined) {
          const path = `${statePath}.relatedTabs.${selectedRelatedTabIndex}`;
          const relatedTab = state.relatedTabs[selectedRelatedTabIndex];
          dispatch(Redux.UPDATE(path, {
            renderedSparklines: relatedTab.sparklines,
          }));
        }

        dispatch(Redux.UPDATE(statePath, {selectedRelatedTabName}));
      },
  };

  function createSparkline(name, sparkLayout, revisions, matrix) {
    const lineDescriptors = cp.ChartSection.createLineDescriptors(matrix);
    if (lineDescriptors.length === 1) {
      lineDescriptors.push({
        ...lineDescriptors[0],
        buildType: 'ref',
      });
    }

    return {
      name: cp.breakWords(name),
      chartOptions: {
        parameters: cp.ChartSection.parametersFromMatrix(matrix),
        ...revisions,
      },
      layout: {
        ...sparkLayout,
        ...revisions,
        lineDescriptors,
      },
    };
  }

  SparklineCompound.reducers = {
    buildRelatedTabs: (state, action, rootState) => {
      const relatedTabs = [];
      const parameterMatrix = cp.ChartSection.parameterMatrix(state);
      const revisions = {
        minRevision: state.minRevision,
        maxRevision: state.maxRevision,
        zeroYAxis: state.zeroYAxis,
        fixedXAxis: state.fixedXAxis,
        mode: state.mode,
      };

      const sparkLayout = cp.ChartTimeseries.buildState({});
      sparkLayout.yAxis.generateTicks = false;
      sparkLayout.xAxis.generateTicks = false;
      sparkLayout.graphHeight = 100;

      function maybeAddParameterTab(propertyName, tabName, matrixName) {
        let options = state.descriptor[propertyName].selectedOptions;
        if (options.length === 0) {
          // If zero suites or bots are selected, then buildRelatedTabs
          // wouldn't be called. If zero cases are selected, then build
          // sparklines for all available cases.
          options = []; // Do not append to [propertyName].selectedOptions!
          for (const option of state.descriptor[propertyName].options) {
            options.push(...cp.OptionGroup.getValuesFromOption(option));
          }
          if (options.length === 0) return;
        } else if (options.length === 1 ||
                   !state.descriptor[propertyName].isAggregated) {
          return;
        }
        relatedTabs.push({
          name: tabName,
          sparklines: options.map(option =>
            createSparkline(option, sparkLayout, revisions, {
              ...parameterMatrix,
              [matrixName]: [[option]],
            })),
        });
      }
      maybeAddParameterTab('suite', 'Test suites', 'suiteses');

      const rails = ['Response', 'Animation', 'Idle', 'Load', 'Startup'];

      const measurements = state.descriptor.measurement.selectedOptions;
      // TODO Use RelatedNameMaps instead of these hard-coded strings.
      const processSparklines = [];
      const componentSparklines = [];
      const railSparklines = [];

      if (state.descriptor.suite.selectedOptions.filter(
          ts => ts.startsWith('v8:browsing')).length) {
        if (measurements.filter(
            m => (!rails.includes(m.split('_')[0]) &&
                  !m.startsWith('memory:'))).length) {
          for (const rail of rails) {
            railSparklines.push(createSparkline(
                rail, sparkLayout, revisions, {
                  ...parameterMatrix,
                  measurements: measurements.map(m => rail + '_' + m),
                }));
          }
        }

        if (measurements.filter(
            m => (m.startsWith('Total:') &&
                  ['count', 'duration'].includes(m.split(':')[1]))).length) {
          for (const relatedName of ['Blink C++', 'V8-Only']) {
            componentSparklines.push(createSparkline(
                relatedName, sparkLayout, revisions, {
                  ...parameterMatrix,
                  measurements: measurements.map(
                      m => relatedName + ':' + m.split(':')[1]),
                }));
          }
        }

        const v8Only = measurements.filter(m => m.includes('V8-Only:'));
        if (v8Only.length) {
          for (const relatedName of [
            'API',
            'Compile',
            'Compile-Background',
            'GC',
            'IC',
            'JavaScript',
            'Optimize',
            'Parse',
            'Parse-Background',
            'V8 C++',
          ]) {
            componentSparklines.push(createSparkline(
                relatedName, sparkLayout, revisions, {
                  ...parameterMatrix,
                  measurements: v8Only.map(
                      m => m.replace('V8-Only', relatedName)),
                }));
          }
        }

        const gc = measurements.filter(m => m.includes('GC:'));
        if (gc.length) {
          for (const relatedName of [
            'MajorMC', 'Marking', 'MinorMC', 'Other', 'Scavenger', 'Sweeping',
          ]) {
            componentSparklines.push(createSparkline(
                relatedName, sparkLayout, revisions, {
                  ...parameterMatrix,
                  measurements: gc.map(
                      m => m.replace('GC', 'GC-Background-' + relatedName)),
                }));
          }
        }
      }

      for (const measurement of state.descriptor.measurement.selectedOptions) {
        const measurementAvg = measurement + '_avg';
        if (d.MEMORY_PROCESS_RELATED_NAMES.has(measurementAvg)) {
          for (let relatedMeasurement of d.MEMORY_PROCESS_RELATED_NAMES.get(
              measurementAvg)) {
            if (relatedMeasurement.endsWith('_avg')) {
              relatedMeasurement = relatedMeasurement.slice(0, -4);
            }
            if (relatedMeasurement === measurement) continue;
            const relatedParts = relatedMeasurement.split(':');
            processSparklines.push(createSparkline(
                relatedParts[2], sparkLayout, revisions, {
                  ...parameterMatrix,
                  measurements: [relatedMeasurement],
                }));
          }
        }
        if (d.MEMORY_COMPONENT_RELATED_NAMES.has(measurementAvg)) {
          for (let relatedMeasurement of d.MEMORY_COMPONENT_RELATED_NAMES.get(
              measurementAvg)) {
            if (relatedMeasurement.endsWith('_avg')) {
              relatedMeasurement = relatedMeasurement.slice(0, -4);
            }
            if (relatedMeasurement === measurement) continue;
            const relatedParts = relatedMeasurement.split(':');
            const name = relatedParts.slice(
                4, relatedParts.length - 1).join(':');
            componentSparklines.push(createSparkline(
                name, sparkLayout, revisions, {
                  ...parameterMatrix,
                  measurements: [relatedMeasurement],
                }));
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
      if (railSparklines.length) {
        relatedTabs.push({
          name: 'RAILS',
          sparklines: railSparklines,
        });
      }

      maybeAddParameterTab('bot', 'Bots', 'botses');
      maybeAddParameterTab('case', 'Test cases', 'caseses');

      if (state.selectedRelatedTabName) {
        const selectedRelatedTabIndex = relatedTabs.findIndex(tab =>
          tab.name === state.selectedRelatedTabName);
        if (selectedRelatedTabIndex >= 0) {
          relatedTabs[selectedRelatedTabIndex].renderedSparklines =
            relatedTabs[selectedRelatedTabIndex].sparklines;
        }
      }

      return {...state, relatedTabs};
    },

    updateSparklineRevisions: (state, action, rootState) => {
      if (!state || !state.relatedTabs) return state;
      function updateSparkline(sparkline) {
        return {
          ...sparkline,
          layout: {
            ...sparkline.layout,
            minRevision: state.minRevision,
            maxRevision: state.maxRevision,
          },
        };
      }
      return {
        ...state,
        relatedTabs: state.relatedTabs.map(tab => {
          let renderedSparklines;
          if (tab.renderedSparklines) {
            renderedSparklines = tab.renderedSparklines.map(updateSparkline);
          }
          return {
            ...tab,
            sparklines: tab.sparklines.map(updateSparkline),
            renderedSparklines,
          };
        }),
      };
    },

    setCursors: (state, action, rootState) => {
      if (!state.cursorRevision || !state.cursorScalar || !state.relatedTabs) {
        return state;
      }

      // Copy state.cursorScalar/cursorRevision to all renderedSparklines in all
      // tabs.
      const relatedTabs = state.relatedTabs.map(tab => {
        if (!tab.renderedSparklines) return tab;

        const renderedSparklines = tab.renderedSparklines.map(sparkline => {
          if (sparkline.layout.xAxis.range.isEmpty ||
              !sparkline.layout.yAxis) {
            return sparkline;
          }

          let xPct;
          if (state.fixedXAxis) {
            let nearestDatum;
            for (const line of sparkline.layout.lines) {
              if (!line.data || !line.data.length) continue;
              const datum = tr.b.findClosestElementInSortedArray(
                  line.data, d => d.x, state.cursorRevision);
              if (!nearestDatum ||
                  (Math.abs(state.cursorRevision - datum.x) <
                  Math.abs(state.cursorRevision - nearestDatum.x))) {
                nearestDatum = datum;
              }
            }
            if (nearestDatum) xPct = nearestDatum.xPct + '%';
          } else {
            xPct = sparkline.layout.xAxis.range.normalize(
                state.cursorRevision) * 100 + '%';
          }

          let yPct;
          let yRange;
          if (state.mode === 'normalizeUnit') {
            if (sparkline.layout.yAxis.rangeForUnitName) {
              yRange = sparkline.layout.yAxis.rangeForUnitName.get(
                  state.cursorScalar.unit.baseUnit.unitName);
            }
          } else if (sparkline.layout.lines.length === 1) {
            yRange = sparkline.layout.lines[0].yRange;
          }
          if (yRange) {
            yPct = (1 - yRange.normalize(
                state.cursorScalar.value)) * 100 + '%';
          }

          return {
            ...sparkline,
            layout: {
              ...sparkline.layout,
              xAxis: {
                ...sparkline.layout.xAxis,
                cursor: {pct: xPct},
              },
              yAxis: {
                ...sparkline.layout.yAxis,
                cursor: {pct: yPct},
              },
            },
          };
        });
        return {...tab, renderedSparklines};
      });
      return {...state, relatedTabs};
    },
  };

  cp.ElementBase.register(SparklineCompound);

  return {SparklineCompound};
});
