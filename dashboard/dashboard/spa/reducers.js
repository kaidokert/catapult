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

  const DEFAULT_STATE = {
    sections: [],
  };

  const NEW_SECTION_STATES = new Map();

  NEW_SECTION_STATES.set('chart', {
    isLoading: false,
  });

  NEW_SECTION_STATES.set('alerts', {
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
  });

  function assign(obj, delta) {
    return Object.assign({}, obj, delta);
  }

  function assignInArray(arr, index, delta) {
    return arr.slice(0, index).concat([
      assign(arr[index], delta),
    ]).concat(arr.slice(index + 1));
  }

  REDUCERS.set('appendSection', (state, action) => {
    return assign(state, {
      sections: state.sections.concat([
        assign({type: action.section}, NEW_SECTION_STATES.get(action.section)),
      ]),
    });
  });

  REDUCERS.set('closeSection', (state, action) => {
    return assign(state, {
      sections: state.sections.slice(0, action.sectionId).concat(
        state.sections.slice(action.sectionId + 1)),
    });
  });

  REDUCERS.set('receiveAlerts', (state, action) => {
    return assign(state, {
      sections: assignInArray(state.sections, action.sectionId, {
        summary: action.summary,
        areRowsPlaceholders: false,
        rows: action.rows,
      }),
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

    return assign(state, {
      sections: assignInArray(state.sections, action.sectionId, {
        rows: newRows,
      }),
    });
  });

  function rootReducer(state, action) {
    if (state === undefined) return DEFAULT_STATE;
    if (!REDUCERS.has(action.type)) return state;
    return REDUCERS.get(action.type)(state, action);
  };

  function bindSectionState(type, name) {
    const obj = {};
    obj[name] = {
      type,
      statePath(state) {
        if (!state.sections[this.sectionId]) return undefined;
        return state.sections[this.sectionId][name];
      }
    };
    return obj;
  }

  window.bindSectionState = bindSectionState;
  window.rootReducerForTesting = rootReducer;
  window.ReduxMixin = PolymerRedux(Redux.createStore(rootReducer, DEFAULT_STATE));
})();
