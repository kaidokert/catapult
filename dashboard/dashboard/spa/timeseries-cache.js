/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  const TimeseriesCache = (fetchDescriptor, refStatePath) =>
    async (dispatch, getState) => {
      const rootState = getState();
      // Redux state keys must not contain dots, or they would confuse
      // Polymer.Path.
      const cacheKey = fetchDescriptor.testPath.replace('.', '_');
      const cacheEntry = rootState.timeseries[cacheKey];

      // TODO If cacheKey is in rootState.timeseries, and its data contains
      // everything that fetchDescriptor needs, then add refStatePath to its
      // references and return its data.
      return cacheEntry.data;
      // TODO Otherwise, fetch it, store it, and return it.
    };

  return {
    TimeseriesCache,
  };
});
