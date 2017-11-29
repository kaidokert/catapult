/*
Copyright 2017 The Chromium Authors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be
found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class ChartSection extends cp.Element {
    static get is() { return 'chart-section'; }

    static get properties() {
      return cp.sectionProperties({
        isLoading: {type: Boolean},
        histograms: {type: tr.v.HistogramSet},
        onlyChart: {type: Boolean},
        minimapLayout: {type: Object},
        chartLayout: {type: Object},
        testPathComponents: {type: Array},
        testSuiteDescription: {type: String},
      });
    }

    async ready() {
      super.ready();
      this.scrollIntoView(true);
      this.dispatch(cp.ChromeperfApp.updateSectionWidth(this));
    }

    closeSection_() {
      this.dispatch(cp.ChromeperfApp.closeSection(this.sectionId));
    }

    toggleChartOnly_() {
      this.dispatch(ChartSection.toggleChartOnly(this.sectionId));
    }

    static toggleChartOnly(sectionId) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'chart-section.toggleChartOnly',
          sectionId: sectionId,
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
        const components = getState().sections[sectionId].testPathComponents;
        if (components[0].selectedOptions && components[0].selectedOptions.length &&
            components[1].selectedOptions && components[1].selectedOptions.length &&
            components[2].selectedOptions && components[2].selectedOptions.length) {
          dispatch(ChartSection.loadTimeseries(sectionId));
        }
      };
    }

    static loadTimeseries(sectionId) {
      return async (dispatch, getState) => {
        const section = getState().sections[sectionId];
        const selectedTestPathComponents = section.testPathComponents.slice(0, 4).map(
          component => (component.isAggregated ? [component.selectedOptions] : component.selectedOptions));
        if (!section.testPathComponents[3].selectedOptions.length) {
          selectedTestPathComponents.pop();
        }
        selectedTestPathComponents.push(section.testPathComponents[4].selectedOptions);
        const testPathCartesianProduct = ChartSection.cartesianProduct(
            selectedTestPathComponents);

        // TODO fetch rows and histograms from backend
        // TODO cache

        // TODO set/clear isLoading

        // TODO use brightnessRange when > 15
        const colors = tr.b.generateFixedColorScheme(testPathCartesianProduct.length);

        // TODO LineChart.layout()

        const state = getState();
        const maxYAxisTickWidth = 30;
        const textHeight = 20;
        const minimapHeight = 60;
        const chartHeight = 200;

        const minimapXAxisTicks = [
          'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
          '2018', 'Feb', 'Mar', 'Apr', 'May',
        ].map((text, index, texts) => ({
          text,
          x: maxYAxisTickWidth + (state.sectionWidth - maxYAxisTickWidth) * index / texts.length,
          y: minimapHeight - 5,
        }));

        const minimapSequences = [{
          path: 'M' + maxYAxisTickWidth + ',20',
          color: '' + colors[0],
          data: [{x: maxYAxisTickWidth, y: 20}],
          dotColor: '' + colors[0],
        }];
        for (let i = 10; i < (state.sectionWidth - maxYAxisTickWidth); i += 10) {
          const datum = {
            x: maxYAxisTickWidth + i,
            y: 20 + parseInt(Math.random() * (minimapHeight - textHeight - 20)),
          };
          minimapSequences[0].data.push(datum);
          minimapSequences[0].path += ' L' + datum.x + ',' + datum.y;
        }

        const minimapAntiBrushes = [
          {
            x: maxYAxisTickWidth,
            width: parseInt(state.sectionWidth * 0.66),
            leftHandle: false,
            rightHandle: true,
            rightHandleX: maxYAxisTickWidth + parseInt(state.sectionWidth * 0.66) - 5,
          },
          {
            x: parseInt(state.sectionWidth * 0.86),
            width: parseInt(state.sectionWidth * 0.14),
            leftHandle: true,
            rightHandle: false,
            leftHandleX: parseInt(state.sectionWidth * 0.86) - 5,
          },
        ];

        const chartSequences = [];
        for (const color of colors) {
          const y0 = 20 + parseInt(Math.random() * (chartHeight - textHeight - 20));
          const sequence = {
            path: 'M' + maxYAxisTickWidth + ',' + y0,
            color: '' + color,
            dotColor: '' + color,
            data: [{x: maxYAxisTickWidth, y: y0}],
          };
          chartSequences.push(sequence);
          for (let i = 10; i < (state.sectionWidth - maxYAxisTickWidth); i += 10) {
            const datum = {
              x: maxYAxisTickWidth + i,
              y: 20 + parseInt(Math.random() * (chartHeight - textHeight - 20)),
            };
            sequence.data.push(datum);
            sequence.path += ' L' + datum.x + ',' + datum.y;
          }
        }

        const chartXAxisTicks = [
          'Dec', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13',
          '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24',
          '25', '26', '27', '28', '29', '30', '31', '2018', '2', '3',
        ].map((text, index, texts) => ({
          text,
          x: maxYAxisTickWidth + (state.sectionWidth - maxYAxisTickWidth) * index / texts.length,
          y: chartHeight - 5,
        }));

        const chartYAxisTicks = [
          '9MB', '8MB', '7MB', '6MB', '5MB', '4MB', '3MB', '2MB', '1MB',
        ].map((text, index, texts) => ({
          text,
          x: 0,
          y: 20 + (chartHeight - textHeight - 20) * index / texts.length,
        }));

        const chartAntiBrushes = [
          {
            x: maxYAxisTickWidth,
            width: parseInt(state.sectionWidth * 0.66),
            leftHandle: false,
            rightHandle: true,
            rightHandleX: maxYAxisTickWidth + parseInt(state.sectionWidth * 0.66) - 5,
          },
          {
            x: parseInt(state.sectionWidth * 0.86),
            width: parseInt(state.sectionWidth * 0.14),
            leftHandleX: parseInt(state.sectionWidth * 0.86) - 5,
            leftHandle: true,
            rightHandle: false,
          },
        ];

        dispatch({
          type: 'chart-section.layoutChart',
          sectionId,

          minimapLayout: {
            width: state.sectionWidth,
            height: minimapHeight,
            left: maxYAxisTickWidth,
            right: state.sectionWidth,
            top: 15,
            bottom: minimapHeight - textHeight,
            graphHeight: minimapHeight - textHeight - 15,
            brushHandleTop: 0,
            dotRadius: 0,
            dotCursor: '',
            sequences: minimapSequences,
            xAxisTicks: minimapXAxisTicks,
            showXAxisTickLines: true,
            fhowYAxisTickLines: false,
            antiBrushes: minimapAntiBrushes,
          },

          chartLayout: {
            width: state.sectionWidth,
            height: chartHeight,
            left: maxYAxisTickWidth,
            right: state.sectionWidth,
            top: 15,
            bottom: chartHeight - textHeight,
            graphHeight: chartHeight - textHeight - 15,
            brushHandleTop: 0,
            dotRadius: 6,
            dotCursor: 'pointer',
            showYAxisTickLines: true,
            showXAxisTickLines: true,
            sequences: chartSequences,
            yAxisTicks: chartYAxisTicks,
            xAxisTicks: chartXAxisTicks,
            antiBrushes: chartAntiBrushes,
          },
        });
      };
    }
  }
  customElements.define(ChartSection.is, ChartSection);

  cp.REDUCERS.set('chart-section.layoutChart', (state, action) => {
    return cp.assignSection(state, action.sectionId, {
      minimapLayout: action.minimapLayout,
      chartLayout: action.chartLayout,
    });
  });

  cp.REDUCERS.set('chart-section.toggleChartOnly', (state, action) => {
    return cp.assignSection(state, action.sectionId, {
      onlyChart: !state.sections[action.sectionId].onlyChart,
    });
  });

  return {
    ChartSection,
  };
});

