/*
Copyright 2017 The Chromium Authors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be
found in the LICENSE file.
*/
'use strict';

(function() {
  // Reducers MUST NOT have side effects.
  // Reducers MUST NOT modify state.
  // Reducers MUST return a new object.
  // Reducers MAY copy properties from state.

  const REDUCERS = new Map();

  const NEW_SECTION_STATES = new Map();

  NEW_SECTION_STATES.set('chart', {
    isLoading: false,
    onlyChart: false,
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
        canAggregate: true,
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

  const DEFAULT_SECTION = assign(NEW_SECTION_STATES.get('releasing'), {
    type: 'releasing',
    report: 'Chromeperf Public',
    isMenuFocused: false,
    tables: [
      {
        title: 'health-plan-clankium-phone',
        currentVersion: '517411-73a',
        referenceVersion: '508578-c23',
        rows: [
          {
            isFirstInCategory: true,
            rowCount: 4,
            evenCategory: false,
            category: 'Foreground',
            href: '#',
            name: 'Java Heap',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Native Heap',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Ashmem',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Overall PSS',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: true,
            rowCount: 4,
            evenCategory: true,
            category: 'Background',
            href: '#',
            name: 'Java Heap',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Native Heap',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Ashmem',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Overall PSS',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
        ],
      },
      {
        title: 'health-plan-clankium-low-end-phone',
        currentVersion: '517411-73a',
        referenceVersion: '508578-c23',
        rows: [
          {
            isFirstInCategory: true,
            rowCount: 4,
            evenCategory: false,
            category: 'Foreground',
            href: '#',
            name: 'Java Heap',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Native Heap',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Ashmem',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Overall PSS',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: true,
            rowCount: 4,
            evenCategory: true,
            category: 'Background',
            href: '#',
            name: 'Java Heap',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Native Heap',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Ashmem',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Overall PSS',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
        ],
      },
    ],
  });

  const DEFAULT_STATE = {
    sections: [DEFAULT_SECTION],
    containsDefaultSection: true,
  };

  function assign(obj, delta) {
    return Object.assign({}, obj, delta);
  }

  function assignInArray(arr, index, delta) {
    return arr.slice(0, index).concat([
      assign(arr[index], delta),
    ]).concat(arr.slice(index + 1));
  }

  function assignSection(state, sectionId, delta) {
    return assign(state, {
      sections: assignInArray(state.sections, sectionId, delta),
    });
  }

  REDUCERS.set('appendSection', (state, action) => {
    const newSection = assign(
      {type: action.section},
      NEW_SECTION_STATES.get(action.section));
    if (state.containsDefaultSection) {
      return assign(state, {
        sections: [newSection],
        containsDefaultSection: false,
      });
    }
    return assign(state, {
      sections: state.sections.concat([newSection]),
    });
  });

  REDUCERS.set('closeSection', (state, action) => {
    return assign(state, {
      sections: state.sections.slice(0, action.sectionId).concat(
        state.sections.slice(action.sectionId + 1)),
    });
  });

  REDUCERS.set('receiveAlerts', (state, action) => {
    return assignSection(state, action.sectionId, {
      areRowsPlaceholders: false,
      isMenuFocused: false,
      rows: action.rows,
      summary: action.summary,
    });
  });

  REDUCERS.set('toggleAlertGroupExpanded', (state, action) => {
    const oldRows = state.sections[action.sectionId].rows;
    const oldRow = oldRows[action.rowIndex];

    const newRow = assign(oldRow, {
      isGroupExpanded: !oldRow.isGroupExpanded,
    });

    let newRows = oldRows.slice(0, action.rowIndex);
    newRows.push(newRow);

    if (newRow.isGroupExpanded) {
      newRows = newRows.concat(newRow.subRows);
      newRows = newRows.concat(oldRows.slice(action.rowIndex + 1));
    } else {
      newRows = newRows.concat(oldRows.slice(
        action.rowIndex + 1 + newRow.subRows.length));
    }

    return assignSection(state, action.sectionId, {
      rows: newRows,
    });
  });

  /**
   * @param {Number} action.sectionId
   * @param {Number} action.componentIndex
   * @param {String} action.value
   */
  REDUCERS.set('selectTestPathComponent', (state, action) => {
    const oldComponents = state.sections[action.sectionId].testPathComponents;
    const oldComponent = oldComponents[action.componentIndex];
    let newComponents = assignInArray(oldComponents, action.componentIndex, {
      value: action.value,
      isFocused: false,
    });
    if ((1 + action.componentIndex) < newComponents.length) {
      newComponents = assignInArray(newComponents, 1 + action.componentIndex, {
        isFocused: true,
      });
    }

    return assignSection(state, action.sectionId, {
      testPathComponents: newComponents,
    });
  });

  /**
   * @param {Number} action.sectionId
   * @param {Number} action.componentIndex
   * @param {Boolean} action.isFocused
   */
  REDUCERS.set('testPathFocus', (state, action) => {
    const oldComponents = state.sections[action.sectionId].testPathComponents;
    return assignSection(state, action.sectionId, {
      testPathComponents: assignInArray(oldComponents, action.componentIndex, {
        isFocused: action.isFocused,
      }),
    });
  });

  /**
   * @param {Number} action.sectionId
   * @param {Number} action.componentIndex
   * @param {String} action.value
   */
  REDUCERS.set('testPathKeydown', (state, action) => {
    const oldComponents = state.sections[action.sectionId].testPathComponents;
    return assignSection(state, action.sectionId, {
      testPathComponents: assignInArray(oldComponents, action.componentIndex, {
        value: action.value,
      }),
    });
  });

  /**
   * @param {Number} action.sectionId
   * @param {Boolean} action.isFocused
   */
  REDUCERS.set('focusAlertsMenu', (state, action) => {
    return assignSection(state, action.sectionId, {
      isMenuFocused: action.isFocused,
    });
  });

  /**
   * @param {Number} action.sectionId
   * @param {String} action.sheriffOrBug
   */
  REDUCERS.set('alertsMenuKeydown', (state, action) => {
    return assignSection(state, action.sectionId, {
      sheriffOrBug: action.sheriffOrBug,
    });
  });

  /**
   * @param {Number} action.sectionId
   */
  REDUCERS.set('alertsMenuClear', (state, action) => {
    return assignSection(state, action.sectionId, {
      sheriffOrBug: '',
      isMenuFocused: true,
    });
  });

  /**
   * @param {Number} action.sectionId
   * @param {Boolean} action.isMenuFocused
   */
  REDUCERS.set('releasingMenuFocus', (state, action) => {
    return assignSection(state, action.sectionId, {
      isMenuFocused: action.isMenuFocused,
    });
  });

  /**
   * @param {Number} action.sectionId
   * @param {String} action.report
   */
  REDUCERS.set('releasingMenuSelect', (state, action) => {
    return assignSection(state, action.sectionId, DEFAULT_SECTION);
  });

  /**
   * @param {Number} action.sectionId
   */
  REDUCERS.set('releasingMenuClear', (state, action) => {
    return assignSection(state, action.sectionId, {
      report: '',
      isMenuFocused: true,
    });
  });

  /**
   * @param {Number} action.sectionId
   * @param {String} action.report
   */
  REDUCERS.set('releasingMenuKeydown', (state, action) => {
    return assignSection(state, action.sectionId, {
      report: action.report,
      isMenuFocused: true,
    });
  });

  function rootReducer(state, action) {
    if (state === undefined) return DEFAULT_STATE;
    if (!REDUCERS.has(action.type)) return state;
    return REDUCERS.get(action.type)(state, action);
  };

  function sectionProperties(configs) {
    const properties = {sectionId: Number};
    for (const [name, config] of Object.entries(configs)) {
      properties[name] = Object.assign(config, {
        statePath(state) {
          if (!state.sections[this.sectionId]) return undefined;
          return state.sections[this.sectionId][name];
        }
      });
    }
    return properties;
  }

  window.sectionProperties = sectionProperties;
  window.rootReducerForTesting = rootReducer;
  window.ReduxMixin = PolymerRedux(Redux.createStore(rootReducer, DEFAULT_STATE));
})();
