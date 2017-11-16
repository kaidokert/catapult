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

  function assign(obj, delta) {
    return Object.assign({}, obj, delta);
  }

  function assignInArray(arr, index, delta) {
    return arr.slice(0, index).concat([
      assign(arr[index], delta),
    ]).concat(arr.slice(index + 1));
  }

  const REDUCERS = (state, action) => {
    if (state === undefined) return DEFAULT_STATE;
    if (!REDUCERS[action.type]) return state;
    return REDUCERS[action.type](state, action);
  };

  REDUCERS.addChartSection = (state, action) => {
    return assign(state, {
      sections: state.sections.concat([
        assign(NEW_CHART_SECTION_STATE),
      ]),
    });
  };

  REDUCERS.addAlertsSection = (state, action) => {
    return assign(state, {
      sections: state.sections.concat([
        assign(NEW_ALERTS_SECTION_STATE),
      ]),
    });
  };

  REDUCERS.addReleasingSection = (state, action) => {
    return assign(state, {
      sections: state.sections.concat([
        assign(NEW_RELEASING_SECTION_STATE),
      ]),
    });
  };

  REDUCERS.addAlerts = (state, action) => {
    return assign(state, {
      sections: assignInArray(state.sections, action.sectionId, {
        summary: action.summary,
        rows: action.rows,
      }),
    });
  };

  window.REDUCERS = REDUCERS;
})();
