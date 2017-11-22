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
        testPathComponents: {type: Array},
        testSuiteDescription: {type: String},
      });
    }

    closeSection_() {
      this.dispatch(closeSection(this.sectionId));
    }

    toggleChartOnly_() {
      this.dispatch(toggleChartOnly(this.sectionId));
    }

    anyHistograms_(histograms) {
      return histograms && histograms.length;
    }
  }
  customElements.define(ChartSection.is, ChartSection);

  const closeSection = sectionId => async (dispatch, getState) => {
    dispatch({
      type: 'chromeperf-app.closeSection',
      sectionId: this.sectionId,
    });
  };

  const toggleChartOnly = sectionId => async (dispatch, getState) => {
    dispatch({
      type: 'chart-section.toggleChartOnly',
      sectionId: this.sectionId,
    });
  };

  return {
  };
});

