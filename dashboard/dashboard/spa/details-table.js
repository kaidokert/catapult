/* Copyright 2019 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class DetailsTable extends cp.ElementBase {
    columnHead_(range) {
      return 'TODO';
    }

    showDeltaColumn_(revisionRanges) {
      return revisionRanges && (revisionRanges.length === 2);
    }

    observeConfig_() {
      this.debounce('load', () => {
        this.dispatch('load', this.statePath);
      }, Polymer.Async.microTask);
    }
  }

  DetailsTable.State = {
    isLoading: options => false,
    lineDescriptors: options => options.lineDescriptors || [],
    revisionRanges: options => options.revisionRanges || [],
    commonLinkRows: options => [],
    bodies: options => [],
  };

  DetailsTable.properties = cp.buildProperties(
      'state', DetailsTable.State);
  DetailsTable.buildState = options => cp.buildState(
      DetailsTable.State, options);
  DetailsTable.observers = [
    'observeConfig_(lineDescriptors, revisionRanges)',
  ];

  DetailsTable.actions = {
    load: statePath => async(dispatch, getState) => {
      let state = Polymer.Path.get(getState(), statePath);
      if (!state) return;
      dispatch({type: DetailsTable.reducers.startLoading.name, statePath});

      const generator = cp.ChartTimeseries.generateTimeseries(
          state.lineDescriptors.slice(0, cp.ChartTimeseries.MAX_LINES),
          state.revisionRanges,
          cp.LEVEL_OF_DETAIL.HISTOGRAMS);
      for await (const {timeseriesesByLine, errors} of generator) {
        state = Polymer.Path.get(getState(), statePath);
        if (!state) {
          // This chart is no longer in the redux store.
          return;
        }

        dispatch({
          type: DetailsTable.reducers.receiveData.name,
          statePath,
          timeseriesesByLine,
        });
      }

      dispatch({type: DetailsTable.reducers.doneLoading.name, statePath});
    },
  };

  DetailsTable.reducers = {
    startLoading: (state, action, rootState) => {
      return {...state, isLoading: true};
    },

    receiveData: (state, {timeseriesesByLine}, rootState) => {
      const commonLinkRows = [];
      const bodies = [];
      return {...state, commonLinkRows, bodies};
    },

    doneLoading: (state, action, rootState) => {
      return {...state, isLoading: false};
    },
  };

  return {DetailsTable};
});
