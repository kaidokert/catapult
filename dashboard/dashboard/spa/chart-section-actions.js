/*
Copyright 2017 The Chromium Authors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be
found in the LICENSE file.
*/
'use strict';

tr.exportTo('cp.cs', () => {
  const ACTIONS = {
    closeSection(sectionId) {
      return {
        type: 'chromeperf-app.closeSection',
        sectionId: this.sectionId,
      };
    },

    toggleChartOnly(sectionId) {
      return {
        type: 'chart-section.toggleChartOnly',
        sectionId: this.sectionId,
      };
    },
  };

  return {
    ACTIONS,
  };
});
