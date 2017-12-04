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
          statePath(state) {
            return state.sectionIds.map(id => state.sectionsById[id]);
          },
        },
        hasClosedSection: {
          type: Boolean,
          statePath(state) {
            return state.closedSectionId !== undefined;
          },
        },
        closedSectionType: {
          type: String,
          statePath(state) {
            if (!state.closedSectionId) return '';
            return state.sectionsById[state.closedSectionId].type.split('-')[0];
          },
        },
      };
    }

    newAlertsSection_() {
      this.dispatch(ChromeperfApp.appendSection('alerts-section'));
    }

    newChartSection_() {
      this.dispatch(ChromeperfApp.appendSection('chart-section'));
    }

    newReleasingSection_() {
      this.dispatch(ChromeperfApp.appendSection('releasing-section'));
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

    static clearAllFocused(oldSectionsById) {
      const newSectionsById = {};
      for (const [id, section] of Object.entries(oldSectionsById)) {
        newSectionsById[id] =
          SECTION_CLASSES_BY_TYPE.get(section.type).clearAllFocused(section);
      }
      return newSectionsById;
    }
  }
  customElements.define(ChromeperfApp.is, ChromeperfApp);

  const SECTION_CLASSES_BY_TYPE = new Map([
    cp.ChartSection,
    cp.AlertsSection,
    cp.ReleasingSection,
  ].map(cls => [cls.is, cls]));

  /**
   * @param {String} action.sectionType
   */
  cp.REDUCERS.set('chromeperf-app.newSection', (state, action) => {
    const newSection = Object.assign(
      {
        type: action.sectionType,
        id: tr.b.GUID.allocateSimple(),
      },
      SECTION_CLASSES_BY_TYPE.get(action.sectionType).NEW_STATE);
    const sectionsById = Object.assign({}, state.sectionsById);
    sectionsById[newSection.id] = newSection;

    if (state.containsDefaultSection) {
      state = {
        ...state,
        sectionIds: [newSection.id],
        sectionsById,
        containsDefaultSection: false,
      };
      return state;
    }
    return {
      ...state,
      sectionsById,
      sectionIds: state.sectionIds.concat([newSection.id]),
    };
  });

  /**
   * @param {Number} action.sectionId
   */
  cp.REDUCERS.set('chromeperf-app.closeSection', (state, action) => {
    const sectionIdIndex = state.sectionIds.indexOf(action.sectionId);
    return {
      ...state,
      sectionIds: state.sectionIds.slice(0, sectionIdIndex).concat(
        state.sectionIds.slice(sectionIdIndex + 1)),
      closedSectionId: action.sectionId,
      closedSectionTimerId: action.closedSectionTimerId,
    };
  });

  cp.REDUCERS.set('chromeperf-app.forgetClosedSection', (state, action) => {
    const sectionsById = Object.assign({}, state.sectionsById);
    delete sectionsById[state.closedSectionId];
    return {
      ...state,
      sectionsById,
      closedSectionId: undefined,
      closedSectionTimerId: undefined,
    };
  });

  cp.REDUCERS.set('chromeperf-app.reopenClosedSection', (state, action) => {
    return {
      ...state,
      sectionIds: state.sectionIds.concat([state.closedSectionId]),
      closedSectionId: undefined,
      closedSectionTimerId: undefined,
    };
  });

  return {
    ChromeperfApp,
  };
});
