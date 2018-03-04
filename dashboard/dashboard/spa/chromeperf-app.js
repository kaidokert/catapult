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

  const PRE_DESCRIBE_TEST_SUITES = [
    'system_health.common_desktop',
    'system_health.common_mobile',
    'system_health.memory_desktop',
    'system_health.memory_mobile',
  ];

  // gapi.auth2.init is then-able, but not await-able, so wrap it in a Promise.
  const gapiAuthInit = params => new Promise(resolve =>
    gapi.load('auth2', () => gapi.auth2.init(params).then(resolve, resolve)));

  class ChromeperfApp extends Polymer.GestureEventListeners(cp.ElementBase) {
    async ready() {
      super.ready();
      if (location.hostname !== 'localhost') {
        await gapiAuthInit({
          client_id: this.$.signin.clientId,
          cookie_policy: this.$.signin.cookiePolicy,
          scope: this.$.signin.scopes,
          hosted_domain: this.$.signin.hostedDomain,
        });
      }
      this.dispatch('ready', this.statePath, new URLSearchParams(
          this.route.path));
    }

    onReduxRouteChange_() {
      this.route = {prefix: '', path: this.reduxRoutePath};
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
        console.log('not going to try to sign in from localhost');
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

    onAlerts_(event) {
      this.dispatch('alerts', this.statePath, event.detail.options);
    }

    onNewChart_(event) {
      this.dispatch('newChart', this.statePath, event.detail.options);
    }

    onSectionChange_() {
      if (!this.readied) return;
      this.debounce('updateLocation', () => {
        this.dispatch('updateLocation', this.statePath);
      }, Polymer.Async.animationFrame);
    }

    showTopButtons_(
        showingReleasingSection, showingAlertsSection, chartSectionIds) {
      return ((showingAlertsSection || !this._empty(chartSectionIds)) &&
              (!showingReleasingSection || !showingAlertsSection));
    }

    showMultipleTopButtons_(showingReleasingSection, showingAlertsSection) {
      return !showingReleasingSection && !showingAlertsSection;
    }

    showMultipleBottomButtons_(
        showingReleasingSection, showingAlertsSection, chartSectionIds) {
      return (
          this.showBottomReleasingButton_(
              showingReleasingSection, showingAlertsSection, chartSectionIds) ||
          this.showBottomAlertsButton_(
              showingReleasingSection, showingAlertsSection, chartSectionIds));
    }

    showBottomReleasingButton_(
        showingReleasingSection, showingAlertsSection, chartSectionIds) {
      return !showingReleasingSection && !this.showTopButtons_(
          showingReleasingSection, showingAlertsSection, chartSectionIds);
    }

    showBottomAlertsButton_(
        showingReleasingSection, showingAlertsSection, chartSectionIds) {
      return !showingAlertsSection && !this.showTopButtons_(
          showingReleasingSection, showingAlertsSection, chartSectionIds);
    }
  }

  ChromeperfApp.properties = {
    ...cp.ElementBase.statePathProperties('statePath', {
      isLoading: {type: Boolean},
      readied: {type: Boolean},
      releasingSection: {
        type: Object,
        observer: 'onSectionChange_',
      },
      showingReleasingSection: {
        type: Boolean,
        observer: 'onSectionChange_',
      },
      alertsSection: {
        type: Object,
        observer: 'onSectionChange_',
      },
      showingAlertsSection: {
        type: Boolean,
        observer: 'onSectionChange_',
      },
      chartSectionIds: {type: Array},
      chartSectionsById: {
        type: Object,
        observer: 'onSectionChange_',
      },
      closedChartId: {type: Number},
      // App-route sets |route|, and redux sets |reduxRoutePath|.
      // ChromeperfApp translates between them.
      // https://stackoverflow.com/questions/41440316
      reduxRoutePath: {
        type: String,
        observer: 'onReduxRouteChange_',
      },
    }),
    route: {
      type: Object,
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
        const state = Polymer.Path.get(getState(), statePath);
        if (0 === state.alertsSection.source.selectedOptions.length) {
          dispatch(cp.DropdownInput.actions.focus(
              `${statePath}.alertsSection.source`));
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
    },

    onSignout: () => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject('', {
        authHeaders: undefined,
        userEmail: '',
      }));
    },

    ready: (statePath, appRouteParams) =>
      async (dispatch, getState) => {
        requestIdleCallback(() => {
          dispatch(cp.TimeseriesCache.actions.testSuites());
          for (const testSuite of PRE_DESCRIBE_TEST_SUITES) {
            dispatch(cp.TimeseriesCache.actions.describe(testSuite));
          }
        });

        dispatch(cp.ElementBase.actions.ensureObject(statePath));

        // Wait for ChromeperfApp and its reducers to be registered.
        await cp.ElementBase.afterRender();

        dispatch({
          type: ChromeperfApp.reducers.ready.typeName,
          statePath,
        });
        await dispatch(ChromeperfApp.actions.restoreFromRoute(
            statePath, appRouteParams));
        dispatch(cp.ElementBase.actions.updateObject(statePath, {
          isLoading: false,
          readied: true,
        }));
      },

    restoreSessionState: (statePath, sessionId) =>
      async (dispatch, getState) => {
        const request = new cp.SessionStateRequest({sessionId});
        const sessionState = await request.response;
        dispatch({
          type: ChromeperfApp.reducers.receiveSessionState.typeName,
          statePath,
          sessionState,
        });
        dispatch(cp.ReleasingSection.actions.restoreState(
            `${statePath}.releasingSection`, sessionState.releasingSection));
        dispatch(cp.AlertsSection.actions.restoreState(
            `${statePath}.alertsSection`, sessionState.alertsSection));
      },

    restoreFromRoute: (statePath, appRouteParams) =>
      async (dispatch, getState) => {
        const sessionId = appRouteParams.get('session');
        if (sessionId) {
          await dispatch(ChromeperfApp.actions.restoreSessionState(
              statePath, sessionId));
          return;
        }

        if (appRouteParams.get('report') !== null) {
          dispatch(cp.ReleasingSection.actions.restoreFromRoute(
              `${statePath}.releasingSection`, appRouteParams));
          return;
        }

        if (appRouteParams.get('alerts') !== null) {
          dispatch(cp.ElementBase.actions.updateObject(statePath, {
            showingReleasingSection: false,
            showingAlertsSection: true,
          }));
          dispatch(cp.ReleasingSection.actions.restoreFromRoute(
              `${statePath}.alertsSection`, appRouteParams));
          return;
        }

        if (appRouteParams.get('testSuite') !== null ||
            appRouteParams.get('chart') !== null) {
          // Hide the releasing section and create a single chart.
          dispatch(cp.ElementBase.actions.updateObject(statePath, {
            showingReleasingSection: false,
          }));
          dispatch({
            type: ChromeperfApp.reducers.newChart.typeName,
            statePath,
            options: cp.ChartSection.newStateOptionsFromQueryParams(
                appRouteParams),
          });
          return;
        }
      },

    saveSession: statePath => async (dispatch, getState) => {
      let state = Polymer.Path.get(getState(), statePath);
      const sessionState = ChromeperfApp.getSessionState(state);
      const request = new cp.SessionIdRequest({sessionState});
      const sessionId = await request.response;
      state = Polymer.Path.get(getState(), statePath);
      const newSessionState = ChromeperfApp.getSessionState(state);
      if (JSON.stringify(sessionState) !== JSON.stringify(newSessionState)) {
        return;
      }
      dispatch(cp.ElementBase.actions.updateObject(statePath, {
        reduxRoutePath: new URLSearchParams({session: sessionId}),
      }));
    },

    updateLocation: statePath => async (dispatch, getState) => {
      const state = Polymer.Path.get(getState(), statePath);
      if (!state.readied) return;
      const nonEmptyCharts = state.chartSectionIds.filter(id =>
          !cp.ChartSection.isEmpty(state.chartSectionsById[id]));

      if (!state.showingReleasingSection &&
          !state.showingAlertsSection &&
          (nonEmptyCharts.length === 0)) {
        dispatch(cp.ElementBase.actions.updateObject(statePath, {
          reduxRoutePath: '',
        }));
        return;
      }

      if (state.showingReleasingSection &&
          !state.showingAlertsSection &&
          (nonEmptyCharts.length === 0)) {
        const routeParams = cp.ReleasingSection.getRouteParams(
            state.releasingSection);
        dispatch(cp.ElementBase.actions.updateObject(statePath, {
          reduxRoutePath: routeParams.toString(),
        }));
        return;
      }

      if (!state.showingReleasingSection &&
          state.showingAlertsSection &&
          (nonEmptyCharts.length === 0)) {
        const routeParams = cp.AlertsSection.getRouteParams(
            state.alertsSection);
        dispatch(cp.ElementBase.actions.updateObject(statePath, {
          reduxRoutePath: routeParams.toString(),
        }));
        return;
      }

      if (!state.showingReleasingSection &&
          !state.showingAlertsSection &&
          (nonEmptyCharts.length === 1)) {
        const queryParams = cp.ChartSection.getRouteParams(
            state.chartSectionsById[nonEmptyCharts[0]]);
        if (queryParams !== undefined) {
          dispatch(cp.ElementBase.actions.updateObject(statePath, {
            reduxRoutePath: queryParams.toString(),
          }));
          return;
        }
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

    newChart: (statePath, options) => async (dispatch, getState) => {
      dispatch({
        type: ChromeperfApp.reducers.newChart.typeName,
        statePath,
        options,
      });
    },

    closeChart: (statePath, sectionId) => async (dispatch, getState) => {
      let state = Polymer.Path.get(getState(), statePath);
      const chart = state.chartSectionsById[sectionId];
      dispatch({
        type: ChromeperfApp.reducers.closeChart.typeName,
        statePath,
        sectionId,
      });
      dispatch(cp.ChromeperfApp.actions.updateLocation(statePath));
      await cp.ElementBase.timeout(5000);
      state = Polymer.Path.get(getState(), statePath);
      if (state.closedChartId !== sectionId) return;
      dispatch({
        type: ChromeperfApp.reducers.forgetClosedChart.typeName,
        statePath,
      });
    },

    alerts: (statePath, options) => async (dispatch, getState) => {
      dispatch(ChromeperfApp.actions.alertsSectionShowing(statePath, true));
      // TODO restoreOptions
    },
  };

  ChromeperfApp.reducers = {
    ready: cp.ElementBase.statePathReducer((state, action) => {
      return {
        ...state,
        isLoading: true,
        readied: false,
        releasingSection: {
          ...cp.ReleasingSection.newState({
            sources: [cp.ReleasingSection.DEFAULT_SOURCE],
          }),
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
        chartSectionIds: [],
        chartSectionsById: {},
      };
    }),

    newChart: cp.ElementBase.statePathReducer((state, action) => {
      const sectionId = action.sectionId || tr.b.GUID.allocateSimple();
      const newSection = {
        type: cp.ChartSection.is,
        sectionId,
        ...cp.ChartSection.newState(action.options || {}),
      };
      const chartSectionsById = {...state.chartSectionsById};
      chartSectionsById[sectionId] = newSection;
      state = {...state, chartSectionsById};

      const chartSectionIds = Array.from(state.chartSectionIds);
      chartSectionIds.push(sectionId);
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

    receiveSessionState: cp.ElementBase.statePathReducer((state, action) => {
      state = {
        ...state,
        isLoading: false,
        showingReleasingSection: action.sessionState.showingReleasingSection,
        showingAlertsSection: action.sessionState.showingAlertsSection,
        chartSectionIds: [],
        chartSectionsById: {},
      };

      for (const options of action.sessionState.chartSections) {
        state = ChromeperfApp.reducers.newChart.implementation(
            state, {options});
      }
      return state;
    }),
  };

  ChromeperfApp.getSessionState = state => {
    const chartSections = [];
    for (const id of state.chartSectionIds) {
      if (cp.ChartSection.isEmpty(state.chartSectionsById[id])) continue;
      chartSections.push(cp.ChartSection.getSessionState(
          state.chartSectionsById[id]));
    }

    return {
      showingReleasingSection: state.showingReleasingSection,
      releasingSection: cp.ReleasingSection.getSessionState(
          state.releasingSection),

      showingAlertsSection: state.showingAlertsSection,
      alertsSection: cp.AlertsSection.getSessionState(state.alertsSection),

      chartSections,
    };
  };

  cp.ElementBase.register(ChromeperfApp);

  return {
    ChromeperfApp,
  };
});
