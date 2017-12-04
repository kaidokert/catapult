/*
Copyright 2017 The Chromium Authors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be
found in the LICENSE file.
*/
'use strict';

tr.exportTo('cp', () => {
  class ChromeperfApp extends cp.Element {
    static get is() { return 'chromeperf-app'; }

    static get properties() {
      return {
        sections: {
          type: Array,
          statePath: 'sections',
        },
        hasClosedSection: {
          type: Boolean,
          statePath: 'hasClosedSection',
        },
        closedSectionType: {
          type: String,
          statePath: 'closedSectionType',
        },
      };
    }

    newAlertsSection_() {
      this.dispatch(ChromeperfApp.appendSection('alerts'));
    }

    newChartSection_() {
      this.dispatch(ChromeperfApp.appendSection('chart'));
    }

    newReleasingSection_() {
      this.dispatch(ChromeperfApp.appendSection('releasing'));
    }

    showFabs_() {
      // TODO for touchscreens
    }

    reopenClosedSection_() {
      this.dispatch(ChromeperfApp.reopenClosedSection());
    }

    static reopenClosedSection() {
      return async (dispatch, getState) => {
        dispatch({
          type: 'chromeperf-app.reopenClosedSection',
        });
      };
    }

    static appendSection(sectionType) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'chromeperf-app.newSection',
          sectionType,
        });
      };
    }

    static closeSection(sectionId) {
      return async (dispatch, getState) => {
        const closedSectionTimerId = Math.random();
        dispatch({
          type: 'chromeperf-app.closeSection',
          sectionId,
          closedSectionTimerId,
        });

        await tr.b.timeout(3000);
        if (getState().closedSectionTimerId !== closedSectionTimerId) return;
        dispatch({
          type: 'chromeperf-app.forgetClosedSection',
        });
      };
    }
  }
  customElements.define(ChromeperfApp.is, ChromeperfApp);

  const NEW_SECTION_STATES = new Map([
    ['chart', cp.ChartSection.NEW_STATE],
    ['alerts', cp.AlertsSection.NEW_STATE],
    ['releasing', cp.ReleasingSection.NEW_STATE],
  ]);

  /**
   * @param {String} action.sectionType
   */
  cp.REDUCERS.set('chromeperf-app.newSection', (state, action) => {
    const newSection = cp.assign(
      {type: action.sectionType},
      NEW_SECTION_STATES.get(action.sectionType));
    if (state.containsDefaultSection) {
      state = cp.assign(state, {
        sections: [newSection],
        containsDefaultSection: false,
      });
      return state;
    }
    return cp.assign(state, {
      sections: state.sections.concat([newSection]),
    });
  });

  /**
   * @param {Number} action.sectionId
   */
  cp.REDUCERS.set('chromeperf-app.closeSection', (state, action) => {
    return cp.assign(state, {
      sections: state.sections.slice(0, action.sectionId).concat(
        state.sections.slice(action.sectionId + 1)),
      hasClosedSection: true,
      closedSection: state.sections[action.sectionId],
      closedSectionType: state.sections[action.sectionId].type,
      closedSectionTimerId: action.closedSectionTimerId,
    });
  });

  cp.REDUCERS.set('chromeperf-app.forgetClosedSection', (state, action) => {
    return cp.assign(state, {
      hasClosedSection: false,
      closedSection: undefined,
      closedSectionType: '',
      closedSectionTimerId: undefined,
    });
  });

  cp.REDUCERS.set('chromeperf-app.reopenClosedSection', (state, action) => {
    return cp.assign(state, {
      sections: state.sections.concat([state.closedSection]),
      hasClosedSection: false,
      closedSection: undefined,
      closedSectionType: '',
      closedSectionTimerId: undefined,
    });
  });

  return {
    ChromeperfApp,
    NEW_SECTION_STATES,
  };
});
