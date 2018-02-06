/* Copyright 2018 The Chromium Authors. All rights reserved.
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

  // This must be outside the range of tr.b.GUID.allocateSimple().
  const DEFAULT_SECTION_ID = -1;

  async function SHA256(str) {
    str = new TextEncoder('utf-8').encode(str);
    let hash = await crypto.subtle.digest('SHA-256', buffer);
    hash = Array.from(new Uint8Array(hash));
    return hash.map(b => ('00' + b.toString(16)).slice(-2)).join('');
  }

  class ChromeperfApp extends Polymer.GestureEventListeners(cp.ElementBase) {
    ready() {
      super.ready();
      this.dispatch('ready', this.statePath);
    }

    getSections_(sectionIds, sectionsById) {
      if (!sectionIds) return [];
      return sectionIds.map(id => sectionsById[id]);
    }

    getSectionType_(closedSectionId) {
      if (!closedSectionId) return '';
      if (!this.sectionsById) return '';
      if (!this.sectionsById[closedSectionId]) return '';
      return this.sectionsById[closedSectionId].type.split('-')[0];
    }

    onAppRouteChange_() {
      this.debounce('appRouteChanged', () => this.dispatch(
          'appRouteChanged', this.statePath,
          this.appRouteData.routeMode, this.appRouteQueryParams));
    }

    onReduxRouteChange_() {
      this.appRouteData = {routeMode: this.reduxRouteMode};
      this.appRouteQueryParams = this.reduxRouteQueryParams;
      const queryStr = Object.entries(this.reduxRouteQueryParams).map(kv =>
          (kv[1] === '' ? encodeURIComponent(kv[0]) :
          encodeURIComponent(kv[0]) + '=' +
          encodeURIComponent(kv[1]))).join('&');

      // TODO Why doesn't app-route handle this?
      if (['', undefined].includes(this.reduxRouteMode) ||
          ((this.reduxRouteMode === 'releasing') && (queryStr === 'Public'))) {
        this.route.path = '/spa';
        history.replaceState({}, '', this.route.path);
      } else {
        this.route.path = '/spa/' + this.reduxRouteMode;
        this.route.__queryParams = this.reduxRouteQueryParams;
        // Don't use URLSearchParams, which unnecessarily appends equal signs
        // for empty params.
        history.replaceState({}, '', this.route.path + '?' + queryStr);
      }
    }

    onSignin_(event) {
      this.dispatch('onSignin', this.statePath);
    }

    onSignout_(event) {
      this.dispatch('onSignout', this.statePath);
    }

    newAlertsSection_() {
      this.dispatch('onFab', this.statePath, cp.AlertsSection.is);
    }

    newChartSection_() {
      this.dispatch('onFab', this.statePath, cp.ChartSection.is);
    }

    newReleasingSection_() {
      this.dispatch('onFab', this.statePath, cp.ReleasingSection.is);
    }

    newPivotSection_() {
      this.dispatch('onFab', this.statePath, cp.PivotSection.is);
    }

    onFabMouseOver_(event) {
      this.dispatch('fabs', this.statePath, true);
    }

    onFabMouseOut_(event) {
      this.dispatch('fabs', this.statePath, false);
    }

    reopenClosedSection_() {
      this.dispatch('reopenClosedSection', this.statePath);
    }

    closeFabCallout_() {
      this.dispatch('closeFabCallout', this.statePath);
    }

    requireSignIn_(event) {
      if (location.hostname === 'localhost') {
        // eslint-disable-next-line no-console
        console.log('not trying to sign in');
        return;
      }
      if (!this.$.signin.isAuthorized) this.$.signin.signIn();
    }

    closeSection_(event) {
      this.dispatch('closeSection', this.statePath, event.detail.sectionId);
    }

    newSection_(event) {
      this.dispatch('appendSection', this.statePath, event.detail.type,
          event.detail.keepDefaultSection, event.detail.options);
    }

    onSectionChange_() {
      this.dispatch('updateLocation', this.statePath);
    }
  }

  ChromeperfApp.properties = {
    ...cp.ElementBase.statePathProperties('statePath', {
      sectionIds: {type: Array},
      sectionsById: {
        type: Object,
        observer: 'onSectionChange_',
      },
      showingFabs: {type: Boolean},
      closedSectionId: {type: Number},
      isExplainingFab: {type: Boolean},
      // App-route wants to manage some properties, and redux wants to manage
      // some properties, but they can't both manage the same properties, so
      // we have two versions of each of app-route's properties, and manually
      // synchronize them: https://stackoverflow.com/questions/41440316
      reduxRouteMode: {
        type: String,
        observer: 'onReduxRouteChange_',
      },
      reduxRouteQueryParams: {
        type: Object,
        observer: 'onReduxRouteChange_',
      },
    }),
    appRouteData: {
      type: Object,
      observer: 'onAppRouteChange_',
    },
    appRouteQueryParams: {
      type: Object,
      observer: 'onAppRouteChange_',
    },
    userEmail: {
      type: String,
      statePath: 'userEmail',
    },
    sections: {
      type: Array,
      computed: 'getSections_(sectionIds, sectionsById)',
    },
    closedSectionType: {
      type: String,
      computed: 'getSectionType_(closedSectionId)',
    },
  };

  ChromeperfApp.actions = {
    fabs: (statePath, showingFabs) => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(statePath, {
        showingFabs,
      }));
      if (showingFabs) {
        dispatch(cp.ElementBase.actions.updateObject(statePath, {
          isExplainingFab: false,
        }));
      }
    },

    onSignin: () => async (dispatch, getState) => {
      const user = gapi.auth2.getAuthInstance().currentUser.get();
      const response = user.getAuthResponse();
      dispatch(cp.ElementBase.actions.updateObject('', {
        userEmail: user.getBasicProfile().getEmail(),
        authHeaders: {
          Authorization: response.token_type + ' ' + response.access_token,
        },
      }));
      cp.todo('fetch recent bugs here');
    },

    onSignout: () => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject('', {
        authHeaders: undefined,
        userEmail: '',
      }));
    },

    keepDefaultSection: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(statePath, {
        containsDefaultSection: false,
      }));
    },

    ready: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.ensureObject(statePath));

      const defaultSection = {
        ...cp.ReleasingSection.newState({sources: ['Public']}),
        type: cp.ReleasingSection.is,
        sectionId: -1,
        isOwner: Math.random() < 0.5,
        isPreviousMilestone: true,
      };

      const sectionsByType = {};
      for (const sectionType of SECTION_CLASSES_BY_TYPE.keys()) {
        sectionsByType[sectionType] = {};
      }

      dispatch(cp.ElementBase.actions.updateObject(statePath, {
        containsDefaultSection: true,
        isExplainingFab: true,
        sectionIds: [defaultSection.sectionId],
        sectionsById: {[defaultSection.sectionId]: defaultSection},
        sectionsByType,
        showingFabs: false,
      }));
    },

    appRouteChanged: (statePath, mode, queryParams) =>
      async (dispatch, getState) => {
        let state = Polymer.Path.get(getState(), statePath);
        if (mode == (state.reduxRouteMode || '') &&
            JSON.stringify(queryParams) ==
            JSON.stringify(state.reduxRouteQueryParams)) {
          // appRouteData/appRouteQueryParams were just updated from
          // reduxRouteMode/reduxRouteQueryParams, so don't do anything.
          return;
        }
        dispatch(ChromeperfApp.actions.updateRoute(
            statePath, mode, queryParams));
        const sectionClass = SECTION_CLASSES_BY_TYPE.get(
            mode + '-section');
        if (mode === 'session') {
          cp.todo('restore session');
          return;
        }
        if (mode === '' ||
            mode === undefined ||
            sectionClass === undefined) {
          dispatch({
            type: ChromeperfApp.reducers.closeAllSections.typeName,
            statePath,
          });
          return;
        }
        state = getState();
        let sectionId = state.sectionIds[0];
        if (state.sectionIds.length !== 1 ||
            state.sectionsById[sectionId].type !== sectionClass.is) {
          sectionId = tr.b.GUID.allocateSimple();
          dispatch({
            type: ChromeperfApp.reducers.closeAllSections.typeName,
            statePath,
          });
          dispatch(ChromeperfApp.actions.closeSection(-1));
          dispatch({
            type: ChromeperfApp.reducers.newSection.typeName,
            statePath,
            sectionType: sectionClass.is,
            sectionId,
            options: sectionClass.newStateOptionsFromQueryParams(queryParams),
          });
        }
      },

    updateRoute: (statePath, mode, queryParams) =>
      async (dispatch, getState) => {
        const state = Polymer.Path.get(getState(), statePath);
        if (mode == (state.reduxRouteMode || '') &&
            JSON.stringify(queryParams) ==
            JSON.stringify(state.reduxRouteQueryParams)) {
          return;
        }
        dispatch(cp.ElementBase.actions.updateObject(statePath, {
          reduxRouteMode: mode,
          reduxRouteQueryParams: queryParams,
        }));
      },

    saveSession: statePath => async (dispatch, getState) => {
      const state = Polymer.Path.get(getState(), statePath);
      const sessionState = state.sectionIds.map(sectionId => {
        const sectionState = state.sectionsById[sectionId];
        const sectionClass = SECTION_CLASSES_BY_TYPE.get(sectionState.type);
        return sectionClass.getSessionState(sectionState);
      });
      const sessionStateJson = JSON.stringify(sessionState);
      const sessionId = SHA256(stateJson);
      cp.todo('post sessionId = sessionState');
      dispatch(ChromeperfApp.actions.updateRoute(
          statePath, 'session', {[sessionId]: ''}));
    },

    updateLocation: statePath => async (dispatch, getState) => {
      const state = Polymer.Path.get(getState(), statePath);
      if (state.sectionIds.length === 0) {
        dispatch(ChromeperfApp.actions.updateRoute(statePath, '', {}));
        return;
      }
      if (state.sectionIds.length > 1) {
        dispatch(ChromeperfApp.actions.saveSession());
        return;
      }
      const sectionState = state.sectionsById[state.sectionIds[0]];
      const sectionClass = SECTION_CLASSES_BY_TYPE.get(sectionState.type);
      const queryParams = sectionClass.getQueryParams(sectionState);
      if (queryParams === undefined) {
        dispatch(ChromeperfApp.actions.saveSession(statePath));
      } else {
        dispatch(ChromeperfApp.actions.updateRoute(
            statePath, sectionState.type.split('-')[0], queryParams));
      }
    },

    closeFabCallout: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(
          statePath, {isExplainingFab: false}));
      cp.todo('localStorage remember fab callout closed');
    },

    reopenClosedSection: statePath => async (dispatch, getState) => {
      const state = Polymer.Path.get(getState(), statePath);
      dispatch(cp.ElementBase.actions.updateObject(statePath, {
        sectionIds: state.sectionIds.concat([state.closedSectionId]),
        closedSectionId: undefined,
      }));
    },

    onFab: (statePath, sectionType) => async (dispatch, getState) => {
      dispatch(ChromeperfApp.actions.closeFabCallout(statePath));
      dispatch(ChromeperfApp.actions.appendSection(
          statePath, sectionType, false, {}));
    },

    appendSection: (statePath, sectionType, keepDefaultSection, options) =>
      async (dispatch, getState) => {
        dispatch({
          type: ChromeperfApp.reducers.newSection.typeName,
          statePath,
          sectionType,
          keepDefaultSection,
          sectionId: tr.b.GUID.allocateSimple(),
          options,
        });
      },

    closeSection: (statePath, sectionId) => async (dispatch, getState) => {
      dispatch({
        type: ChromeperfApp.reducers.closeSection.typeName,
        statePath,
        sectionId,
      });

      dispatch(cp.ChromeperfApp.actions.updateLocation(statePath));

      await tr.b.timeout(3000);
      if (getState().closedSectionId !== sectionId) return;
      dispatch({
        type: ChromeperfApp.reducers.forgetClosedSection.typeName,
        statePath,
      });
    },
  };

  ChromeperfApp.reducers = {
    closeAllSections: cp.ElementBase.statePathReducer((state, action) => {
      const sectionsById = {};
      sectionsById[-1] = state.sectionsById[-1];
      const sectionIds = [-1];
      return {
        ...state,
        sectionsById,
        sectionIds,
      };
    }),

    newSection: cp.ElementBase.statePathReducer((state, action) => {
      const sectionClass = SECTION_CLASSES_BY_TYPE.get(action.sectionType);
      const newSection = {
        type: action.sectionType,
        sectionId: action.sectionId,
        ...sectionClass.newState(action.options || {}),
      };
      const sectionsById = {...state.sectionsById};
      sectionsById[newSection.sectionId] = newSection;
      const containedDefaultSection = state.containsDefaultSection;
      state = {...state, sectionsById, containsDefaultSection: false};

      if (containedDefaultSection && !action.keepDefaultSection) {
        return {
          ...state,
          sectionIds: [newSection.sectionId],
        };
      }
      return {
        ...state,
        sectionIds: state.sectionIds.concat([newSection.sectionId]),
      };
    }),

    closeSection: cp.ElementBase.statePathReducer((state, action) => {
      // Don't remove the section from sectionsById until forgetClosedSection.
      const sectionIdIndex = state.sectionIds.indexOf(action.sectionId);
      const sectionIds = Array.from(state.sectionIds);
      sectionIds.splice(sectionIdIndex, 1);
      return {
        ...state,
        sectionIds,
        closedSectionId: action.sectionId,
      };
    }),

    forgetClosedSection: cp.ElementBase.statePathReducer((state, action) => {
      const sectionsById = {...state.sectionsById};
      if (state.closedSectionId !== -1) {
        delete sectionsById[state.closedSectionId];
      }
      return {
        ...state,
        sectionsById,
        closedSectionId: undefined,
      };
    }),
  };

  cp.ElementBase.register(ChromeperfApp);

  return {
    ChromeperfApp,
  };
});
