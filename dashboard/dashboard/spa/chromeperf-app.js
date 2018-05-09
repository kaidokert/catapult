/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  const SECTION_CLASSES_BY_TYPE = new Map([
    cp.ChartSection,
    cp.AlertsSection,
    cp.ReportSection,
    cp.PivotSection,
  ].map(cls => [cls.is, cls]));

  const PRE_DESCRIBE_TEST_SUITES = [
    'system_health.common_desktop',
    'system_health.common_mobile',
    'system_health.memory_desktop',
    'system_health.memory_mobile',
  ];

  class SessionStateRequest extends cp.RequestBase {
    constructor(options) {
      super(options);
      this.sessionId_ = options.sessionId;
    }

    get url_() {
      return `/short_uri?sid=${this.sessionId_}`;
    }
  }

  const CLIENT_ID =
    '62121018386-rhk28ad5lbqheinh05fgau3shotl2t6c.apps.googleusercontent.com';

  class RecentBugsRequest extends cp.RequestBase {
    constructor(options) {
      super(options);
      this.method_ = 'POST';
    }

    get url_() {
      return '/api/alerts/recent_bugs';
    }

    async localhostResponse_() {
      const bugs = [];
      function randInt(min, max) {
        return min + parseInt(Math.random() * (max - min));
      }
      for (let i = 0; i < 50; ++i) {
        bugs.push({
          id: randInt(10000, 100000),
          status: 'WontFix',
          owner: {name: 'abc@chromium.org'},
          summary: (randInt(0, 1000) + '% regression in whatever at ' +
                    randInt(1e5, 1e6) + ':' + randInt(1e5, 1e6)),
        });
      }
      return {bugs};
    }
  }

  class ChromeperfApp extends Polymer.GestureEventListeners(cp.ElementBase) {
    get clientId() {
      return CLIENT_ID;
    }

    async ready() {
      super.ready();
      const routeParams = new URLSearchParams(this.route.path);
      let authParams;
      if (this.isProduction) {
        authParams = {
          client_id: this.clientId,
          cookie_policy: '',
          scope: 'email',
          hosted_domain: '',
        };
      }
      this.dispatch('ready', this.statePath, routeParams, authParams);
    }

    observeReduxRoute_() {
      this.route = {prefix: '', path: this.reduxRoutePath};
    }

    async onSignin_(event) {
      await this.dispatch('onSignin', this.statePath);
    }

    async onSignout_(event) {
      await this.dispatch('onSignout', this.statePath);
    }

    reopenClosedChart_() {
      this.dispatch('reopenClosedChart', this.statePath);
    }

    requireSignIn_(event) {
      if (!this.isProduction) {
        // eslint-disable-next-line no-console
        console.log('not going to try to sign in from non-prod hostname');
        return;
      }
      if (!this.userEmail) {
        this.shadowRoot.querySelector('google-signin').signIn();
      }
    }

    hideReportSection_(event) {
      this.dispatch('reportSectionShowing', this.statePath, false);
    }

    showReportSection_(event) {
      this.dispatch('reportSectionShowing', this.statePath, true);
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

    async onAlerts_(event) {
      await this.dispatch('alerts', this.statePath, event.detail.options);
    }

    async onNewChart_(event) {
      await this.dispatch('newChart', this.statePath, event.detail.options);
    }

    async onCloseAllCharts_(event) {
      await this.dispatch('closeAllCharts', this.statePath);
    }

    observeSections_() {
      if (!this.readied) return;
      this.debounce('updateLocation', () => {
        this.dispatch('updateLocation', this.statePath);
      }, Polymer.Async.animationFrame);
    }

    showTopReportButton_(
        showingReportSection, showingAlertsSection, chartSectionIds) {
      return !showingReportSection && (
        showingAlertsSection || !this._empty(chartSectionIds));
    }

    showBottomReportButton_(
        showingReportSection, showingAlertsSection, chartSectionIds) {
      return !showingReportSection && !showingAlertsSection &&
        this._empty(chartSectionIds);
    }

    isInternal_(userEmail) {
      return userEmail.endsWith('@google.com') ||
          userEmail.endsWith('chromium.org');
    }

    get isProduction() {
      return location.hostname === 'v2spa-dot-chromeperf.appspot.com';
    }

    getChartTitle_(ids) {
      if (ids === undefined || ids.length === 0) return '';
      if (ids.length === 1) {
        const title = this.chartSectionsById[ids[0]].title;
        if (title) return title;
      }
      return ids.length + ' charts';
    }

    onReset_(event) {
      this.dispatch('reset', this.statePath);
    }
  }

  ChromeperfApp.properties = {
    ...cp.ElementBase.statePathProperties('statePath', {
      isLoading: {type: Boolean},
      readied: {type: Boolean},
      reportSection: {
        type: Object,
        observer: 'observeSections_',
      },
      showingReportSection: {
        type: Boolean,
        observer: 'observeSections_',
      },
      alertsSection: {
        type: Object,
        observer: 'observeSections_',
      },
      showingAlertsSection: {
        type: Boolean,
        observer: 'observeSections_',
      },
      chartSectionIds: {type: Array},
      chartSectionsById: {
        type: Object,
        observer: 'observeSections_',
      },
      closedChartIds: {type: Array},
      // App-route sets |route|, and redux sets |reduxRoutePath|.
      // ChromeperfApp translates between them.
      // https://stackoverflow.com/questions/41440316
      reduxRoutePath: {
        type: String,
        observer: 'observeReduxRoute_',
      },
      vulcanizedDate: {
        type: String,
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
    ready: (statePath, routeParams, authParams) =>
      async(dispatch, getState) => {
        requestIdleCallback(() => {
          dispatch(cp.ReadTestSuites());
          dispatch(cp.PrefetchTestSuiteDescriptors({
            testSuites: PRE_DESCRIBE_TEST_SUITES,
          }));
        });

        dispatch(cp.ElementBase.actions.ensureObject(statePath));
        dispatch(cp.ElementBase.actions.updateObject('', {
          userEmail: '',
        }));

        // Wait for ChromeperfApp and its reducers to be registered.
        await cp.ElementBase.afterRender();

        // Create the First Contentful Paint with a placeholder table in the
        // ReportSection. ReportSection will also fetch public /api/report_names
        // without authorizationHeaders.
        dispatch({
          type: ChromeperfApp.reducers.ready.typeName,
          statePath,
        });

        if (authParams) {
          // Wait for gapi to load and get an Authorization token.
          // gapi.auth2.init is then-able, but not await-able, so wrap it in a
          // real Promise.
          await new Promise(resolve => gapi.load('auth2', () =>
            gapi.auth2.init(authParams).then(resolve, resolve)));
        }

        // Now, if the user is signed in, we have authorizationHeaders. Try to
        // restore session state, which might include internal data.
        await dispatch(ChromeperfApp.actions.restoreFromRoute(
            statePath, routeParams));

        // The app is done loading.
        dispatch(cp.ElementBase.actions.updateObject(statePath, {
          isLoading: false,
          readied: true,
        }));
      },

    reportSectionShowing: (statePath, showingReportSection) =>
      async(dispatch, getState) => {
        dispatch(cp.ElementBase.actions.updateObject(
            statePath, {showingReportSection}));
      },

    alertsSectionShowing: (statePath, showingAlertsSection) =>
      async(dispatch, getState) => {
        dispatch(cp.ElementBase.actions.updateObject(
            statePath, {showingAlertsSection}));
        if (!showingAlertsSection) return;
        const state = Polymer.Path.get(getState(), statePath);
        if (0 === state.alertsSection.sheriff.selectedOptions.length) {
          dispatch(cp.DropdownInput.actions.focus(
              `${statePath}.alertsSection.sheriff`));
        }
      },

    onSignin: statePath => async(dispatch, getState) => {
      const user = gapi.auth2.getAuthInstance().currentUser.get();
      let response = user.getAuthResponse();
      dispatch(cp.ElementBase.actions.updateObject('', {
        userEmail: user.getBasicProfile().getEmail(),
      }));

      // TODO The AlertsHandler should be able to serve recent bugs without
      // requiring authorization.
      const request = new RecentBugsRequest({});
      response = await request.response;
      dispatch(cp.ElementBase.actions.updateObject('', {
        recentBugs: response.bugs.map(cp.AlertsSection.transformBug),
      }));
    },

    onSignout: () => async(dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject('', {
        userEmail: '',
      }));
    },

    restoreSessionState: (statePath, sessionId) =>
      async(dispatch, getState) => {
        const request = new SessionStateRequest({sessionId});
        const sessionState = await request.response;
        if (sessionState.teamName) {
          dispatch(cp.ElementBase.actions.updateObject('', {
            teamName: sessionState.teamName,
          }));
        }

        dispatch({
          type: ChromeperfApp.reducers.receiveSessionState.typeName,
          statePath,
          sessionState,
        });
        dispatch(cp.ReportSection.actions.restoreState(
            `${statePath}.reportSection`, sessionState.reportSection));
        dispatch(cp.AlertsSection.actions.restoreState(
            `${statePath}.alertsSection`, sessionState.alertsSection));
      },

    restoreFromRoute: (statePath, routeParams) => async(dispatch, getState) => {
      const teamName = routeParams.get('team');
      if (teamName) {
        dispatch(cp.ElementBase.actions.updateObject('', {teamName}));
      }

      const sessionId = routeParams.get('session');
      if (sessionId) {
        await dispatch(ChromeperfApp.actions.restoreSessionState(
            statePath, sessionId));
        return;
      }

      if (routeParams.get('report') !== null) {
        const options = cp.ReportSection.newStateOptionsFromQueryParams(
            routeParams);
        dispatch(cp.ReportSection.actions.restoreState(
            `${statePath}.reportSection`, options));
        return;
      }

      if (routeParams.get('sheriff') !== null ||
          routeParams.get('bug') !== null) {
        dispatch(cp.ElementBase.actions.updateObject(statePath, {
          showingReportSection: false,
          showingAlertsSection: true,
        }));
        const options = cp.AlertsSection.newStateOptionsFromQueryParams(
            routeParams);
        dispatch(cp.AlertsSection.actions.restoreState(
            `${statePath}.alertsSection`, options));
        return;
      }

      if (routeParams.get('testSuite') !== null ||
          routeParams.get('chart') !== null) {
        // Hide the report section and create a single chart.
        dispatch(cp.ElementBase.actions.updateObject(statePath, {
          showingReportSection: false,
        }));
        dispatch({
          type: ChromeperfApp.reducers.newChart.typeName,
          statePath,
          options: cp.ChartSection.newStateOptionsFromQueryParams(
              routeParams),
        });
        return;
      }
    },

    saveSession: statePath => async(dispatch, getState) => {
      const rootState = getState();
      const state = Polymer.Path.get(rootState, statePath);
      dispatch(cp.readSessionId({
        sessionState: {
          ...ChromeperfApp.getSessionState(state),
          teamName: rootState.teamName,
        },
        sessionIdCallback: session =>
          dispatch(cp.ElementBase.actions.updateObject(statePath, {
            reduxRoutePath: new URLSearchParams({session}),
          })),
      }));
    },

    updateLocation: statePath => async(dispatch, getState) => {
      const rootState = getState();
      const state = Polymer.Path.get(rootState, statePath);
      if (!state.readied) return;
      const nonEmptyCharts = state.chartSectionIds.filter(id =>
        !cp.ChartSection.isEmpty(state.chartSectionsById[id]));

      let routeParams;

      if (!state.showingReportSection &&
          !state.showingAlertsSection &&
          (nonEmptyCharts.length === 0)) {
        routeParams = new URLSearchParams();
      }

      if (state.showingReportSection &&
          !state.showingAlertsSection &&
          (nonEmptyCharts.length === 0)) {
        routeParams = cp.ReportSection.getRouteParams(state.reportSection);
      }

      if (!state.showingReportSection &&
          state.showingAlertsSection &&
          (nonEmptyCharts.length === 0)) {
        routeParams = cp.AlertsSection.getRouteParams(state.alertsSection);
      }

      if (!state.showingReportSection &&
          !state.showingAlertsSection &&
          (nonEmptyCharts.length === 1)) {
        routeParams = cp.ChartSection.getRouteParams(
            state.chartSectionsById[nonEmptyCharts[0]]);
      }

      if (routeParams === undefined) {
        dispatch(ChromeperfApp.actions.saveSession(statePath));
        return;
      }

      if (rootState.teamName) {
        routeParams.set('team', rootState.teamName);
      }

      dispatch(cp.ElementBase.actions.updateObject(statePath, {
        reduxRoutePath: routeParams.toString(),
      }));
    },

    reopenClosedChart: statePath => async(dispatch, getState) => {
      const state = Polymer.Path.get(getState(), statePath);
      dispatch(cp.ElementBase.actions.updateObject(statePath, {
        chartSectionIds: [
          ...state.chartSectionIds,
          ...state.closedChartIds,
        ],
        closedChartIds: undefined,
      }));
    },

    newChart: (statePath, options) => async(dispatch, getState) => {
      dispatch({
        type: ChromeperfApp.reducers.newChart.typeName,
        statePath,
        options,
      });
    },

    closeChart: (statePath, sectionId) => async(dispatch, getState) => {
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
      if (state.closedChartIds && !state.closedChartIds.includes(sectionId)) {
        // This chart was reopened.
        return;
      }
      dispatch({
        type: ChromeperfApp.reducers.forgetClosedChart.typeName,
        statePath,
      });
    },

    alerts: (statePath, options) => async(dispatch, getState) => {
      dispatch(ChromeperfApp.actions.alertsSectionShowing(statePath, true));
      // TODO restoreOptions
    },

    closeAllCharts: statePath => async(dispatch, getState) => {
      dispatch({
        type: ChromeperfApp.reducers.closeAllCharts.typeName,
        statePath,
      });
      dispatch(cp.ChromeperfApp.actions.updateLocation(statePath));
    },

    reset: statePath => async(dispatch, getState) => {
      dispatch(cp.ReportSection.actions.restoreState(
          `${statePath}.reportSection`, {sources: [
            cp.ReportSection.DEFAULT_NAME,
          ]}));
      dispatch(ChromeperfApp.actions.reportSectionShowing(statePath, true));
      dispatch(ChromeperfApp.actions.alertsSectionShowing(statePath, false));
      dispatch(ChromeperfApp.actions.closeAllCharts(statePath));
    },
  };

  ChromeperfApp.reducers = {
    ready: (state, action, rootState) => {
      let vulcanizedDate = '';
      if (window.VULCANIZED_TIMESTAMP) {
        vulcanizedDate = tr.b.formatDate(new Date(
            VULCANIZED_TIMESTAMP.getTime() - (1000 * 60 * 60 * 7))) + ' PT';
      }
      return {
        ...state,
        isLoading: true,
        readied: false,
        reportSection: {
          ...cp.ReportSection.newState({
            sources: [cp.ReportSection.DEFAULT_NAME],
          }),
          type: cp.ReportSection.is,
          sectionId: tr.b.GUID.allocateSimple(),
        },
        showingReportSection: true,
        alertsSection: {
          ...cp.AlertsSection.newState({}),
          type: cp.AlertsSection.is,
          sectionId: tr.b.GUID.allocateSimple(),
        },
        showingAlertsSection: false,
        chartSectionIds: [],
        chartSectionsById: {},
        linkedChartState: {
          linkedCursorRevision: undefined,
          linkedMinRevision: undefined,
          linkedMaxRevision: undefined,
          linkedMode: 'normalizeUnit',
          linkedFixedXAxis: true,
          linkedZeroYAxis: false,
        },
        vulcanizedDate,
      };
    },

    newChart: (state, action, rootState) => {
      for (const chart of Object.values(state.chartSectionsById)) {
        // If the user mashes the OPEN CHART button in the alerts-section, for
        // example, don't open multiple copies of the same chart.
        // TODO scroll to the matching chart.
        if (!cp.ChartSection.matchesOptions(chart, action.options)) continue;
        if (state.chartSectionIds.includes(chart.sectionId)) return state;
        return {
          ...state,
          closedChartIds: undefined,
          chartSectionIds: [
            chart.sectionId,
            ...state.chartSectionIds,
          ],
        };
      }

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

      if (chartSectionIds.length === 1 && action.options) {
        const linkedChartState = {...state.linkedChartState};
        if (action.options.mode) {
          linkedChartState.linkedMode = action.options.mode;
        }
        linkedChartState.linkedFixedXAxis = action.options.fixedXAxis;
        linkedChartState.linkedZeroYAxis = action.options.zeroYAxis;
        state = {...state, linkedChartState};
      }
      return {...state, chartSectionIds};
    },

    closeChart: (state, action, rootState) => {
      // Don't remove the section from chartSectionsById until
      // forgetClosedChart.
      const sectionIdIndex = state.chartSectionIds.indexOf(action.sectionId);
      const chartSectionIds = [...state.chartSectionIds];
      chartSectionIds.splice(sectionIdIndex, 1);
      let closedChartIds;
      if (!cp.ChartSection.isEmpty(state.chartSectionsById[action.sectionId])) {
        closedChartIds = [action.sectionId];
      }
      return {
        ...state,
        chartSectionIds,
        closedChartIds,
      };
    },

    closeAllCharts: (state, action, rootState) => {
      return {
        ...state,
        chartSectionIds: [],
        closedChartIds: Array.from(state.chartSectionIds),
      };
    },

    forgetClosedChart: (state, action, rootState) => {
      const chartSectionsById = {...state.chartSectionsById};
      if (state.closedChartIds) {
        for (const id of state.closedChartIds) {
          delete chartSectionsById[id];
        }
      }
      return {
        ...state,
        chartSectionsById,
        closedChartIds: undefined,
      };
    },

    receiveSessionState: (state, action, rootState) => {
      state = {
        ...state,
        isLoading: false,
        showingReportSection: action.sessionState.showingReportSection,
        showingAlertsSection: action.sessionState.showingAlertsSection,
        chartSectionIds: [],
        chartSectionsById: {},
      };

      if (action.sessionState.chartSections) {
        for (const options of action.sessionState.chartSections) {
          state = ChromeperfApp.reducers.newChart(state, {options});
        }
      }
      return state;
    },
  };

  ChromeperfApp.getSessionState = state => {
    const chartSections = [];
    for (const id of state.chartSectionIds) {
      if (cp.ChartSection.isEmpty(state.chartSectionsById[id])) continue;
      chartSections.push(cp.ChartSection.getSessionState(
          state.chartSectionsById[id]));
    }

    return {
      showingReportSection: state.showingReportSection,
      reportSection: cp.ReportSection.getSessionState(
          state.reportSection),

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
