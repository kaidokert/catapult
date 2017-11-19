/*
Copyright 2017 The Chromium Authors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be
found in the LICENSE file.
*/
'use strict';

tr.exportTo('cp.as', () => {
  const DUMMY_ALERTS = {
    summary:  '6 alerts in 3 groups',
    rows: [
      {
        revisions: '543210 - 543221',
        bot: 'nexus5X',
        testSuite: 'system_health.common_mobile',
        testParts: ['story:power_avg', 'load_chrome_blank', '', '', ''],
        delta: '1.000 W',
        deltaPct: '100%',
      },
      {
        revisions: '543222 - 543230',
        bot: 'nexus5X',
        testSuite: 'system_health.common_mobile',
        testParts: ['story:power_avg', 'load_chrome_blank', '', '', ''],
        delta: '1.000 W',
        deltaPct: '100%',
      },
      {
        isGroupExpanded: false,
        numGroupMembers: 4,
        subRows: [
          {
            isGroupExpanded: true,
            revisions: '543210 - 543221',
            bot: 'nexus5X',
            testSuite: 'system_health.common_mobile',
            testParts: ['story:power_avg', 'load_chrome_blank', '', '', ''],
            delta: '1.000 W',
            deltaPct: '100%',
          },
          {
            isGroupExpanded: true,
            revisions: '543210 - 543221',
            bot: 'nexus5X',
            testSuite: 'system_health.common_mobile',
            testParts: ['story:power_avg', 'load_chrome_blank', '', '', ''],
            delta: '1.000 W',
            deltaPct: '100%',
          },
          {
            isGroupExpanded: true,
            revisions: '543210 - 543221',
            bot: 'nexus5X',
            testSuite: 'system_health.common_mobile',
            testParts: ['story:power_avg', 'load_chrome_blank', '', '', ''],
            delta: '1.000 W',
            deltaPct: '100%',
          },
        ],
        revisions: '543240 - 543250',
        bot: 'nexus5X',
        testSuite: 'system_health.common_mobile',
        testParts: ['story:power_avg', 'load_chrome_blank', '', '', ''],
        delta: '1.000 W',
        deltaPct: '100%',
      },
    ]
  };

  const ACTIONS = {
    loadAlerts(sectionId, sheriff) {
      // TODO fetch()
      return Object.assign({
        type: 'receiveAlerts',
        sectionId,
      }, DUMMY_ALERTS);
    }
  };

  return {
    ACTIONS,
  };
});
