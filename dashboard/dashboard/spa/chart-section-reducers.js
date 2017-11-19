/*
Copyright 2017 The Chromium Authors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be
found in the LICENSE file.
*/
'use strict';

tr.exportTo('cp', () => {
  cp.REDUCERS.set('chart-section.toggleChartOnly', (state, action) => {
    return cp.assignSection(state, action.sectionId, {
      onlyChart: !state.sections[action.sectionId].onlyChart,
    });
  });

  return {
  };
});
