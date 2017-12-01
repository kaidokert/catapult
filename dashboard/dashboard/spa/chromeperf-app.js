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
        hasClosedSection: {
          type: Boolean,
          statePath: 'hasClosedSection',
        },
        closedSectionType: {
          type: String,
          statePath: 'closedSectionType',
        },
      };
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

    reopenClosedSection_() {
      this.dispatch(ChromeperfApp.reopenClosedSection());
    }

    static reopenClosedSection() {
      return async (dispatch, getState) => {
        dispatch({
          type: 'chromeperf-app.reopenClosedSection',
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
      return async (dispatch, getState) => {
        const closedSectionTimerId = Math.random();
        dispatch({
          type: 'chromeperf-app.closeSection',
          sectionId,
          closedSectionTimerId,
        });

        await tr.b.timeout(3000);
        if (getState().closedSectionTimerId !== timerId) return;
        dispatch({
          type: 'chromeperf-app.forgetClosedSection',
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
        placeholder: 'Bot',
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
        placeholder: 'Measurement',
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
        placeholder: 'Stories',
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
  });

  NEW_SECTION_STATES.set('alerts', {
    anyAlertsSelected: false,
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
    source: {
      inputValue: '',
      isFocused: true,
      selectedOptions: [],
      options: [
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
    },
  });

  NEW_SECTION_STATES.set('releasing', {
    isLoading: false,
    menu: {
      isFocused: true,
      inputValue: '',
      selectedOptions: [],
      options: [
        'Chromeperf Public',
        'Loading',
        'Input',
        'Memory',
        'Battery',
      ],
    },
    milestone: 64,
    isPreviousMilestone: false,
    isNextMilestone: false,
    anyAlerts: false,
  });

  /**
   * @param {String} action.sectionType
   */
  cp.REDUCERS.set('chromeperf-app.newSection', (state, action) => {
    const newSection = cp.assign(
      {type: action.sectionType},
      NEW_SECTION_STATES.get(action.sectionType));
    if (state.containsDefaultSection) {
      state = cp.assign(state, {
        sections: [newSection],
        containsDefaultSection: false,
      });
      return state;
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
      hasClosedSection: true,
      closedSection: state.sections[action.sectionId],
      closedSectionType: state.sections[action.sectionId].type,
      closedSectionTimerId: action.closedSectionTimerId,
    });
  });

  cp.REDUCERS.set('chromeperf-app.forgetClosedSection', (state, action) => {
    return cp.assign(state, {
      hasClosedSection: false,
      closedSection: undefined,
      closedSectionType: '',
      closedSectionTimerId: undefined,
    });
  });

  cp.REDUCERS.set('chromeperf-app.reopenClosedSection', (state, action) => {
    return cp.assign(state, {
      sections: state.sections.concat([state.closedSection]),
      hasClosedSection: false,
      closedSection: undefined,
      closedSectionType: '',
      closedSectionTimerId: undefined,
    });
  });

  return {
    ChromeperfApp,
    NEW_SECTION_STATES,
  };
});
