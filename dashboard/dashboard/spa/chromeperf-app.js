/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  const CLIENT_ID =
    '62121018386-rhk28ad5lbqheinh05fgau3shotl2t6c.apps.googleusercontent.com';

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
    }

    async onReopenClosedChart_() {
    }

    async onShowReportSection_(event) {
    }

    async onNewAlertsSection_(event) {
    }

    async onNewChart_(event) {
    }

    async onCloseAllCharts_(event) {
    }

    isInternal_(userEmail) {
      return userEmail.endsWith('@google.com');
    }

    get isProduction() {
      return window.IS_PRODUCTION;
    }
  }

  ChromeperfApp.State = {
    enableNav: options => true,
    isLoading: options => true,
    readied: options => false,
    closedAlertsIds: options => undefined,
    closedChartIds: options => undefined,
    // App-route sets |route|, and redux sets |reduxRoutePath|.
    // ChromeperfApp translates between them.
    // https://stackoverflow.com/questions/41440316
    reduxRoutePath: options => '',
    vulcanizedDate: options => options.vulcanizedDate,
  };

  ChromeperfApp.properties = {
    ...cp.buildProperties('state', ChromeperfApp.State),
    route: {type: Object},
    userEmail: {statePath: 'userEmail'},
  };

  ChromeperfApp.observers = [
    'observeReduxRoute_(reduxRoutePath)',
  ];

  ChromeperfApp.actions = {
    ready: (statePath, routeParams, authParams) =>
      async(dispatch, getState) => {
        dispatch(Redux.CHAIN(
            Redux.ENSURE(statePath),
            Redux.ENSURE('userEmail', ''),
        ));

        // Wait for ChromeperfApp and its reducers to be registered.
        await cp.afterRender();

        // Create the First Contentful Paint with a placeholder table in the
        // ReportSection. ReportSection will also fetch public /api/report/names
        // without authorizationHeaders.
        dispatch({
          type: ChromeperfApp.reducers.ready.name,
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
        dispatch(Redux.UPDATE(statePath, {
          isLoading: false,
          readied: true,
        }));
      },

    reportSectionShowing: (statePath, showingReportSection) =>
      async(dispatch, getState) => {
        dispatch(Redux.UPDATE(statePath, {showingReportSection}));
      },

    onSignin: statePath => async(dispatch, getState) => {
      const user = gapi.auth2.getAuthInstance().currentUser.get();
      const response = user.getAuthResponse();
      dispatch(Redux.UPDATE('', {
        userEmail: user.getBasicProfile().getEmail(),
      }));
    },

    onSignout: () => async(dispatch, getState) => {
      dispatch(Redux.UPDATE('', {userEmail: ''}));
    },

    restoreSessionState: (statePath, sessionId) =>
      async(dispatch, getState) => {
      },

    restoreFromRoute: (statePath, routeParams) => async(dispatch, getState) => {
      const teamName = routeParams.get('team');
      if (teamName) {
        dispatch(Redux.UPDATE('', {teamName}));
      }

      if (routeParams.has('nonav')) {
        dispatch(Redux.UPDATE(statePath, {enableNav: false}));
      }

      const sessionId = routeParams.get('session');
      if (sessionId) {
        await ChromeperfApp.actions.restoreSessionState(
            statePath, sessionId)(dispatch, getState);
        return;
      }
    },

    updateLocation: statePath => async(dispatch, getState) => {
      const rootState = getState();
      const state = Polymer.Path.get(rootState, statePath);
      if (!state.readied) return;

      let routeParams;
      // TODO get routeParams from singular section

      if (routeParams === undefined) {
        return;
      }

      if (rootState.teamName) {
        routeParams.set('team', rootState.teamName);
      }
      if (!state.enableNav) {
        routeParams.set('nonav', '');
      }
      dispatch(Redux.UPDATE(statePath, {
        reduxRoutePath: routeParams.toString(),
      }));
    },

    reopenClosedAlerts: statePath => async(dispatch, getState) => {
      const state = Polymer.Path.get(getState(), statePath);
      dispatch(Redux.UPDATE(statePath, {
        alertsSectionIds: [
          ...state.alertsSectionIds,
          ...state.closedAlertsIds,
        ],
        closedAlertsIds: undefined,
      }));
    },
  };

  ChromeperfApp.reducers = {
    ready: (state, action, rootState) => {
      let vulcanizedDate = '';
      if (window.VULCANIZED_TIMESTAMP) {
        vulcanizedDate = tr.b.formatDate(new Date(
            VULCANIZED_TIMESTAMP.getTime() - (1000 * 60 * 60 * 7))) + ' PT';
      }
      return cp.buildState(ChromeperfApp.State, {vulcanizedDate});
    },
  };

  cp.ElementBase.register(ChromeperfApp);
  return {ChromeperfApp};
});
