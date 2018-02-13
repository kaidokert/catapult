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

  class ChromeperfApp extends Polymer.GestureEventListeners(cp.ElementBase) {
    ready() {
      super.ready();
      this.dispatch('ready', this.statePath, this.appRouteData.routeMode,
          this.appRouteQueryParams);
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

    reopenClosedChart_() {
      this.dispatch('reopenClosedChart', this.statePath);
    }

    requireSignIn_(event) {
      if (location.hostname === 'localhost') {
        // eslint-disable-next-line no-console
        console.log('not trying to sign in');
        return;
      }
      if (!this.$.signin.isAuthorized) this.$.signin.signIn();
    }

    hideReleasingSection_(event) {
      this.dispatch('releasingSectionShowing', this.statePath, false);
    }

    showReleasingSection_(event) {
      this.dispatch('releasingSectionShowing', this.statePath, true);
    }

    showAlertsSection_(event) {
      this.dispatch('alertsSectionShowing', this.statePath, true);
    }

    hideAlertsSection_(event) {
      this.dispatch('alertsSectionShowing', this.statePath, false);
    }

    closeChart_(event) {
      this.dispatch('closeChart', this.statePath, event.model.id);
    }

    newSection_(event) {
      this.dispatch('newSection', this.statePath, event.detail.type,
          event.detail.options, undefined);
    }

    onSectionChange_() {
      if (!this.readied) return;
      this.dispatch('updateLocation', this.statePath);
      this.dispatch('ensureEmptyChart', this.statePath);
    }
  }

  ChromeperfApp.properties = {
    ...cp.ElementBase.statePathProperties('statePath', {
      readied: {type: Boolean},
      releasingSection: {
        type: Object,
        observer: 'onSectionChange_',
      },
      showingReleasingSection: {type: Boolean},
      alertsSection: {
        type: Object,
        observer: 'onSectionChange_',
      },
      showingAlertsSection: {type: Boolean},
      chartSectionIds: {type: Array},
      chartSectionsById: {
        type: Object,
        observer: 'onSectionChange_',
      },
      closedChartId: {type: Number},
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
  };

  ChromeperfApp.actions = {
    releasingSectionShowing: (statePath, showingReleasingSection) =>
      async (dispatch, getState) => {
        dispatch(cp.ElementBase.actions.updateObject(
            statePath, {showingReleasingSection}));
      },

    alertsSectionShowing: (statePath, showingAlertsSection) =>
      async (dispatch, getState) => {
        dispatch(cp.ElementBase.actions.updateObject(
            statePath, {showingAlertsSection}));
      },

    ensureEmptyChart: statePath => async (dispatch, getState) => {
      const state = Polymer.Path.get(getState(), statePath);
      if (ChromeperfApp.anyEmptyChart(state)) return;
      dispatch(ChromeperfApp.actions.newSection(
          statePath, cp.ChartSection.is, {}, undefined));
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
          type: ChromeperfApp.reducers.restoreDefaultSections.typeName,
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
      const nonEmptyCharts = state.chartSectionIds.filter(id =>
          !cp.ChartSection.isEmpty(state.chartSectionsById[id]));

      if (!state.showingReleasingSection &&
          !state.showingAlertsSection &&
          (nonEmptyCharts.length === 0)) {
        dispatch(ChromeperfApp.actions.updateRoute(statePath, '', {}));
        return;
      }

      if (state.showingReleasingSection &&
          !state.showingAlertsSection &&
          (nonEmptyCharts.length === 0)) {
        dispatch(ChromeperfApp.actions.updateRoute(statePath, 'releasing',
            cp.ReleasingSection.getQueryParams(state.releasingSection)));
        return;
      }

      if (!state.showingReleasingSection &&
          state.showingAlertsSection &&
          (nonEmptyCharts.length === 0)) {
        dispatch(ChromeperfApp.actions.updateRoute(statePath, 'alerts',
            cp.AlertsSection.getQueryParams(state.alertsSection)));
        return;
      }

      if (!state.showingReleasingSection &&
          !state.showingAlertsSection &&
          (nonEmptyCharts.length === 1)) {
        dispatch(ChromeperfApp.actions.updateRoute(statePath, 'chart',
            cp.ChartSection.getQueryParams(state.chartSectionsById[
              nonEmptyCharts[0]])));
        return;
      }

      dispatch(ChromeperfApp.actions.saveSession(statePath));
    },

    reopenClosedChart: statePath => async (dispatch, getState) => {
      const state = Polymer.Path.get(getState(), statePath);
      dispatch(cp.ElementBase.actions.updateObject(statePath, {
        chartSectionIds: state.chartSectionIds.concat([state.closedChartId]),
        closedChartId: undefined,
      }));
    },

    newSection: (statePath, sectionType, options, index) =>
      async (dispatch, getState) => {
        dispatch({
          type: ChromeperfApp.reducers.newSection.typeName,
          statePath,
          sectionType,
          index,
          sectionId: tr.b.GUID.allocateSimple(),
          options,
        });
      },

    closeChart: (statePath, sectionId) => async (dispatch, getState) => {
      let state = Polymer.Path.get(getState(), statePath);
      const chart = state.chartSectionsById[sectionId];
      if (cp.ChartSection.isEmpty(chart)) {
        // Don't close the last empty chart.
        const emptyChartIds = state.chartSectionIds.filter(id =>
            cp.ChartSection.isEmpty(state.chartSectionsById[id]));
        if (emptyChartIds.length === 1) return;
      }

      dispatch({
        type: ChromeperfApp.reducers.closeChart.typeName,
        statePath,
        sectionId,
      });
      dispatch(cp.ChromeperfApp.actions.updateLocation(statePath));

      await tr.b.timeout(5000);

      state = Polymer.Path.get(getState(), statePath);
      if (state.closedChartId !== sectionId) return;
      dispatch({
        type: ChromeperfApp.reducers.forgetClosedChart.typeName,
        statePath,
      });
    },
  };

  ChromeperfApp.anyEmptyChart = state => {
    for (const sectionId of state.chartSectionIds) {
      if (cp.ChartSection.isEmpty(state.chartSectionsById[sectionId])) {
        return true;
      }
    }
    return false;
  };

  ChromeperfApp.reducers = {
    ready: cp.ElementBase.statePathReducer((state, action) => {
      const emptyChart = {
        type: cp.ChartSection.is,
        sectionId: tr.b.GUID.allocateSimple(),
        ...cp.ChartSection.newState({}),
      };
      return {
        ...state,
        readied: false,
        reduxRouteMode: action.appRouteMode,
        reduxRouteQueryParams: action.appRouteQueryParams,
        releasingSection: {
          ...cp.ReleasingSection.newState({sources: ['Public']}),
          type: cp.ReleasingSection.is,
          sectionId: tr.b.GUID.allocateSimple(),
          isOwner: Math.random() < 0.5,
          isPreviousMilestone: true,
        },
        showingReleasingSection: true,
        alertsSection: {
          ...cp.AlertsSection.newState({}),
          type: cp.AlertsSection.is,
          sectionId: tr.b.GUID.allocateSimple(),
        },
        showingAlertsSection: false,
        chartSectionIds: [emptyChart.sectionId],
        chartSectionsById: {[emptyChart.sectionId]: emptyChart},
      };
    }),

    restoreDefaultSections: cp.ElementBase.statePathReducer((state, action) => {
      const emptyChart = {
        type: cp.ChartSection.is,
        sectionId: tr.b.GUID.allocateSimple(),
        ...cp.ChartSection.newState({}),
      };
      return {
        ...state,
        showingReleasingSection: true,
        showingAlertsSection: false,
        chartSectionIds: [emptyChart.sectionId],
        chartSectionsById: {[emptyChart.sectionId]: emptyChart},
      };
    }),

    closeAllSections: cp.ElementBase.statePathReducer((state, action) => {
      return {
        ...state,
        showingReleasingSection: false,
        showingAlertsSection: false,
        chartSectionIds: [],
        chartSectionsById: {},
      };
    }),

    newSection: cp.ElementBase.statePathReducer((state, action) => {
      const sectionClass = SECTION_CLASSES_BY_TYPE.get(action.sectionType);
      const newSection = {
        type: action.sectionType,
        sectionId: action.sectionId,
        ...sectionClass.newState(action.options || {}),
      };
      const chartSectionsById = {...state.chartSectionsById};
      chartSectionsById[newSection.sectionId] = newSection;
      state = {...state, chartSectionsById};

      const chartSectionIds = Array.from(state.chartSectionIds);
      if (action.index === undefined) {
        chartSectionIds.push(newSection.sectionId);
      } else {
        chartSectionIds.splice(action.index, 0, newSection.sectionId);
      }
      return {...state, chartSectionIds};
    }),

    closeChart: cp.ElementBase.statePathReducer((state, action) => {
      // Don't remove the section from chartSectionsById until
      // forgetClosedChart.
      const sectionIdIndex = state.chartSectionIds.indexOf(action.sectionId);
      const chartSectionIds = Array.from(state.chartSectionIds);
      chartSectionIds.splice(sectionIdIndex, 1);
      return {
        ...state,
        chartSectionIds,
        closedChartId: action.sectionId,
      };
    }),

    forgetClosedChart: cp.ElementBase.statePathReducer((state, action) => {
      const chartSectionsById = {...state.chartSectionsById};
      delete chartSectionsById[state.closedChartId];
      return {
        ...state,
        chartSectionsById,
        closedChartId: undefined,
      };
    }),
  };

  ChromeperfApp.getSessionState = state => {
    return {
      releasingSection: cp.ReleasingSection.getSessionState(
          state.releasingSection),
      showingReleasingSection: state.showingReleasingSection,
      alertsSection: cp.AlertsSection.getSessionState(state.alertsSection),
      showingAlertsSection: state.showingAlertsSection,
      chartSections: state.chartSectionIds.map(id =>
        cp.ChartSection.getSessionState(state.chartSectionsById[id])),
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
