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
    lines: options => options.lines || [],
    revisionRanges: options => options.revisionRanges || [],
    commonLinkRows: options => [],
    bodies: options => [],
  };

  DetailsTable.properties = cp.buildProperties(
      'state', DetailsTable.State);
  DetailsTable.buildState = options => cp.buildState(
      DetailsTable.State, options);
  DetailsTable.observers = [
    'observeConfig_(lines, brushRevisions)',
  ];

  DetailsTable.actions = {
    load: statePath => async(dispatch, getState) => {
      let state = Polymer.Path.get(getState(), statePath);
      if (!state) return;

      const started = performance.now();
      const revisionRanges = DetailsTable.revisionRanges(state.brushRevisions);
      dispatch({
        type: DetailsTable.reducers.startLoading.name,
        statePath,
        started,
        revisionRanges,
      });

      const generator = cp.ChartTimeseries.generateTimeseries(
          lineDescriptors,
          state.revisionRanges,
          cp.LEVEL_OF_DETAIL.HISTOGRAMS);
      for await (const {timeseriesesByLine, errors} of generator) {
        state = Polymer.Path.get(getState(), statePath);
        if (!state || state.started !== started) {
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
      const commonLinkRows = [];
      const bodies = [];
      return {...state, isLoading: true, commonLinkRows, bodies};
    },

    receiveData: (state, {timeseriesesByLine}, rootState) => {
      const commonLinkRows = [];
      const bodies = [];
      return {...state, details, commonLinkRows, bodies};
    },

    doneLoading: (state, action, rootState) => {
      return {...state, isLoading: false};
    },
  };

  return {DetailsTable};
});
