/*
Copyright 2017 The Chromium Authors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be
found in the LICENSE file.
*/
'use strict';

window.REDUCERS = (state, action) => {
  if (state === undefined) return DEFAULT_STATE;
  if (!REDUCERS[action.type]) return state;
  return REDUCERS[action.type](state, action);
};

REDUCERS.addChartSection = (state, action) => {
  return Object.assign({}, state, {
    sections: state.sections.concat([{
      type: 'chart',
    }]),
  });
};

REDUCERS.addAlertsSection = (state, action) => {
  return Object.assign({}, state, {
    sections: state.sections.concat([{
      type: 'alerts',
    }]),
  });
};
