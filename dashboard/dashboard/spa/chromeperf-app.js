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

  class ChromeperfApp extends Polymer.GestureEventListeners(cp.ElementBase) {
    ready() {
      super.ready();
      this.dispatch('ready', this.statePath, this.appRouteData.routeMode,
          this.appRouteQueryParams);
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
      if (!this.readied) return;
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
      readied: {type: Boolean},
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

    ready: (statePath, appRouteMode, appRouteQueryParams) =>
      async (dispatch, getState) => {
        dispatch(cp.ElementBase.actions.ensureObject(statePath));
        await cp.ElementBase.afterRender();
        dispatch({
          type: ChromeperfApp.reducers.ready.typeName,
          statePath,
          appRouteMode,
          appRouteQueryParams,
        });
        dispatch(ChromeperfApp.actions.restoreFromRoute(statePath));
        dispatch(cp.ElementBase.actions.updateObject(
            statePath, {readied: true}));
      },

    restoreSessionState: (statePath, sessionState) =>
      async (dispatch, getState) => {
        let state = Polymer.Path.get(getState(), statePath);
        if (state.reduxRouteMode !== 'session') throw new Error('wtf');
        const sessionId = Object.keys(state.reduxRouteQueryParams)[0];
        const sessionState = await ChromeperfApp.fetchSessionState(sessionId);
        state = Polymer.Path.get(getState(), statePath);
        if ((state.reduxRouteMode !== 'session') ||
            (Object.keys(state.reduxRouteQueryParams)[0] !== sessionId)) {
          return;
        }
        for (const options of sessionState.sections) {
          dispatch({
            type: ChromeperfApp.reducers.newSection.typeName,
            statePath,
            sectionType: options.type,
            sectionId: tr.b.GUID.allocateSimple(),
            options,
          });
        }
      },

    restoreFromRoute: statePath => async (dispatch, getState) => {
      dispatch({
        type: ChromeperfApp.reducers.closeAllSections.typeName,
        statePath,
      });

      const state = Polymer.Path.get(getState(), statePath);

      if (state.reduxRouteMode === 'session') {
        dispatch(ChromeperfApp.actions.restoreSessionState(statePath));
        return;
      }

      const sectionClass = SECTION_CLASSES_BY_TYPE.get(
          state.reduxRouteMode + '-section');
      if (!sectionClass) {
        dispatch({
          type: ChromeperfApp.reducers.restoreDefaultSection.typeName,
          statePath,
        });
        return;
      }

      dispatch({
        type: ChromeperfApp.reducers.newSection.typeName,
        statePath,
        sectionType: sectionClass.is,
        sectionId: tr.b.GUID.allocateSimple(),
        options: sectionClass.newStateOptionsFromQueryParams(
            state.reduxRouteQueryParams),
      });
    },

    appRouteChanged: (statePath, mode, queryParams) =>
      async (dispatch, getState) => {
        const state = Polymer.Path.get(getState(), statePath);
        if (mode == (state.reduxRouteMode || '') &&
            JSON.stringify(queryParams) ==
            JSON.stringify(state.reduxRouteQueryParams)) {
          // appRouteData/appRouteQueryParams were just updated from
          // reduxRouteMode/reduxRouteQueryParams, so don't do anything.
          return;
        }

        dispatch(ChromeperfApp.actions.updateRoute(
            statePath, mode, queryParams));
        dispatch(ChromeperfApp.actions.restoreFromRoute(statePath));
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
      let state = Polymer.Path.get(getState(), statePath);
      const sessionState = ChromeperfApp.getSessionState(state);
      const sessionId = await ChromeperfApp.fetchSessionId(sessionState);

      state = Polymer.Path.get(getState(), statePath);
      const newSessionState = ChromeperfApp.getSessionState(state);
      if (JSON.stringify(sessionState) !== JSON.stringify(newSessionState)) {
        return;
      }

      dispatch(ChromeperfApp.actions.updateRoute(
          statePath, 'session', {[sessionId]: ''}));
    },

    updateLocation: statePath => async (dispatch, getState) => {
      const state = Polymer.Path.get(getState(), statePath);
      if (!state.readied) return;
      if (state.sectionIds.length === 0) {
        dispatch(ChromeperfApp.actions.updateRoute(statePath, '', {}));
        return;
      }
      if (state.sectionIds.length > 1) {
        dispatch(ChromeperfApp.actions.saveSession(statePath));
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

      await tr.b.timeout(5000);
      if (getState().closedSectionId !== sectionId) return;
      dispatch({
        type: ChromeperfApp.reducers.forgetClosedSection.typeName,
        statePath,
      });
    },
  };

  ChromeperfApp.reducers = {
    restoreDefaultSection: cp.ElementBase.statePathReducer((state, action) => {
      return {
        ...state,
        containsDefaultSection: true,
        sectionIds: [DEFAULT_SECTION_ID],
      };
    }),

    ready: cp.ElementBase.statePathReducer((state, action) => {
      const defaultSection = {
        ...cp.ReleasingSection.newState({sources: ['Public']}),
        type: cp.ReleasingSection.is,
        sectionId: DEFAULT_SECTION_ID,
        isOwner: Math.random() < 0.5,
        isPreviousMilestone: true,
      };
      const sectionsByType = {};
      for (const sectionType of SECTION_CLASSES_BY_TYPE.keys()) {
        sectionsByType[sectionType] = {};
      }
      return {
        ...state,
        isExplainingFab: true,
        readied: false,
        reduxRouteMode: action.appRouteMode,
        reduxRouteQueryParams: action.appRouteQueryParams,
        sectionIds: [],
        sectionsById: {[DEFAULT_SECTION_ID]: defaultSection},
        sectionsByType,
        showingFabs: false,
      };
    }),

    closeAllSections: cp.ElementBase.statePathReducer((state, action) => {
      return {
        ...state,
        sectionIds: [],
        sectionsById: {
          [DEFAULT_SECTION_ID]: state.sectionsById[DEFAULT_SECTION_ID],
        },
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
      if (state.closedSectionId !== DEFAULT_SECTION_ID) {
        delete sectionsById[state.closedSectionId];
      }
      return {
        ...state,
        sectionsById,
        closedSectionId: undefined,
      };
    }),
  };

  ChromeperfApp.getSessionState = state => {
    return {
      sections: state.sectionIds.map(sectionId => {
        const sectionState = state.sectionsById[sectionId];
        const sectionClass = SECTION_CLASSES_BY_TYPE.get(sectionState.type);
        return {
          ...sectionClass.getSessionState(sectionState),
          type: sectionState.type,
        };
      }),
    };
  };

  ChromeperfApp.fetchSessionId = async state => {
    const headers = new Headers();
    headers.set('Content-type', 'application/x-www-form-urlencoded');
    const body = 'page_state=' + encodeURIComponent(JSON.stringify(state));
    const response = await fetch('/short_uri', {method: 'POST', headers, body});
    const responseJson = await response.json();
    return responseJson.sid;
  };

  ChromeperfApp.fetchSessionState = async sessionId => {
    const response = await fetch('/short_uri?sid=' + sessionId);
    return await response.json();
  };

  cp.ElementBase.register(ChromeperfApp);

  return {
    ChromeperfApp,
  };
});
