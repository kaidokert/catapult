/*
Copyright 2017 The Chromium Authors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be
found in the LICENSE file.
*/
'use strict';

(function() {
  // Action creators MAY have side-effects.
  // Action creators MUST return an object with type containing a string name of a
  // reducer.
  // Action creators MAY take any number of parameters.
  // Action creators SHOULD NOT have the same name as any reducer in order to avoid
  // confusiong, but technically COULD.

  const ACTION_CREATORS = {};

  ACTION_CREATORS.newAlertsSection = () => {
    return {type: 'addAlertsSection'};
  };

  ACTION_CREATORS.newChartSection = () => {
    return {type: 'addChartSection'};
  };

  ACTION_CREATORS.newReleasingSection = () => {
    return {type: 'addReleasingSection'};
  };

  ACTION_CREATORS.closeSection = sectionId => {
    return {
      type: 'closeSection',
      sectionId,
    };
  };

  ACTION_CREATORS.loadAlerts = (sectionId, sheriff) => {
    return {
      type: 'addAlerts',
      sectionId,
      summary:  '44 alerts in 3 groups',
      rows: [
          {
            isGroupHeader: false,
            revisions: '543210 - 543221',
            bot: 'nexus5X',
            testSuite: 'system_health.common_mobile',
            test: 'story:power_avg/load_chrome_blank',
            delta: '1.000 W',
            deltaPct: '100%',
          },
          {
            isGroupHeader: false,
            revisions: '543222 - 543230',
            bot: 'nexus5X',
            testSuite: 'system_health.common_mobile',
            test: 'story:power_avg/load_chrome_blank',
            delta: '1.000 W',
            deltaPct: '100%',
          },
          {
            isGroupHeader: true,
            isGroupExpanded: false,
            numGroupMembers: 42,
            revisions: '543240 - 543250',
            bot: 'nexus5X',
            testSuite: 'system_health.common_mobile',
            test: 'story:power_avg/load_chrome_blank',
            delta: '1.000 W',
            deltaPct: '100%',
          },
        ]
    };
  };

  window.ACTION_CREATORS = ACTION_CREATORS;
})();
