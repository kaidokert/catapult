/* Copyright 2017 The Chromium Authors. All rights reserved.
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
        isExplainingFab: {
          type: Boolean,
          statePath: 'isExplainingFab',
        },

        // App-route wants to manage some properties, and redux wants to manage
        // some properties, but they can't both manage the same properties, so
        // we have two versions of each of app-route's properties, and manually
        // synchronize them: https://stackoverflow.com/questions/41440316
        routeData: {
          type: Object,
          observer: 'onRouteChange_',
        },
        routeQueryParams: {
          type: Object,
          observer: 'onRouteChange_',
        },
        reduxRouteMode: {
          type: String,
          statePath: 'routeMode',
          observer: 'onReduxRouteChange_',
        },
        reduxRouteQueryParams: {
          type: String,
          statePath: 'routeQueryParams',
          observer: 'onReduxRouteChange_',
        },
      };
    }

    onRouteChange_(nu, old) {
      this._debounceRoute = Polymer.Debouncer.debounce(
          this._debounceRoute, Polymer.Async.microTask, () =>
            this.dispatch(ChromeperfApp.routeChange(
                this.routeData.routeMode, this.routeQueryParams)));
    }

    static routeChange(routeMode, routeQueryParams) {
      return async (dispatch, getState) => {
        const state = getState();
        if (JSON.stringify(routeMode) == JSON.stringify(state.routeMode) &&
            JSON.stringify(routeQueryParams) ==
            JSON.stringify(state.routeQueryParams)) {
          return;
        }
        dispatch({
          type: 'chromeperf-app.routeChange',
          routeMode,
          routeQueryParams,
        });
      };
    }

    static clearRoute() {
      return async (dispatch, getState) => {
        dispatch(ChromeperfApp.routeChange('', {}));
      };
    }

    static saveSession() {
      return async (dispatch, getState) => {
        const state = getState();
        const filteredState = 'TODO';
        // TODO POST to backend to save filteredState
        const sessionId = tr.b.GUID.allocateUUID4();
        const queryParams = {};
        queryParams[sessionId] = '';
        dispatch(ChromeperfApp.routeChange('session', queryParams));
      };
    }

    onReduxRouteChange_() {
      this.routeData = {routeMode: this.reduxRouteMode};
      this.routeQueryParams = this.reduxRouteQueryParams;

      // TODO Why doesn't app-route handle this?
      if (this.reduxRouteMode !== undefined) {
        this.route.path = '/spa/' + this.reduxRouteMode;
        this.route.__queryParams = this.routeQueryParams;
        history.replaceState(this.getState(), '', this.route.path + '?' +
          Object.entries(this.routeQueryParams).map(kv =>
            (kv[1] === '' ? encodeURIComponent(kv[0]) :
            encodeURIComponent(kv[0]) + '=' +
            encodeURIComponent(kv[1])).join('&')));
      }
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

    newPivotSection_() {
      this.dispatch(ChromeperfApp.appendSection('pivot-section'));
    }

    showFabs_() {
      // TODO for touchscreens
    }

    reopenClosedSection_() {
      this.dispatch(ChromeperfApp.reopenClosedSection());
    }

    closeFabCallout_() {
      this.dispatch(ChromeperfApp.closeFabCallout());
    }

    static closeFabCallout() {
      return async (dispatch, getState) => {
        dispatch({
          type: 'chromeperf-app.closeFabCallout',
        });
        // TODO Use localStorage to remember that the fab callout has been
        // closed and does not need to annoy the user ever again.
      };
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
          sectionId: tr.b.GUID.allocateSimple(),
        });
      };
    }

    static closeSection(sectionId) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'chromeperf-app.closeSection',
          sectionId,
        });

        if (getState().sectionIds.length === 0) {
          dispatch(ChromeperfApp.clearRoute());
        }

        await tr.b.timeout(3000);
        if (getState().closedSectionId !== sectionId) return;
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

  cp.REDUCERS.set('chromeperf-app.clearAllFocused', (state, action) => {
    return {
      ...state,
      sectionsById: ChromeperfApp.clearAllFocused(state.sectionsById),
    };
  });

  cp.REDUCERS.set('chromeperf-app.keepDefaultSection', (state, action) => {
    return {
      ...state,
      containsDefaultSection: false,
    };
  });

  const SECTION_CLASSES_BY_TYPE = new Map([
    cp.ChartSection,
    cp.AlertsSection,
    cp.ReleasingSection,
    cp.PivotSection,
  ].map(cls => [cls.is, cls]));

  cp.REDUCERS.set('chromeperf-app.closeFabCallout', (state, action) => {
    return {
      ...state,
      isExplainingFab: false,
    };
  });

  cp.REDUCERS.set('chromeperf-app.newSection', (state, action) => {
    const newSection = {
      type: action.sectionType,
      id: action.sectionId,
      ...SECTION_CLASSES_BY_TYPE.get(action.sectionType).NEW_STATE,
    };
    const sectionsById = {...state.sectionsById};
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

  cp.REDUCERS.set('chromeperf-app.closeSection', (state, action) => {
    const sectionIdIndex = state.sectionIds.indexOf(action.sectionId);
    return {
      ...state,
      sectionIds: state.sectionIds.slice(0, sectionIdIndex).concat(
          state.sectionIds.slice(sectionIdIndex + 1)),
      closedSectionId: action.sectionId,
    };
  });

  cp.REDUCERS.set('chromeperf-app.forgetClosedSection', (state, action) => {
    const sectionsById = {...state.sectionsById};
    delete sectionsById[state.closedSectionId];
    return {
      ...state,
      sectionsById,
      closedSectionId: undefined,
    };
  });

  cp.REDUCERS.set('chromeperf-app.reopenClosedSection', (state, action) => {
    return {
      ...state,
      sectionIds: state.sectionIds.concat([state.closedSectionId]),
      closedSectionId: undefined,
    };
  });

  cp.REDUCERS.set('chromeperf-app.routeChange', (state, action) => {
    return {
      ...state,
      routeMode: action.routeMode,
      routeQueryParams: action.routeQueryParams,
    };
  });

  return {
    ChromeperfApp,
  };
});
