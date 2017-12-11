/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class ChartSection extends cp.Element {
    static get is() { return 'chart-section'; }

    static get properties() {
      return cp.sectionProperties({
        chartLayout: {type: Object},
        histograms: {type: Object},
        isLoading: {type: Boolean},
        isShowingOptions: {type: Boolean},
        minimapLayout: {type: Object},
        onlyChart: {type: Boolean},
        relatedTabs: {type: Array},
        selectedRelatedTabIndex: {type: Number},
        showHistogramsControls: {type: Boolean},
        testPathComponents: {type: Array},
        title: {type: String},
      });
    }

    async ready() {
      super.ready();
      this.scrollIntoView(true);
    }

    closeSection_() {
      this.dispatch(cp.ChromeperfApp.closeSection(this.sectionId));
    }

    onTitleKeyup_(e) {
      this.dispatch(ChartSection.setTitle(this.sectionId, e.target.value));
    }

    static setTitle(sectionId, title) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'chart-section.setTitle',
          sectionId,
          title,
        });
      };
    }

    toggleOptions_() {
      this.dispatch(ChartSection.showOptions(
          this.sectionId, !this.isShowingOptions));
    }

    static showOptions(sectionId, showOptions) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'chart-section.showOptions',
          sectionId,
          showOptions,
        });
      };
    }

    onMinimapBrush_(e) {
      this.dispatch(ChartSection.brushMinimap(
          this.sectionId, e.detail.brushIndex, e.detail.value));
    }

    onBrush_(e) {
      this.dispatch(ChartSection.brushChart(
          this.sectionId, e.detail.brushIndex, e.detail.value));
    }

    static brushMinimap(sectionId, brushIndex, value) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'chart-section.brushMinimap',
          sectionId,
          brushIndex,
          value,
        });
      };
    }

    static brushChart(sectionId, brushIndex, value) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'chart-section.brushChart',
          sectionId,
          brushIndex,
          value,
        });
      };
    }

    onDotClick_(e) {
      // TODO
    }

    onDotMouseOver_(e) {
      // TODO
    }

    onDotMouseOut_(e) {
      // TODO
    }

    toggleChartOnly_() {
      this.dispatch(ChartSection.toggleChartOnly(this.sectionId));
    }

    static toggleChartOnly(sectionId) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'chart-section.toggleChartOnly',
          sectionId,
        });
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

    static maybeLoadTimeseries(sectionId) {
      return async (dispatch, getState) => {
        // If the first 3 components are filled, then load the timeseries.
        const section = getState().sectionsById[sectionId];
        const components = section.testPathComponents;
        if (components[0].selectedOptions.length &&
            components[1].selectedOptions.length &&
            components[2].selectedOptions.length) {
          dispatch(ChartSection.loadTimeseries(sectionId));
        } else {
          dispatch(ChartSection.clearTimeseries(sectionId));
        }
      };
    }

    static clearTimeseries(sectionId) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'chart-section.clearTimeseries',
          sectionId,
        });
      };
    }

    static loadTimeseries(sectionId) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'chart-section.startLoadingTimeseries',
          sectionId,
        });
        await tr.b.timeout(500);

        const section = getState().sectionsById[sectionId];
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

        // TODO fetch rows and histograms from backend via cache

        // TODO use brightnessRange when > 15
        const colors = tr.b.generateFixedColorScheme(
            testPathCartesianProduct.length, {hueOffset: 0.64});

        // TODO LineChart.layout()

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

        const minimapSequences = [{
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
          minimapSequences[0].data.push(datum);
        }

        const chartSequences = [];
        for (const color of colors) {
          const y0 = 1 + parseInt(98 * Math.random());
          const sequence = {
            color: '' + color,
            dotColor: '' + color,
            data: [{x: 1, y: y0}],
            strokeWidth: 1,
          };
          chartSequences.push(sequence);
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

        const histograms = new tr.v.HistogramSet();
        for (let i = 0; i < testPathCartesianProduct.length; ++i) {
          const testPath = testPathCartesianProduct[i];
          function inArray(x) {
            return x instanceof Array ? x : [x];
          }
          let stories = inArray(testPath[3]);
          if (section.testPathComponents[3].selectedOptions.length === 0) {
            stories = [
              'load:news:cnn',
              'load:news:nytimes',
              'load:news:qq',
            ];
          }
          histograms.createHistogram(
              testPath[2],
              tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
              [Math.random() * 1e9], {
                diagnostics: new Map([
                  [
                    tr.v.d.RESERVED_NAMES.BENCHMARKS,
                    new tr.v.d.GenericSet(inArray(testPath[0])),
                  ],
                  [
                    tr.v.d.RESERVED_NAMES.BOTS,
                    new tr.v.d.GenericSet(inArray(testPath[1])),
                  ],
                  [
                    tr.v.d.RESERVED_NAMES.STORIES,
                    new tr.v.d.GenericSet(stories),
                  ],
                  [
                    tr.v.d.RESERVED_NAMES.LABELS,
                    new tr.v.d.GenericSet([tr.b.formatDate(new Date())]),
                  ],
                  [
                    tr.v.d.RESERVED_NAMES.NAME_COLORS,
                    new tr.v.d.GenericSet([colors[i].toString()]),
                  ],
                ]),
              });
        }

        dispatch({
          type: 'chart-section.layoutChart',
          sectionId,
          title,

          minimapLayout: {
            height: minimapHeight,
            yAxisWidth: maxYAxisTickWidth,
            xAxisHeight: textHeight,
            graphHeight: minimapHeight - textHeight - 15,
            dotRadius: 0,
            dotCursor: '',
            sequences: minimapSequences,
            xAxisTicks: minimapXAxisTicks,
            showXAxisTickLines: true,
            fhowYAxisTickLines: false,
            brushes: [60, 90],
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
            sequences: chartSequences,
            yAxisTicks: chartYAxisTicks,
            xAxisTicks: chartXAxisTicks,
            brushes: [95, 100],
          },

          histograms,
        });

        // TODO fetch RelatedNameMaps

        dispatch({
          type: 'chart-section.layoutRelatedTabs',
          sectionId,

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
                    sequences: chartSequences,
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
                    sequences: chartSequences,
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
                    sequences: chartSequences,
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
                    sequences: chartSequences,
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
                    sequences: chartSequences,
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
                    sequences: chartSequences,
                    yAxisTicks: [],
                    xAxisTicks: [],
                    brushes: [],
                  },
                },
              ],
            },
          ],
        });
      };
    }

    onSelectRelatedTab_(e) {
      this.dispatch(ChartSection.selectRelatedTab(
          this.sectionId, e.target.selected));
    }

    static selectRelatedTab(sectionId, selectedRelatedTabIndex) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'chart-section.selectRelatedTab',
          sectionId,
          selectedRelatedTabIndex,
        });
      };
    }

    onSparklineTap_(e) {
      // TODO
    }

    static clearAllFocused(sectionState) {
      return {
        ...sectionState,
        testPathComponents: sectionState.testPathComponents.map(component => {
          return {...component, isFocused: false};
        }),
      };
    }
  }
  customElements.define(ChartSection.is, ChartSection);

  ChartSection.NEW_STATE = {
    isLoading: false,
    onlyChart: false,
    title: '',
    isTitleCustom: false,
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
          'nexus5X',
          'nexus5',
          'mac',
          'win',
          'linux',
        ],
      },
      {
        placeholder: 'Measurement (500)',
        canAggregate: false,
        isFocused: false,
        inputValue: '',
        selectedOptions: [],
        multipleSelectedOptions: false,
        options: [
          'PSS',
          'power',
          'TTFMP',
          'TTI',
        ],
      },
      {
        placeholder: 'Stories (100)',
        canAggregate: true,
        isFocused: false,
        inputValue: '',
        selectedOptions: [],
        multipleSelectedOptions: false,
        options: [
          'load:news:cnn',
          'load:news:nytimes',
          'load:news:qq',
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

  cp.sectionReducer('chart-section.showOptions', (state, action, section) => {
    return {
      isShowingOptions: action.showOptions,
    };
  });

  cp.sectionReducer('chart-section.setTitle', (state, action, section) => {
    return {
      title: action.title,
      isTitleCustom: true,
    };
  });

  cp.sectionReducer('chart-section.selectRelatedTab',
      (state, action, section) => {
        return {
          selectedRelatedTabIndex: action.selectedRelatedTabIndex,
        };
      });

  cp.sectionReducer('chart-section.layoutChart', (state, action, section) => {
    return {
      isLoading: false,
      title: action.title,
      minimapLayout: action.minimapLayout,
      chartLayout: action.chartLayout,
      histograms: action.histograms,
    };
  });

  cp.sectionReducer('chart-section.toggleChartOnly',
      (state, action, section) => {
        return {
          onlyChart: !section.onlyChart,
        };
      });

  cp.sectionReducer('chart-section.clearTimeseries',
      (state, action, section) => {
        return {
          chartLayout: undefined,
          minimapLayout: undefined,
          histograms: undefined,
        };
      });

  cp.sectionReducer('chart-section.startLoadingTimeseries',
      (state, action, section) => {
        return {
          isLoading: true,
        };
      });

  cp.sectionReducer('chart-section.layoutRelatedTabs',
      (state, action, section) => {
        return {relatedTabs: action.relatedTabs};
      });

  cp.sectionReducer('chart-section.brushChart', (state, action, section) => {
    let brushes = section.chartLayout.brushes;
    brushes = brushes.slice(0, action.brushIndex).concat([action.value
    ]).concat(brushes.slice(action.brushIndex + 1));
    return {chartLayout: {...section.chartLayout, brushes}};
  });

  cp.sectionReducer('chart-section.brushMinimap', (state, action, section) => {
    let brushes = section.minimapLayout.brushes;
    brushes = brushes.slice(0, action.brushIndex).concat([action.value
    ]).concat(brushes.slice(action.brushIndex + 1));
    return {minimapLayout: {...section.minimapLayout, brushes}};
  });

  return {
    ChartSection,
  };
});
