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
    return {type: 'addChartsSection'};
  };

  ACTION_CREATORS.newReleasingSection = () => {
    return {type: 'addReleasingSection'};
  };

  ACTION_CREATORS.loadAlerts = (sectionId, sheriffOrBug) => {
    return {
      type: 'addAlerts',
      sectionId,
    };
  };

  window.ACTION_CREATORS = ACTION_CREATORS;
})();
