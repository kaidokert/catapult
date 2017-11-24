/*
Copyright 2017 The Chromium Authors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be
found in the LICENSE file.
*/
'use strict';

tr.exportTo('cp', () => {
  class ChromeperfApp extends cp.Element {
    static get is() { return 'chromeperf-app'; }

    static get properties() {
      return {
        sections: {
          type: Array,
          statePath: 'sections',
        },
      };
    }

    ready() {
      super.ready();
      this.onResize_ = this.onResize_.bind(this);
      window.addEventListener('resize', this.onResize_);
    }

    onResize_(e) {
      this.dispatch(ChromeperfApp.updateSectionWidth(
        this.shadowRoot.querySelector(
          'chart-section, alerts-section, releasing-section')));
    }

    newAlertsSection_() {
      this.dispatch(ChromeperfApp.appendSection('alerts'));
    }

    newChartSection_() {
      this.dispatch(ChromeperfApp.appendSection('chart'));
    }

    newReleasingSection_() {
      this.dispatch(ChromeperfApp.appendSection('releasing'));
    }

    showFabs_() {
      // TODO for touchscreens
    }

    static updateSectionWidth(section) {
      return async (dispatch, getState) => {
        const rect = await cp.measureElement(section);
        if (Math.abs(rect.width - getState().sectionWidth) < 1) return;
        dispatch({
          type: 'chromeperf-app.updateSectionWidth',
          sectionWidth: rect.width,
        });
      };
    }

    static appendSection(sectionType) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'chromeperf-app.newSection',
          sectionType,
        });
      };
    }

    static closeSection(sectionId) {
      return  async (dispatch, getState) => {
        dispatch({
          type: 'chromeperf-app.closeSection',
          sectionId,
        });
      };
    }
  }
  customElements.define(ChromeperfApp.is, ChromeperfApp);

  const NEW_SECTION_STATES = new Map();

  NEW_SECTION_STATES.set('chart', {
    isLoading: false,
    onlyChart: false,
    chartLayout: false,
    minimapLayout: false,
    testSuiteDescription: 'test suite description',
    histograms: undefined,
    testPathComponents: [
      {
        placeholder: 'Test suite',
        canAggregate: true,
        isFocused: true,
        value: '',
        options: [
          'system_health.common_desktop',
          'system_health.common_mobile',
          'system_health.memory_desktop',
          'system_health.memory_mobile',
        ],
      },
      {
        placeholder: 'Bot',
        canAggregate: true,
        isFocused: false,
        value: '',
        options: [
          'nexus5X',
          'nexus5',
          'mac',
          'win',
          'linux',
        ],
      },
      {
        placeholder: 'Measurement',
        canAggregate: false,
        isFocused: false,
        value: '',
        options: [
          'PSS',
          'power',
          'TTFMP',
          'TTI',
        ],
      },
      {
        placeholder: 'Stories',
        canAggregate: true,
        isFocused: false,
        value: '',
        options: [
          'load:news:cnn',
          'load:news:nytimes',
          'load:news:qq',
        ],
      },
      {
        placeholder: 'Statistics',
        canAggregate: false,
        value: 'avg',
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
  });

  NEW_SECTION_STATES.set('alerts', {
    sheriffOrBug: '',
    isMenuFocused: true,
    rows: [
      {
        revisions: '-----',
        bot: '-----',
        testSuite: '-----',
        testParts: ['-----', '', '', '', ''],
        delta: '-----',
        deltaPct: '-----',
      },
      {
        revisions: '-----',
        bot: '-----',
        testSuite: '-----',
        testParts: ['-----', '', '', '', ''],
        delta: '-----',
        deltaPct: '-----',
      },
      {
        revisions: '-----',
        bot: '-----',
        testSuite: '-----',
        testParts: ['-----', '', '', '', ''],
        delta: '-----',
        deltaPct: '-----',
      },
      {
        revisions: '-----',
        bot: '-----',
        testSuite: '-----',
        testParts: ['-----', '', '', '', ''],
        delta: '-----',
        deltaPct: '-----',
      },
      {
        revisions: '-----',
        bot: '-----',
        testSuite: '-----',
        testParts: ['-----', '', '', '', ''],
        delta: '-----',
        deltaPct: '-----',
      },
    ],
    areRowsPlaceholders: true,
    isLoading: false,
    showingImprovements: false,
    showingTriaged: false,
    sheriffList: [
      "ARC Perf Sheriff",
      "Angle Perf Sheriff",
      "Binary Size Sheriff",
      "Blink Memory Mobile Sheriff",
      "Chrome OS Graphics Perf Sheriff",
      "Chrome OS Installer Perf Sheriff",
      "Chrome OS Perf Sheriff",
      "Chrome Perf Accessibility Sheriff",
      "Chromium Perf AV Sheriff",
      "Chromium Perf Sheriff",
      "Chromium Perf Sheriff - Sub-series",
      "CloudView Perf Sheriff",
      "Cronet Perf Sheriff",
      "Jochen",
      "Mojo Perf Sheriff",
      "NaCl Perf Sheriff",
      "Network Service Sheriff",
      "OWP Storage Perf Sheriff",
      "Oilpan Perf Sheriff",
      "Pica Sheriff",
      "Power Perf Sheriff",
      "Service Worker Perf Sheriff",
      "Tracing Perftests Sheriff",
      "V8 Memory Perf Sheriff",
      "V8 Perf Sheriff",
      "WebView Perf Sheriff",
    ],
  });

  NEW_SECTION_STATES.set('releasing', {
    isLoading: false,
    isMenuFocused: true,
    report: '',
    reportOptions: [
      'Chromeperf Public',
      'Loading',
      'Input',
      'Memory',
      'Battery',
    ],
    milestone: 64,
    isPreviousMilestone: true,
    isNextMilestone: false,
  });

  /**
   * @param {String} action.sectionType
   */
  cp.REDUCERS.set('chromeperf-app.newSection', (state, action) => {
    if (state.sections.length >= 3) throw 'WTF';
    const newSection = cp.assign(
      {type: action.sectionType},
      NEW_SECTION_STATES.get(action.sectionType));
    if (state.containsDefaultSection) {
      return cp.assign(state, {
        sections: [newSection],
        containsDefaultSection: false,
      });
    }
    return cp.assign(state, {
      sections: state.sections.concat([newSection]),
    });
  });

  /**
   * @param {Number} action.sectionId
   */
  cp.REDUCERS.set('chromeperf-app.closeSection', (state, action) => {
    return cp.assign(state, {
      sections: state.sections.slice(0, action.sectionId).concat(
        state.sections.slice(action.sectionId + 1)),
    });
  });

  cp.REDUCERS.set('chromeperf-app.updateSectionWidth', (state, action) => {
    return cp.assign(state, {sectionWidth: action.sectionWidth});
  });

  return {
    ChromeperfApp,
  };
});
