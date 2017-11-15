/*
Copyright 2017 The Chromium Authors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be
found in the LICENSE file.
*/
'use strict';

(function() {
  // Reducers MAY NOT have side effects.
  // Reducers MUST return a new Object.
  // Reducers MAY copy some properties from state.

  const REDUCERS = (state, action) => {
    if (state === undefined) return DEFAULT_STATE;
    if (!REDUCERS[action.type]) return state;
    return REDUCERS[action.type](state, action);
  };

  const NEW_CHART_SECTION_STATE = {
    type: 'chart',
  };

  REDUCERS.addChartSection = (state, action) => {
    return Object.assign({}, state, {
      sections: state.sections.concat([
        Object.assign({}, NEW_CHART_SECTION_STATE),
      ]),
    });
  };

  const NEW_ALERTS_SECTION_STATE = {
    type: 'alerts',
    rows: [],
  };

  REDUCERS.addAlertsSection = (state, action) => {
    return Object.assign({}, state, {
      sections: state.sections.concat([
        Object.assign({}, NEW_ALERTS_SECTION_STATE),
      ]),
    });
  };

  const NEW_RELEASING_SECTION_STATE = {
    type: 'releasing',
  };

  REDUCERS.addReleasingSection = (state, action) => {
    return Object.assign({}, state, {
      sections: state.sections.concat([
        Object.assign({}, NEW_RELEASING_SECTION_STATE),
      ]),
    });
  };

  REDUCERS.addAlerts = (state, action) => {
    return Object.assign({}, state, {
      sections:
    }
  };

  window.REDUCERS = REDUCERS;
})();
