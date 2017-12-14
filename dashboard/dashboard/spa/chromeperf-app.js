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
            if (!state.sectionsById[state.closedSectionId]) return '';
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

    onRouteChange_() {
      this._debounceRoute = Polymer.Debouncer.debounce(
          this._debounceRoute, Polymer.Async.microTask, () =>
            this.dispatch(ChromeperfApp.routeChanged(
                this.routeData.routeMode, this.routeQueryParams)));
    }

    static routeChanged(routeMode, routeQueryParams) {
      return async (dispatch, getState) => {
        dispatch(ChromeperfApp.updateRoute(routeMode, routeQueryParams));
        const sectionClass = SECTION_CLASSES_BY_TYPE.get(
            routeMode + '-section');
        if (routeMode === '' ||
            routeMode === undefined ||
            sectionClass === undefined) {
          dispatch({type: 'chromeperf-app.closeAllSections'});
          return;
        }
        if (routeMode === 'session') {
          // eslint-disable-next-line no-console
          console.log('TODO restore session');
          return;
        }
        const state = getState();
        let sectionId = state.sectionIds[0];
        if (state.sectionIds.length !== 1 ||
            state.sectionsById[sectionId].type !== sectionClass.is) {
          sectionId = tr.b.GUID.allocateSimple();
          dispatch({type: 'chromeperf-app.closeAllSections'});
          dispatch({
            type: 'chromeperf-app.closeSection',
            sectionId: -1,
          });
          dispatch({
            type: 'chromeperf-app.newSection',
            sectionType: sectionClass.is,
            sectionId,
          });
        }
        dispatch(sectionClass.restoreFromQueryParams(
            sectionId, routeQueryParams));
      };
    }

    static updateRoute(routeMode, routeQueryParams) {
      return async (dispatch, getState) => {
        const state = getState();
        if (routeMode == (state.routeMode || '') &&
            JSON.stringify(routeQueryParams) ==
            JSON.stringify(state.routeQueryParams)) {
          return;
        }
        dispatch({
          type: 'chromeperf-app.updateRoute',
          routeMode,
          routeQueryParams,
        });
      };
    }

    static saveSession() {
      return async (dispatch, getState) => {
        const state = getState();
        // eslint-disable-next-line no-console
        console.log('TODO save filteredState in backend');
        const sessionId = tr.b.GUID.allocateUUID4();
        const queryParams = {};
        queryParams[sessionId] = '';
        dispatch(ChromeperfApp.updateRoute('session', queryParams));
      };
    }

    static updateLocation() {
      return async (dispatch, getState) => {
        const state = getState();
        if (state.sectionIds.length === 0) {
          dispatch(ChromeperfApp.updateRoute('', {}));
          return;
        }
        if (state.sectionIds.length > 1) {
          dispatch(ChromeperfApp.saveSession());
          return;
        }
        const section = state.sectionsById[state.sectionIds[0]];
        const sectionClass = SECTION_CLASSES_BY_TYPE.get(section.type);
        dispatch(sectionClass.updateLocation(section));
      };
    }

    onReduxRouteChange_() {
      this.routeData = {routeMode: this.reduxRouteMode};
      this.routeQueryParams = this.reduxRouteQueryParams;

      // TODO Why doesn't app-route handle this?
      if (this.reduxRouteMode === undefined ||
          this.reduxRouteMode === '') {
        this.route.path = '/spa';
        history.replaceState(this.getState(), '', this.route.path);
      } else {
        this.route.path = '/spa/' + this.reduxRouteMode;
        this.route.__queryParams = this.routeQueryParams;
        history.replaceState(this.getState(), '', this.route.path + '?' +
          Object.entries(this.routeQueryParams).map(kv =>
            (kv[1] === '' ? encodeURIComponent(kv[0]) :
            encodeURIComponent(kv[0]) + '=' +
            encodeURIComponent(kv[1]))).join('&'));
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
      // eslint-disable-next-line no-console
      console.log('TODO show fabs for touchscreens');
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
        // eslint-disable-next-line no-console
        console.log('TODO localStorage remember fab callout closed');
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

        dispatch(cp.ChromeperfApp.updateLocation());

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

  cp.REDUCERS.set('chromeperf-app.closeAllSections', (state, action) => {
    const sectionsById = {};
    sectionsById[-1] = state.sectionsById[-1];
    const sectionIds = [-1];
    return {
      ...state,
      sectionsById,
      sectionIds,
    };
  });

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
    if (state.closedSectionId !== -1) {
      delete sectionsById[state.closedSectionId];
    }
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

  cp.REDUCERS.set('chromeperf-app.updateRoute', (state, action) => {
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
