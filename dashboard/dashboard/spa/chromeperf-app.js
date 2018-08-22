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
      return `/short_uri?v2=true&sid=${this.sessionId_}`;
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

  class ChromeperfApp extends cp.ElementBase {
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

    escapedUrl_(path) {
      return encodeURIComponent(window.location.origin + '#' + path);
    }

    showBottomButtons_(
        enableNav, showingReportSection, alertsSectionIds, chartSectionIds) {
      return enableNav && (
        showingReportSection ||
        !this._empty(alertsSectionIds) ||
        !this._empty(chartSectionIds));
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

    async onReopenClosedAlerts_(event) {
      await this.dispatch('reopenClosedAlerts', this.statePath);
    }

    async onReopenClosedChart_() {
      await this.dispatch('reopenClosedChart', this.statePath);
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

    async onShowReportSection_(event) {
      await this.dispatch('reportSectionShowing', this.statePath, true);
    }

    async onNewAlertsSection_(event) {
      await this.dispatch('newAlerts', this.statePath, {});
    }

    async onCloseAlerts_(event) {
      await this.dispatch('closeAlerts', this.statePath, event.model.id);
    }

    async onCloseChart_(event) {
      this.dispatch('closeChart', this.statePath, event.model.id);
    }

    async onReportAlerts_(event) {
      await this.dispatch('newAlerts', this.statePath, event.detail.options);
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

    isInternal_(userEmail) {
      return userEmail.endsWith('@google.com');
    }

    get isProduction() {
      return cp.IS_PRODUCTION;
    }

    getChartTitle_(ids) {
      if (ids === undefined || ids.length === 0) return '';
      if (ids.length === 1) {
        const title = this.chartSectionsById[ids[0]].title;
        if (title) return title;
      }
      return ids.length + ' charts';
    }

    getAlertsTitle_(ids) {
      if (ids === undefined || ids.length === 0) return '';
      if (ids.length === 1) {
        const section = this.alertsSectionsById[ids[0]];
        if (section) {
          const title = cp.AlertsSection.getTitle(section);
          if (title) return title;
        }
      }
      return ids.length + ' alerts-sections';
    }

    onReset_(event) {
      this.dispatch('reset', this.statePath);
    }
  }

  ChromeperfApp.properties = {
    ...cp.ElementBase.statePathProperties('statePath', {
      enableNav: {type: Boolean},
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
      alertsSectionIds: {type: Array},
      alertsSectionsById: {
        type: Object,
        observer: 'observeSections_',
      },
      chartSectionIds: {type: Array},
      chartSectionsById: {
        type: Object,
        observer: 'observeSections_',
      },
      closedAlertsIds: {type: Array},
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
          cp.ReadTestSuites()(dispatch, getState);
          cp.PrefetchTestSuiteDescriptors({
            testSuites: PRE_DESCRIBE_TEST_SUITES,
          })(dispatch, getState);
        });

        cp.ElementBase.actions.ensureObject(statePath)(dispatch, getState);
        cp.ElementBase.actions.updateObject('', {
          userEmail: '',
          largeDom: false,
        })(dispatch, getState);

        // Wait for ChromeperfApp and its reducers to be registered.
        await cp.afterRender();

        // Create the First Contentful Paint with a placeholder table in the
        // ReportSection. ReportSection will also fetch public /api/report/names
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
        await ChromeperfApp.actions.restoreFromRoute(
            statePath, routeParams)(dispatch, getState);

        // The app is done loading.
        cp.ElementBase.actions.updateObject(statePath, {
          isLoading: false,
          readied: true,
        })(dispatch, getState);

        if (cp.IS_DEBUG) {
          cp.ChromeperfApp.actions.getRecentBugs()(dispatch, getState);
        }
      },

    reportSectionShowing: (statePath, showingReportSection) =>
      async(dispatch, getState) => {
        cp.ElementBase.actions.updateObject(statePath, {
          showingReportSection,
        })(dispatch, getState);
      },

    newAlerts: (statePath, options) => async(dispatch, getState) => {
      const sectionId = tr.b.GUID.allocateSimple();
      dispatch({
        type: ChromeperfApp.reducers.newAlerts.typeName,
        statePath,
        sectionId,
        options,
      });

      const state = Polymer.Path.get(getState(), statePath);
      const section = state.alertsSectionsById[sectionId];
      if (cp.AlertsSection.isEmpty(section)) {
        cp.DropdownInput.actions.focus(
            `${statePath}.alertsSectionsById.${sectionId}.sheriff`
        )(dispatch, getState);
      }
    },

    closeAlerts: (statePath, sectionId) => async(dispatch, getState) => {
      dispatch({
        type: ChromeperfApp.reducers.closeAlerts.typeName,
        statePath,
        sectionId,
      });
      cp.ChromeperfApp.actions.updateLocation(statePath)(dispatch, getState);

      await cp.timeout(5000);
      const state = Polymer.Path.get(getState(), statePath);
      if (state.closedAlertsIds && !state.closedAlertsIds.includes(sectionId)) {
        // This alerts section was reopened.
        return;
      }
      dispatch({
        type: ChromeperfApp.reducers.forgetClosedAlerts.typeName,
        statePath,
      });
    },

    onSignin: statePath => async(dispatch, getState) => {
      const user = gapi.auth2.getAuthInstance().currentUser.get();
      const response = user.getAuthResponse();
      cp.ElementBase.actions.updateObject('', {
        userEmail: user.getBasicProfile().getEmail(),
      })(dispatch, getState);
      await Promise.all([
        cp.ReadReportNames()(dispatch, getState),
        cp.ChromeperfApp.actions.getRecentBugs()(dispatch, getState),
        cp.ReadTestSuites()(dispatch, getState),
      ]);
    },

    getRecentBugs: () => async(dispatch, getState) => {
      // TODO The AlertsHandler should be able to serve recent bugs without
      // requiring authorization.
      const request = new RecentBugsRequest({});
      const response = await request.response;
      cp.ElementBase.actions.updateObject('', {
        recentPerformanceBugs: response.bugs.map(cp.AlertsSection.transformBug),
      })(dispatch, getState);
    },

    onSignout: () => async(dispatch, getState) => {
      cp.ElementBase.actions.updateObject('', {
        userEmail: '',
      })(dispatch, getState);
    },

    restoreSessionState: (statePath, sessionId) =>
      async(dispatch, getState) => {
        const request = new SessionStateRequest({sessionId});
        const sessionState = await request.response;
        if (sessionState.teamName) {
          cp.ElementBase.actions.updateObject('', {
            teamName: sessionState.teamName,
          })(dispatch, getState);
        }

        dispatch({
          type: 'CHAIN',
          actions: [
            {
              type: ChromeperfApp.reducers.receiveSessionState.typeName,
              statePath,
              sessionState,
            },
            {
              type: ChromeperfApp.reducers.updateLargeDom.typeName,
              appStatePath: statePath,
            },
          ],
        });
        cp.ReportSection.actions.restoreState(
            `${statePath}.reportSection`, sessionState.reportSection
        )(dispatch, getState);
      },

    restoreFromRoute: (statePath, routeParams) => async(dispatch, getState) => {
      const teamName = routeParams.get('team');
      if (teamName) {
        cp.ElementBase.actions.updateObject('', {teamName})(dispatch, getState);
      }

      if (routeParams.has('nonav')) {
        cp.ElementBase.actions.updateObject(statePath, {
          enableNav: false,
        })(dispatch, getState);
      }

      const sessionId = routeParams.get('session');
      if (sessionId) {
        await ChromeperfApp.actions.restoreSessionState(
            statePath, sessionId)(dispatch, getState);
        return;
      }

      if (routeParams.get('report') !== null) {
        const options = cp.ReportSection.newStateOptionsFromQueryParams(
            routeParams);
        cp.ReportSection.actions.restoreState(
            `${statePath}.reportSection`, options)(dispatch, getState);
        return;
      }

      if (routeParams.get('sheriff') !== null ||
          routeParams.get('bug') !== null ||
          routeParams.get('ar') !== null) {
        // Hide the report section and create a single alerts-section.
        cp.ElementBase.actions.updateObject(statePath, {
          showingReportSection: false,
        })(dispatch, getState);
        dispatch({
          type: ChromeperfApp.reducers.newAlerts.typeName,
          statePath,
          options: cp.AlertsSection.newStateOptionsFromQueryParams(
              routeParams),
        });
        return;
      }

      if (routeParams.get('testSuite') !== null ||
          routeParams.get('chart') !== null) {
        // Hide the report section and create a single chart.
        cp.ElementBase.actions.updateObject(statePath, {
          showingReportSection: false,
        })(dispatch, getState);
        ChromeperfApp.actions.newChart(
            statePath, cp.ChartSection.newStateOptionsFromQueryParams(
                routeParams))(dispatch, getState);
        return;
      }
    },

    saveSession: statePath => async(dispatch, getState) => {
      const rootState = getState();
      const state = Polymer.Path.get(rootState, statePath);
      cp.readSessionId({
        sessionState: {
          ...ChromeperfApp.getSessionState(state),
          teamName: rootState.teamName,
        },
        sessionIdCallback: session =>
          cp.ElementBase.actions.updateObject(statePath, {
            reduxRoutePath: new URLSearchParams({session}),
          })(dispatch, getState),
      })(dispatch, getState);
    },

    updateLocation: statePath => async(dispatch, getState) => {
      const rootState = getState();
      const state = Polymer.Path.get(rootState, statePath);
      if (!state.readied) return;
      const nonEmptyAlerts = state.alertsSectionIds.filter(id =>
        !cp.AlertsSection.isEmpty(state.alertsSectionsById[id]));
      const nonEmptyCharts = state.chartSectionIds.filter(id =>
        !cp.ChartSection.isEmpty(state.chartSectionsById[id]));

      let routeParams;

      if (!state.showingReportSection &&
          (nonEmptyAlerts.length === 0) &&
          (nonEmptyCharts.length === 0)) {
        routeParams = new URLSearchParams();
      }

      if (state.showingReportSection &&
          (nonEmptyAlerts.length === 0) &&
          (nonEmptyCharts.length === 0)) {
        routeParams = cp.ReportSection.getRouteParams(state.reportSection);
      }

      if (!state.showingReportSection &&
          (nonEmptyAlerts.length === 1) &&
          (nonEmptyCharts.length === 0)) {
        routeParams = cp.AlertsSection.getRouteParams(
            state.alertsSectionsById[nonEmptyAlerts[0]]);
      }

      if (!state.showingReportSection &&
          (nonEmptyAlerts.length === 0) &&
          (nonEmptyCharts.length === 1)) {
        routeParams = cp.ChartSection.getRouteParams(
            state.chartSectionsById[nonEmptyCharts[0]]);
      }

      if (routeParams === undefined) {
        ChromeperfApp.actions.saveSession(statePath)(dispatch, getState);
        return;
      }

      if (rootState.teamName) {
        routeParams.set('team', rootState.teamName);
      }

      if (!state.enableNav) {
        routeParams.set('nonav', '');
      }

      cp.ElementBase.actions.updateObject(statePath, {
        reduxRoutePath: routeParams.toString(),
      })(dispatch, getState);
    },

    reopenClosedAlerts: statePath => async(dispatch, getState) => {
      const state = Polymer.Path.get(getState(), statePath);
      cp.ElementBase.actions.updateObject(statePath, {
        alertsSectionIds: [
          ...state.alertsSectionIds,
          ...state.closedAlertsIds,
        ],
        closedAlertsIds: undefined,
      })(dispatch, getState);
    },

    reopenClosedChart: statePath => async(dispatch, getState) => {
      const state = Polymer.Path.get(getState(), statePath);
      cp.ElementBase.actions.updateObject(statePath, {
        chartSectionIds: [
          ...state.chartSectionIds,
          ...state.closedChartIds,
        ],
        closedChartIds: undefined,
      })(dispatch, getState);
    },

    newChart: (statePath, options) => async(dispatch, getState) => {
      dispatch({
        type: 'CHAIN',
        actions: [
          {
            type: ChromeperfApp.reducers.newChart.typeName,
            statePath,
            options,
          },
          {
            type: ChromeperfApp.reducers.updateLargeDom.typeName,
            appStatePath: statePath,
          },
        ],
      });
    },

    closeChart: (statePath, sectionId) => async(dispatch, getState) => {
      dispatch({
        type: ChromeperfApp.reducers.closeChart.typeName,
        statePath,
        sectionId,
      });
      cp.ChromeperfApp.actions.updateLocation(statePath)(dispatch, getState);

      await cp.timeout(5000);
      const state = Polymer.Path.get(getState(), statePath);
      if (state.closedChartIds && !state.closedChartIds.includes(sectionId)) {
        // This chart was reopened.
        return;
      }
      dispatch({
        type: ChromeperfApp.reducers.forgetClosedChart.typeName,
        statePath,
      });
    },

    closeAllCharts: statePath => async(dispatch, getState) => {
      dispatch({
        type: ChromeperfApp.reducers.closeAllCharts.typeName,
        statePath,
      });
      cp.ChromeperfApp.actions.updateLocation(statePath)(dispatch, getState);
    },

    reset: statePath => async(dispatch, getState) => {
      cp.ReportSection.actions.restoreState(`${statePath}.reportSection`, {
        sources: [cp.ReportSection.DEFAULT_NAME]
      })(dispatch, getState);
      ChromeperfApp.actions.reportSectionShowing(
          statePath, true
      )(dispatch, getState);
      ChromeperfApp.actions.closeAllAlerts(statePath)(dispatch, getState);
      ChromeperfApp.actions.closeAllCharts(statePath)(dispatch, getState);
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
        enableNav: true,
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
        alertsSectionIds: [],
        alertsSectionsById: {},
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

    closeAllAlerts: (state, action, rootState) => {
      return {
        ...state,
        alertsSectionIds: [],
        alertsSectionsById: {},
      };
    },

    newAlerts: (state, action, rootState) => {
      for (const alerts of Object.values(state.alertsSectionsById)) {
        // If the user mashes the ALERTS button, don't open copies of the same
        // alerts section.
        // TODO scroll to the matching alerts section.
        if (!cp.AlertsSection.matchesOptions(alerts, action.options)) continue;
        if (state.alertsSectionIds.includes(alerts.sectionId)) return state;
        return {
          ...state,
          closedAlertsIds: undefined,
          alertsSectionIds: [
            alerts.sectionId,
            ...state.alertsSectionIds,
          ],
        };
      }

      const sectionId = action.sectionId || tr.b.GUID.allocateSimple();
      const newSection = {
        type: cp.AlertsSection.is,
        sectionId,
        ...cp.AlertsSection.newState(action.options || {}),
      };
      const alertsSectionsById = {...state.alertsSectionsById};
      alertsSectionsById[sectionId] = newSection;
      state = {...state};
      const alertsSectionIds = Array.from(state.alertsSectionIds);
      alertsSectionIds.push(sectionId);
      return {...state, alertsSectionIds, alertsSectionsById};
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
        if (action.options.fixedXAxis !== undefined) {
          linkedChartState.linkedFixedXAxis = action.options.fixedXAxis;
        }
        if (action.options.zeroYAxis !== undefined) {
          linkedChartState.linkedZeroYAxis = action.options.zeroYAxis;
        }
        state = {...state, linkedChartState};
      }
      return {...state, chartSectionIds};
    },

    closeAlerts: (state, action, rootState) => {
      const sectionIdIndex = state.alertsSectionIds.indexOf(action.sectionId);
      const alertsSectionIds = [...state.alertsSectionIds];
      alertsSectionIds.splice(sectionIdIndex, 1);
      let closedAlertsIds;
      if (!cp.AlertsSection.isEmpty(
          state.alertsSectionsById[action.sectionId])) {
        closedAlertsIds = [action.sectionId];
      }
      return {...state, alertsSectionIds, closedAlertsIds};
    },

    forgetClosedAlerts: (state, action, rootState) => {
      const alertsSectionsById = {...state.alertsSectionsById};
      if (state.closedAlertsIds) {
        for (const id of state.closedAlertsIds) {
          delete alertsSectionsById[id];
        }
      }
      return {
        ...state,
        alertsSectionsById,
        closedAlertsIds: undefined,
      };
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
      return {...state, chartSectionIds, closedChartIds};
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
        alertsSectionIds: [],
        alertsSectionsById: {},
        chartSectionIds: [],
        chartSectionsById: {},
      };

      if (action.sessionState.alertsSections) {
        for (const options of action.sessionState.alertsSections) {
          state = ChromeperfApp.reducers.newAlerts(state, {options});
        }
      }
      if (action.sessionState.chartSections) {
        for (const options of action.sessionState.chartSections) {
          state = ChromeperfApp.reducers.newChart(state, {options});
        }
      }
      return state;
    },

    updateLargeDom: (rootState, action, rootStateAgain) => {
      const state = Polymer.Path.get(rootState, action.appStatePath);
      const sectionCount = (
        state.chartSectionIds.length + state.alertsSectionIds.length);
      return {...rootState, largeDom: (sectionCount > 3)};
    },
  };

  ChromeperfApp.getSessionState = state => {
    const alertsSections = [];
    for (const id of state.alertsSectionIds) {
      if (cp.AlertsSection.isEmpty(state.alertsSectionsById[id])) continue;
      alertsSections.push(cp.AlertsSection.getSessionState(
          state.alertsSectionsById[id]));
    }
    const chartSections = [];
    for (const id of state.chartSectionIds) {
      if (cp.ChartSection.isEmpty(state.chartSectionsById[id])) continue;
      chartSections.push(cp.ChartSection.getSessionState(
          state.chartSectionsById[id]));
    }

    return {
      enableNav: state.enableNav,
      showingReportSection: state.showingReportSection,
      reportSection: cp.ReportSection.getSessionState(
          state.reportSection),
      alertsSections,
      chartSections,
    };
  };

  cp.ElementBase.register(ChromeperfApp);

  return {
    ChromeperfApp,
  };
});
