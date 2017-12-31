/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  const SECTION_CLASSES_BY_TYPE = new Map([
    cp.ChartSection,
    cp.AlertsSection,
    cp.ReleasingSection,
    cp.PivotSection,
  ].map(cls => [cls.is, cls]));

  class ChromeperfApp extends cp.ElementBase {
    static get is() { return 'chromeperf-app'; }

    static get properties() {
      return {
        sections: {
          type: Array,
          statePath(state) {
            return (state.sectionIds || []).map(id => state.sectionsById[id]);
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
            if (!state.sectionsById) return '';
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

    ready() {
      super.ready();
      this.dispatch('ready');
    }

    onRouteChange_() {
      this.debounce('routeChanged', () => this.dispatch(
          'routeChanged', this.routeData.routeMode, this.routeQueryParams));
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
      this.dispatch('appendSection', 'alerts-section');
    }

    newChartSection_() {
      this.dispatch('appendSection', 'chart-section');
    }

    newReleasingSection_() {
      this.dispatch('appendSection', 'releasing-section');
    }

    newPivotSection_() {
      this.dispatch('appendSection', 'pivot-section');
    }

    showFabs_() {
      // eslint-disable-next-line no-console
      console.log('TODO show fabs for touchscreens');
    }

    reopenClosedSection_() {
      this.dispatch('reopenClosedSection');
    }

    closeFabCallout_() {
      this.dispatch('closeFabCallout');
    }

    static clearAllFocused(state) {
      const sectionsById = {};
      for (const [id, section] of Object.entries(state.sectionsById)) {
        const cls = SECTION_CLASSES_BY_TYPE.get(section.type);
        sectionsById[id] = cls.clearAllFocused(section);
      }
      return {
        ...state,
        sectionsById,
      };
    }
  }

  ChromeperfApp.actions = {
    focus: statePath => async (dispatch, getState) => {
      dispatch({
        type: 'chromeperf-app.focus',
        statePath,
      });
    },

    keepDefaultSection: () => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObjectAtPath('', {
        containsDefaultSection: false,
      }));
    },

    ready: () => async (dispatch, getState) => {
      const defaultSection = {
        ...cp.ReleasingSection.NEW_STATE,
        type: 'releasing-section',
        sectionId: -1,
        isOwner: Math.random() < 0.5,
        isPreviousMilestone: true,
      };
      dispatch(cp.ElementBase.actions.updateObjectAtPath('', {
        sectionIds: [defaultSection.sectionId],
        sectionsById: {[defaultSection.sectionId]: defaultSection},
        containsDefaultSection: true,
        isExplainingFab: true,
      }));
      dispatch(cp.ReleasingSection.actions.selectSource(
          ['sectionsById', defaultSection.sectionId],
          [defaultSection.source.options[0]]));
    },

    routeChanged: (routeMode, routeQueryParams) =>
      async (dispatch, getState) => {
        let state = getState();
        if (routeMode == (state.routeMode || '') &&
            JSON.stringify(routeQueryParams) ==
            JSON.stringify(state.routeQueryParams)) {
          // routeData/routeQueryParams were just updated from
          // reduxRouteMode/reduxRouteQueryParams, so don't do anything.
          return;
        }
        dispatch(ChromeperfApp.actions.updateRoute(
            routeMode, routeQueryParams));
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
        state = getState();
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
        dispatch(sectionClass.actions.restoreFromQueryParams(
            ['sectionsById', sectionId], routeQueryParams));
      },

    updateRoute: (routeMode, routeQueryParams) =>
      async (dispatch, getState) => {
        const state = getState();
        if (routeMode == (state.routeMode || '') &&
            JSON.stringify(routeQueryParams) ==
            JSON.stringify(state.routeQueryParams)) {
          return;
        }
        dispatch(cp.ElementBase.actions.updateObjectAtPath('', {
          routeMode,
          routeQueryParams,
        }));
      },

    saveSession: () => async (dispatch, getState) => {
      const state = getState();
      // eslint-disable-next-line no-console
      console.log('TODO save filteredState in backend');
      const sessionId = tr.b.GUID.allocateUUID4();
      const queryParams = {};
      queryParams[sessionId] = '';
      dispatch(ChromeperfApp.actions.updateRoute('session', queryParams));
    },

    updateLocation: () => async (dispatch, getState) => {
      const state = getState();
      if (state.sectionIds.length === 0) {
        dispatch(ChromeperfApp.actions.updateRoute('', {}));
        return;
      }
      if (state.sectionIds.length > 1) {
        dispatch(ChromeperfApp.actions.saveSession());
        return;
      }
      const section = state.sectionsById[state.sectionIds[0]];
      const sectionClass = SECTION_CLASSES_BY_TYPE.get(section.type);
      dispatch(sectionClass.actions.updateLocation(section));
    },

    closeFabCallout: () => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObjectAtPath(
          '', {isExplainingFab: false}));
      // eslint-disable-next-line no-console
      console.log('TODO localStorage remember fab callout closed');
    },

    reopenClosedSection: () => async (dispatch, getState) => {
      const state = getState();
      dispatch(cp.ElementBase.actions.updateObjectAtPath('', {
        sectionIds: state.sectionIds.concat([state.closedSectionId]),
        closedSectionId: undefined,
      }));
    },

    appendSection: sectionType => async (dispatch, getState) => {
      dispatch({
        type: 'chromeperf-app.newSection',
        sectionType,
        sectionId: tr.b.GUID.allocateSimple(),
      });
    },

    closeSection: sectionId => async (dispatch, getState) => {
      dispatch({
        type: 'chromeperf-app.closeSection',
        sectionId,
      });

      dispatch(cp.ChromeperfApp.actions.updateLocation());

      await tr.b.timeout(3000);
      if (getState().closedSectionId !== sectionId) return;
      dispatch({type: 'chromeperf-app.forgetClosedSection'});
    },
  };

  ChromeperfApp.reducers = {
    focus: (state, action) => {
      state = cp.ChromeperfApp.clearAllFocused(state);
      if (!action.isFocused) return state;
      // When focusing a dropdown-input, all other dropdown-inputs must be
      // blurred in the same reducer due to how dropdown-input propagates focus
      // between redux and the DOM. Otherwise, infinite recursion can occur.
      return Polymer.Path.setImmutable(state, action.statePath, inputState => {
        return {...inputState, isFocused: true};
      });
    },

    closeAllSections: (state, action) => {
      const sectionsById = {};
      sectionsById[-1] = state.sectionsById[-1];
      const sectionIds = [-1];
      return {
        ...state,
        sectionsById,
        sectionIds,
      };
    },

    newSection: (state, action) => {
      const newSection = {
        type: action.sectionType,
        sectionId: action.sectionId,
        ...SECTION_CLASSES_BY_TYPE.get(action.sectionType).NEW_STATE,
      };
      const sectionsById = {...state.sectionsById};
      sectionsById[newSection.sectionId] = newSection;

      if (state.containsDefaultSection) {
        state = {
          ...state,
          sectionIds: [newSection.sectionId],
          sectionsById,
          containsDefaultSection: false,
        };
        return state;
      }
      return {
        ...state,
        sectionsById,
        sectionIds: state.sectionIds.concat([newSection.sectionId]),
      };
    },

    closeSection: (state, action) => {
      const sectionIdIndex = state.sectionIds.indexOf(action.sectionId);
      return {
        ...state,
        sectionIds: state.sectionIds.slice(0, sectionIdIndex).concat(
            state.sectionIds.slice(sectionIdIndex + 1)),
        closedSectionId: action.sectionId,
      };
    },

    forgetClosedSection: (state, action) => {
      const sectionsById = {...state.sectionsById};
      if (state.closedSectionId !== -1) {
        delete sectionsById[state.closedSectionId];
      }
      return {
        ...state,
        sectionsById,
        closedSectionId: undefined,
      };
    },
  };

  cp.ElementBase.register(ChromeperfApp);

  return {
    ChromeperfApp,
  };
});
