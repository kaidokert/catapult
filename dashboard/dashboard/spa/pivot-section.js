/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class PivotSection extends cp.ElementBase {
    static get is() { return 'pivot-section'; }

    static get properties() {
      return cp.ElementBase.statePathProperties('statePath', {
        benchmark: {type: Object},
        bot: {type: Object},
        revisions: {type: Object},
        histograms: {type: Object},
      });
    }

    closeSection_() {
      this.dispatchEvent(new CustomEvent('close-section', {
        bubbles: true,
        composed: true,
        detail: {sectionId: this.sectionId},
      }));
    }
  }

  PivotSection.actions = {
    updateLocation: sectionState => async (dispatch, getState) => {
      const queryParams = {};
      // eslint-disable-next-line no-console
      console.log('TODO distill', sectionState);
      dispatch(cp.ChromeperfApp.actions.updateRoute('pivot', queryParams));
    },

    restoreFromQueryParams: (sectionId, queryParams) =>
      async (dispatch, getState) => {
        // eslint-disable-next-line no-console
        console.log('TODO restore from', queryParams);
      },
  };

  PivotSection.reducers = {
  };

  cp.ElementBase.register(PivotSection);

  return {
    PivotSection,
  };
});
