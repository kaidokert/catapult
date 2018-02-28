/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  const MS_PER_SECOND = 1000;
  const MS_PER_MINUTE = 60 * MS_PER_SECOND;
  const MS_PER_HOUR = 60 * MS_PER_MINUTE;
  const MS_PER_DAY = 24 * MS_PER_HOUR;
  const MS_PER_MONTH = 30 * MS_PER_DAY;

  class AlertsSection extends cp.ElementBase {
    ready() {
      super.ready();
      this.scrollIntoView(true);
    }

    connectedCallback() {
      super.connectedCallback();
      this.dispatch('connected', this.statePath);
    }

    isLoading_(isLoading, isPreviewLoading) {
      return isLoading || isPreviewLoading;
    }

    canTriage_(alertGroups) {
      const selectedAlerts = AlertsSection.getSelectedAlerts(alertGroups);
      if (selectedAlerts.length === 0) return false;
      for (const alert of selectedAlerts) {
        if (alert.bugId) return false;
      }
      return true;
    }

    crbug_(bugId) {
      return `https://bugs.chromium.org/p/chromium/issues/detail?id=${bugId}`;
    }

    canUnassignAlerts_(alertGroups) {
      const selectedAlerts = AlertsSection.getSelectedAlerts(alertGroups);
      for (const alert of selectedAlerts) {
        if (alert.bugId) return true;
      }
      return false;
    }

    onUnassign_(event) {
      this.dispatch('unassignAlerts', this.statePath);
    }

    summary_(alertGroups) {
      if (!alertGroups) return '';
      const groups = alertGroups.length;
      let total = 0;
      for (const group of alertGroups) {
        total += group.alerts.length;
      }
      return (
        `${total} alert${this._plural(total)} in ` +
        `${groups} group${this._plural(groups)}`);
    }

    onSourceKeydown_(event) {
      this.dispatch('keydownSource', this.statePath, event.detail.value);
    }

    onSourceClear_(event) {
      this.dispatch('onSourceClear', this.statePath);
    }

    onSourceSelect_(event) {
      this.dispatch('loadAlerts', this.statePath);
    }

    onToggleImprovements_(event) {
      this.dispatch('toggleShowingImprovements', this.statePath);
    }

    onToggleTriaged_(event) {
      this.dispatch('toggleShowingTriaged', this.statePath);
    }

    onTapRecentBugs_(event) {
      this.dispatch('showRecentBugs', this.statePath);
    }

    onCancelTriagedNew_(event) {
      this.dispatch('cancelTriagedNew', this.statePath);
    }

    onCancelTriagedExisting_(event) {
      this.dispatch('cancelTriagedExisting', this.statePath);
    }

    onCancelIgnored_(event) {
      this.dispatch('cancelIgnored', this.statePath);
    }

    onCancelRecentBugs_(event) {
      this.dispatch('cancelRecentBugs', this.statePath);
    }

    onClose_(event) {
      this.dispatchEvent(new CustomEvent('close-section', {
        bubbles: true,
        composed: true,
        detail: {sectionId: this.sectionId},
      }));
    }

    onCharts_(event) {
      const ctrlKey = event.detail.sourceEvent.ctrlKey;
      this.dispatch('openCharts', this.statePath, ctrlKey);
    }

    onTriageNew_(event) {
      // If the user is already signed in, then require-sign-in will do nothing,
      // and openNewBugDialog will do so. If the user is not already signed in,
      // then openNewBugDialog won't, and require-sign-in will start the signin
      // flow.
      this.dispatchEvent(new CustomEvent('require-sign-in', {
        bubbles: true,
        composed: true,
      }));
      this.dispatch('openNewBugDialog', this.statePath);
    }

    onTriageExisting_(event) {
      // If the user is already signed in, then require-sign-in will do nothing,
      // and openExistingBugDialog will do so. If the user is not already signed
      // in, then openExistingBugDialog won't, and require-sign-in will start
      // the signin flow.
      this.dispatchEvent(new CustomEvent('require-sign-in', {
        bubbles: true,
        composed: true,
      }));
      this.dispatch('openExistingBugDialog', this.statePath);
    }

    onTriageNewSubmit_(event) {
      this.dispatch('submitNewBug', this.statePath);
    }

    onTriageExistingSubmit_(event) {
      this.dispatch('submitExistingBug', this.statePath);
    }

    onIgnore_(event) {
      this.dispatch('ignore', this.statePath);
    }

    onDotClick_(event) {
      this.dispatchEvent(new CustomEvent('new-section', {
        bubbles: true,
        composed: true,
        detail: {
          type: cp.ChartSection.is,
          options: {
            parameters: event.detail.line.chartParameters,
            // TODO brush event.detail.datum.chromiumCommitPositions
          },
        },
      }));
    }

    onDotMouseOver_(event) {
      this.dispatch('dotMouseOver', this.statePath, event.detail.datum);
    }

    onDotMouseOut_(event) {
      // TODO unbold row in table
    }

    onSelected_(event) {
      this.dispatch('maybeLayoutPreview', this.statePath);
    }

    onPreviewChange_() {
      this.dispatch('updateAlertColors', this.statePath);
    }

    onSort_(event) {
      this.dispatch('onSort_', this.statePath);
    }

    onHasTriaged_() {
      this.$.recent_bugs.scrollIntoView(true);
    }
  }

  AlertsSection.properties = cp.ElementBase.statePathProperties('statePath', {
    alertGroups: {type: Array},
    areAlertGroupsPlaceholders: {type: Boolean},
    hasTriagedNew: {
      type: Boolean,
      observer: 'onHasTriaged_',
    },
    hasTriagedExisting: {
      type: Boolean,
      observer: 'onHasTriaged_',
    },
    hasIgnored: {
      type: Boolean,
      observer: 'onHasTriaged_',
    },
    ignoredCount: {type: Number},
    triagedBugId: {type: Number},
    isLoading: {type: Boolean},
    isOwner: {type: Boolean},
    preview: {
      type: Object,
      observer: 'onPreviewChange_',
    },
    recentBugs: {type: Array},
    showingRecentBugs: {type: Boolean},
    sectionId: {type: String},
    selectedAlertsCount: {type: Number},
    showBugColumn: {type: Boolean},
    showMasterColumn: {type: Boolean},
    showingImprovements: {type: Boolean},
    showingTriaged: {type: Boolean},
    source: {type: Object},
  });

  AlertsSection.actions = {
    showRecentBugs: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(statePath, {
        showingRecentBugs: true,
      }));
    },

    cancelRecentBugs: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(statePath, {
        showingRecentBugs: false,
      }));
    },

    cancelTriagedNew: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(statePath, {
        hasTriagedNew: false,
      }));
    },

    cancelTriagedExisting: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(statePath, {
        hasTriagedExisting: false,
        triagedBugId: 0,
      }));
    },

    cancelIgnored: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(statePath, {
        hasIgnored: false,
      }));
    },

    updateAlertColors: statePath => async (dispatch, getState) => {
      dispatch({
        type: AlertsSection.reducers.updateAlertColors.typeName,
        statePath,
      });
    },

    unassignAlerts: statePath => async (dispatch, getState) => {
      dispatch(AlertsSection.actions.changeBugId(statePath, 0));
    },

    dotMouseOver: (statePath, datum) => async (dispatch, getState) => {
      // TODO bold row in table
    },

    onSourceClear: statePath => async (dispatch, getState) => {
      dispatch(AlertsSection.actions.loadAlerts(statePath));
      dispatch(cp.DropdownInput.actions.focus(statePath + '.source'));
    },

    connected: statePath => async (dispatch, getState) => {
      const state = Polymer.Path.get(getState(), statePath);
      if (state.source.selectedOptions.length === 0) {
        dispatch(cp.DropdownInput.actions.focus(statePath + '.source'));
      } else {
        dispatch(AlertsSection.actions.loadAlerts(statePath));
      }
      if (state.doSelectAll) {
        // TODO select all
        dispatch(cp.ElementBase.actions.updateObject(
            statePath, {doSelectAll: false}));
      }
      if (state.doOpenCharts) {
        // TODO open charts
        dispatch(cp.ElementBase.actions.updateObject(
            statePath, {doOpenCharts: false}));
      }
    },

    submitExistingBug: statePath => async (dispatch, getState) => {
      let state = Polymer.Path.get(getState(), statePath);
      const triagedBugId = state.existingBug.bugId;
      await dispatch(AlertsSection.actions.changeBugId(
          statePath, triagedBugId));
      dispatch({
        type: AlertsSection.reducers.showTriagedExisting.typeName,
        statePath,
        triagedBugId,
      });
      await tr.b.timeout(5000);
      state = Polymer.Path.get(getState(), statePath);
      if (state.triagedBugId !== triagedBugId) return;
      dispatch(AlertsSection.actions.cancelTriagedExisting(statePath));
    },

    changeBugId: (statePath, bugId) => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(
          statePath, {isLoading: true}));
      const rootState = getState();
      let state = Polymer.Path.get(rootState, statePath);
      const alerts = AlertsSection.getSelectedAlerts(state.alertGroups);
      try {
        const request = new cp.ExistingBugRequest({
          headers: rootState.authHeaders,
          alertKeys: alerts.map(a => a.key),
          bugId,
        });
        await request.response;
        dispatch({
          type: AlertsSection.reducers.removeSelectedAlerts.typeName,
          statePath,
          bugId,
        });
        state = Polymer.Path.get(getState(), statePath);
        dispatch(AlertsSection.actions.prefetchPreviewAlertGroup_(
            statePath, state.alertGroups[0]));
        dispatch(cp.ChartTimeseries.actions.load(
            `${statePath}.preview`, []));
      } catch (err) {
        // eslint-disable-next-line no-console
        console.error(err);
      }
      dispatch(cp.ElementBase.actions.updateObject(
          statePath, {isLoading: false}));
      dispatch(cp.ElementBase.actions.updateObject(
          `${statePath}.existingBug`, {isOpen: false}));
    },

    ignore: statePath => async (dispatch, getState) => {
      let state = Polymer.Path.get(getState(), statePath);
      const alerts = AlertsSection.getSelectedAlerts(state.alertGroups);
      const ignoredCount = alerts.length;
      await dispatch(AlertsSection.actions.changeBugId(statePath, -2));

      dispatch(cp.ElementBase.actions.updateObject(statePath, {
        hasTriagedExisting: false,
        hasTriagedNew: false,
        hasIgnored: true,
        ignoredCount,
      }));
      await tr.b.timeout(5000);
      state = Polymer.Path.get(getState(), statePath);
      if (state.ignoredCount !== ignoredCount) return;
      dispatch(cp.ElementBase.actions.updateObject(statePath, {
        hasIgnored: false,
        ignoredCount: 0,
      }));
    },

    openCharts: (statePath, ctrlKey) => async (dispatch, getState) => {
      const state = getState();
      const section = Polymer.Path.get(state, statePath);
      const selectedAlerts = AlertsSection.getSelectedAlerts(
          section.alertGroups);

      if (ctrlKey) {
        cp.todo('ctrl+Charts should open chart-sections in the SPA');
        for (const alert of selectedAlerts) {
          window.open(alert.v1ReportLink, '_blank');
        }
        return;
      }

      for (const alert of selectedAlerts) {
        dispatch({
          type: cp.ChromeperfApp.reducers.newSection.typeName,
          sectionType: 'chart-section',
          sectionId: tr.b.GUID.allocateSimple(),
          options: {
            parameters: {
              testSuites: [alert.testSuite],
              measurements: [alert.measurement],
              bots: [alert.bot],
              testCases: [alert.testCase],
              statistic: 'avg',
            },
            // TODO brush x axis
          },
        });
      }
    },

    openNewBugDialog: statePath => async (dispatch, getState) => {
      let userEmail = getState().userEmail;
      if (location.hostname === 'localhost') {
        userEmail = 'you@chromium.org';
      }
      if (!userEmail) return;
      dispatch({
        type: AlertsSection.reducers.openNewBugDialog.typeName,
        statePath,
        userEmail,
      });
    },

    openExistingBugDialog: statePath => async (dispatch, getState) => {
      let userEmail = getState().userEmail;
      if (location.hostname === 'localhost') {
        userEmail = 'you@chromium.org';
      }
      if (!userEmail) return;
      dispatch({
        type: AlertsSection.reducers.openExistingBugDialog.typeName,
        statePath,
      });
    },

    submitNewBug: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(
          statePath, {isLoading: true}));
      const rootState = getState();
      let state = Polymer.Path.get(rootState, statePath);
      const alerts = AlertsSection.getSelectedAlerts(state.alertGroups);
      let bugId;
      try {
        const request = new cp.NewBugRequest({
          headers: rootState.authHeaders,
          alertKeys: alerts.map(a => a.key),
          ...state.newBug,
          labels: state.newBug.labels.filter(
              x => x.isEnabled).map(x => x.name),
          components: state.newBug.components.filter(
              x => x.isEnabled).map(x => x.name),
        });
        const summary = state.newBug.summary;
        bugId = await request.response;
        dispatch({
          type: AlertsSection.reducers.showTriagedNew.typeName,
          statePath,
          bugId,
          summary,
        });
        dispatch({
          type: AlertsSection.reducers.removeSelectedAlerts.typeName,
          statePath,
          bugId,
        });
        state = Polymer.Path.get(getState(), statePath);
        dispatch(AlertsSection.actions.prefetchPreviewAlertGroup_(
            statePath, state.alertGroups[0]));
        dispatch(cp.ChartTimeseries.actions.load(
            `${statePath}.preview`, []));
      } catch (err) {
        // eslint-disable-next-line no-console
        console.error(err);
      }
      dispatch(cp.ElementBase.actions.updateObject(
          statePath, {isLoading: false}));

      if (bugId === undefined) return;
      await tr.b.timeout(5000);
      state = Polymer.Path.get(getState(), statePath);
      if (state.triagedBugId !== bugId) return;
      dispatch(cp.ElementBase.actions.updateObject(statePath, {
        hasTriagedNew: false,
        triagedBugId: 0,
      }));
    },

    keydownSource: (statePath, inputValue) => async (dispatch, getState) => {
      cp.todo('filter sources');
    },

    onSort_: statePath => async (dispatch, getState) => {
      const state = Polymer.Path.get(getState(), statePath);
      dispatch(AlertsSection.actions.prefetchPreviewAlertGroup_(
          statePath, state.alertGroups[0]));
    },

    loadAlerts: statePath => async (dispatch, getState) => {
      dispatch(cp.DropdownInput.actions.blurAll());
      dispatch({
        type: AlertsSection.reducers.startLoadingAlerts.typeName,
        statePath,
      });
      const rootState = getState();
      let state = Polymer.Path.get(rootState, statePath);

      const alerts = [];
      let recentBugs = [];
      await Promise.all(state.source.selectedOptions.map(async source => {
        // TODO cache alerts
        const request = new cp.AlertsRequest({
          headers: rootState.authHeaders,
          body: {
            improvements: state.showingImprovements ? 'true' : '',
            triaged: state.showingTriaged ? 'true' : '',
            ...AlertsSection.unpackSourceOptions(source),
          },
        });
        const response = await request.response;
        alerts.push.apply(alerts, response.anomaly_list);
        // TODO use a separate request for recent bugs
        recentBugs = response.recent_bugs;
      }));

      dispatch({
        type: AlertsSection.reducers.receiveAlerts.typeName,
        statePath,
        alerts,
        recentBugs,
      });
      state = Polymer.Path.get(getState(), statePath);
      dispatch(AlertsSection.actions.prefetchPreviewAlertGroup_(
          statePath, state.alertGroups[0]));
    },

    toggleShowingImprovements: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.toggleBoolean(
          `${statePath}.showingImprovements`));
      dispatch(AlertsSection.actions.loadAlerts(statePath));
    },

    toggleShowingTriaged: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.toggleBoolean(
          `${statePath}.showingTriaged`));
      dispatch(AlertsSection.actions.loadAlerts(statePath));
    },

    prefetchPreviewAlertGroup_: (statePath, alertGroup) =>
      async (dispatch, getState) => {
        const descriptors = [];
        for (const alert of alertGroup.alerts) {
          descriptors.push(...AlertsSection.lineDescriptorsForAlert(alert));
        }
        dispatch(cp.ChartTimeseries.actions.prefetch(
            `${statePath}.preview`, descriptors));
      },

    layoutPreview: statePath => async (dispatch, getState) => {
      const rootState = getState();
      const state = Polymer.Path.get(rootState, statePath);
      const alerts = AlertsSection.getSelectedAlerts(state.alertGroups);
      const minTimestampMs = new Date() - MS_PER_MONTH;
      const descriptors = [];
      for (const alert of alerts) {
        for (const line of AlertsSection.lineDescriptorsForAlert(alert)) {
          descriptors.push({...line, minTimestampMs});
        }
      }
      dispatch(cp.ChartTimeseries.actions.load(
          `${statePath}.preview`, descriptors, {
            fixedXAxis: true,
            normalize: true,
          }));
    },

    maybeLayoutPreview: statePath => async (dispatch, getState) => {
      const state = Polymer.Path.get(getState(), statePath);
      if (!state.selectedAlertsCount) {
        dispatch(cp.ChartTimeseries.actions.load(
            `${statePath}.preview`, []));
        return;
      }

      dispatch(AlertsSection.actions.layoutPreview(statePath));
    },
  };

  AlertsSection.lineDescriptorsForAlert = alert => {
    const descriptor = {
      baseUnit: alert.baseUnit,
      testSuites: [alert.testSuite],
      measurement: alert.measurement,
      bots: [alert.master + ':' + alert.bot],
      testCases: [alert.testCase],
      statistic: 'avg',  // TODO
    };
    return [
      {
        ...descriptor,
        icons: [  // TODO ChartTimeseries should get this from the backend
          {
            revision: alert.endRevision,
            icon: alert.improvement ? 'thumb-up' : 'error',
          },
        ],
      },
      {
        ...descriptor,
        buildType: 'reference',
      },
    ];
  };

  AlertsSection.reducers = {
    showTriagedNew: cp.ElementBase.statePathReducer((state, action) => {
      return {
        ...state,
        hasTriagedExisting: false,
        hasTriagedNew: true,
        hasIgnored: false,
        triagedBugId: action.bugId,
        recentBugs: [
          {
            id: action.bugId,
            summary: action.summary,
          },
          ...state.recentBugs,
        ],
      };
    }),

    showTriagedExisting: cp.ElementBase.statePathReducer((state, action) => {
      const recentBugs = state.recentBugs.filter(bug =>
        bug.id !== action.triagedBugId);
      let triagedBugSummary = '(TODO fetch bug summary)';
      for (const bug of state.existingBug.recentBugs) {
        if (bug.id === action.triagedBugId) {
          triagedBugSummary = bug.summary;
          break;
        }
      }
      recentBugs.unshift({
        id: action.triagedBugId,
        summary: triagedBugSummary,
      });
      return {
        ...state,
        hasTriagedExisting: true,
        hasTriagedNew: false,
        hasIgnored: false,
        triagedBugId: action.triagedBugId,
        recentBugs,
      };
    }),

    updateAlertColors: cp.ElementBase.statePathReducer((state, action) => {
      const colorByDescriptor = new Map();
      for (const line of state.preview.lines) {
        colorByDescriptor.set(cp.ChartTimeseries.stringifyDescriptor(
            line.descriptor), line.color);
      }
      return {
        ...state,
        alertGroups: state.alertGroups.map(alertGroup => {
          return {
            ...alertGroup,
            alerts: alertGroup.alerts.map(alert => {
              const descriptor = cp.ChartTimeseries.stringifyDescriptor(
                  AlertsSection.lineDescriptorsForAlert(alert)[0]);
              return {
                ...alert,
                color: colorByDescriptor.get(descriptor),
              };
            }),
          };
        }),
      };
    }),

    removeSelectedAlerts: cp.ElementBase.statePathReducer((state, action) => {
      const alertGroups = [];
      for (const group of state.alertGroups) {
        let alerts = group.alerts;
        if (state.showingTriaged) {
          alerts = alerts.map(alert => {
            return {
              ...alert,
              bugId: action.bugId,
            };
          });
        } else {
          alerts = alerts.filter(a => !a.isSelected);
          if (alerts.length === 0) continue;
        }
        alertGroups.push({...group, alerts});
      }
      return {
        ...state,
        alertGroups,
        selectedAlertsCount: 0,
      };
    }),

    openNewBugDialog: cp.ElementBase.statePathReducer((state, action) => {
      const alerts = AlertsSection.getSelectedAlerts(state.alertGroups);
      return {
        ...state,
        newBug: cp.TriageNew.newState(alerts, action.userEmail),
      };
    }),

    openExistingBugDialog: cp.ElementBase.statePathReducer((state, action) => {
      const alerts = AlertsSection.getSelectedAlerts(state.alertGroups);
      return {
        ...state,
        existingBug: {
          ...state.existingBug,
          ...cp.TriageExisting.openState(alerts),
        },
      };
    }),

    receiveAlerts: cp.ElementBase.statePathReducer((state, action) => {
      const recentBugs = action.recentBugs.map(AlertsSection.transformBug);

      if (!action.alerts.length) {
        state = {
          ...state,
          alertGroups: PLACEHOLDER_ALERT_GROUPS,
          areAlertGroupsPlaceholders: true,
          isLoading: false,
          isOwner: false,
          existingBug: {
            ...state.existingBug,
            recentBugs,
          },
          selectedAlertsCount: 0,
          showBugColumn: true,
          showMasterColumn: true,
          showTestCaseColumn: true,
        };
        if (state.source.selectedOptions.length === 0) return state;
        return {
          ...state,
          alertGroups: [],
          areAlertGroupsPlaceholders: false,
        };
      }

      let alertGroups = d.groupAlerts(action.alerts);
      alertGroups = alertGroups.map((alerts, groupIndex) => {
        return {
          isExpanded: false,
          alerts: alerts.map(AlertsSection.transformAlert),
        };
      });

      alertGroups = AlertsSection.sortGroups(
          alertGroups, state.sortColumn, state.sortDescending);

      // Don't automatically select the first group. Users often want to sort
      // the table by some column before previewing any alerts.

      // Hide the Bug, Master, and Test Case columns if they're boring.
      const bugs = new Set();
      const masters = new Set();
      const testCases = new Set();
      for (const group of alertGroups) {
        for (const alert of group.alerts) {
          bugs.add(alert.bugId);
          masters.add(alert.master);
          testCases.add(alert.testCase);
        }
      }

      return {
        ...state,
        alertGroups,
        areAlertGroupsPlaceholders: false,
        isLoading: false,
        isOwner: Math.random() < 0.5,
        selectedAlertsCount: 0,
        showBugColumn: bugs.size > 1,
        showMasterColumn: masters.size > 1,
        showTestCaseColumn: testCases.size > 1,
        existingBug: {
          ...state.existingBug,
          recentBugs,
        }
      };
    }),

    startLoadingAlerts: cp.ElementBase.statePathReducer((state, action) => {
      return {
        ...state,
        isLoading: true,
        source: {
          ...state.source,
          inputValue: state.source.selectedOptions.join(', '),
        },
      };
    }),
  };

  AlertsSection.newStateOptionsFromQueryParams = queryParams => {
    const options = {
      sources: [],
      sortColumn: 'revisions',
      showingImprovements: false,
      showingTriaged: false,
      sortDescending: false,
      doOpenCharts: false,
      doSelectAll: false,
    };
    for (const [name, value] of Object.entries(queryParams)) {
      if (name === 'descending') {
        options.sortDescending = true;
      } else if (name === 'sort') {
        options.sortColumn = value;
      } else if (name === 'improvements') {
        options.showingImprovements = true;
      } else if (name === 'triaged') {
        options.showingTriaged = true;
      } else if (name === 'charts') {
        options.doOpenCharts = true;
      } else if (name === 'bug') {
        options.sources.push(value.split(',').map(bug => 'Bug:' + bug));
      } else if (name === 'releasing') {
        options.sources.push(value.split(',').map(releasing =>
          'Releasing:' + releasing.replace(/_/g, ':')));
      } else if (name === 'sheriff') {
        options.sources.push(value.replace(/_/g, ' '));
      }
    }
    return options;
  };

  const PLACEHOLDER_ALERT_GROUPS = [];
  const DASHES = '-'.repeat(5);
  for (let i = 0; i < 5; ++i) {
    PLACEHOLDER_ALERT_GROUPS.push({
      isSelected: false,
      alerts: [
        {
          bugId: DASHES,
          revisions: DASHES,
          testSuite: DASHES,
          measurement: DASHES,
          master: DASHES,
          bot: DASHES,
          testCase: DASHES,
          deltaValue: 0,
          deltaUnit: tr.b.Unit.byName.countDelta_biggerIsBetter,
          percentDeltaValue: 0,
          percentDeltaUnit:
            tr.b.Unit.byName.normalizedPercentageDelta_biggerIsBetter,
        },
      ],
    });
  }

  AlertsSection.newState = options => {
    const sources = options.sources || [];
    let anyBug = false;
    let anyReleasing = false;
    let anySheriff = false;
    for (const source of sources) {
      if (source.startsWith('Releasing')) {
        anyReleasing = true;
      } else if (source.startsWith('Bug')) {
        anyBug = true;
      } else {
        anySheriff = true;
      }
    }
    const sourceOptions = cp.dummyAlertsSources();
    for (const option of sourceOptions) {
      if ((option.label === 'Bug' && anyBug) ||
          (option.label === 'Releasing' && anyReleasing)) {
        option.isExpanded = true;
      } else if (option.label === 'Sheriff' && !anySheriff &&
                 (anyBug || anyReleasing)) {
        option.isExpanded = false;
      }
    }
    const chartState = cp.ChartTimeseries.newState();

    return {
      alertGroups: PLACEHOLDER_ALERT_GROUPS,
      areAlertGroupsPlaceholders: true,
      doOpenCharts: options.doOpenCharts || false,
      doSelectAll: options.doSelectAll || false,
      existingBug: cp.TriageExisting.DEFAULT_STATE,
      hasTriagedNew: false,
      hasTriagedExisting: false,
      hasIgnored: false,
      ignoredCount: 0,
      triagedBugId: 0,
      isLoading: false,
      isOwner: false,
      newBug: {isOpen: false},
      preview: {
        ...chartState,
        xAxis: {...chartState.xAxis, generateTicks: false},
        yAxis: {...chartState.yAxis, generateTicks: false},
      },
      previousSelectedAlertKey: undefined,
      recentBugs: [],
      selectedAlertsCount: 0,
      showBugColumn: true,
      showMasterColumn: true,
      showTestCaseColumn: true,
      showingImprovements: options.showingImprovements || false,
      showingTriaged: options.showingTriaged || false,
      sortColumn: options.sortColumn || 'revisions',
      sortDescending: options.sortDescending || false,
      source: {
        label: 'Source',
        inputValue: '',
        selectedOptions: sources,
        options: sourceOptions,
      },
    };
  };

  AlertsSection.getSelectedAlerts = alertGroups => {
    const selectedAlerts = [];
    for (const alertGroup of alertGroups) {
      for (const alert of alertGroup.alerts) {
        if (alert.isSelected) {
          selectedAlerts.push(alert);
        }
      }
    }
    return selectedAlerts;
  };

  AlertsSection.compareAlerts = (alertA, alertB, sortColumn) => {
    switch (sortColumn) {
      case 'bug': return alertA.bugId - alertB.bugId;
      case 'revisions': return alertA.startRevision - alertB.startRevision;
      case 'testSuite':
        return alertA.testSuite.localeCompare(alertB.testSuite);
      case 'master': return alertA.master.localeCompare(alertB.master);
      case 'bot': return alertA.bot.localeCompare(alertB.bot);
      case 'measurement':
        return alertA.measurement.localeCompare(alertB.measurement);
      case 'testCase':
        return alertA.testCase.localeCompare(alertB.testCase);
      case 'delta': return alertA.deltaValue - alertB.deltaValue;
      case 'deltaPct':
        return Math.abs(alertA.percentDeltaValue) -
          Math.abs(alertB.percentDeltaValue);
    }
  };

  AlertsSection.sortGroups = (alertGroups, sortColumn, sortDescending) => {
    const factor = sortDescending ? -1 : 1;
    alertGroups = alertGroups.map(group => {
      const alerts = Array.from(group.alerts);
      alerts.sort((alertA, alertB) => factor * AlertsSection.compareAlerts(
          alertA, alertB, sortColumn));
      return {
        ...group,
        alerts,
      };
    });
    alertGroups.sort((groupA, groupB) => factor * AlertsSection.compareAlerts(
        groupA.alerts[0], groupB.alerts[0], sortColumn));
    return alertGroups;
  };

  AlertsSection.transformAlert = alert => {
    let deltaValue = alert.median_after_anomaly -
      alert.median_before_anomaly;
    const percentDeltaValue = deltaValue / alert.median_before_anomaly;

    let improvementDirection = tr.b.ImprovementDirection.BIGGER_IS_BETTER;
    if (alert.improvement === (deltaValue < 0)) {
      improvementDirection = tr.b.ImprovementDirection.SMALLER_IS_BETTER;
    }
    const unitSuffix = tr.b.Unit.nameSuffixForImprovementDirection(
        improvementDirection);

    let unitName = 'unitlessNumber';
    if (tr.b.Unit.byName[alert.units + unitSuffix]) {
      unitName = alert.units;
    } else {
      const info = tr.v.LEGACY_UNIT_INFO.get(alert.units);
      if (info) {
        unitName = info.name;
        deltaValue *= info.conversionFactor || 1;
      }
    }
    const baseUnit = tr.b.Unit.byName[unitName + unitSuffix];

    const testParts = alert.test.split('/');
    let testCase = testParts.slice(1).join('/');
    if (testParts.length > 2 && testParts[2].startsWith(testParts[1])) {
      // Drop redundant legacy test path components.
      testCase = testParts.slice(2).join('/');
    }
    if (alert.testsuite.startsWith('system_health')) {
      testCase = testCase.replace(/_/g, ':');
    }

    return {
      baseUnit,
      bot: alert.bot,
      bugComponents: alert.bug_components,
      bugId: alert.bug_id === undefined ? '' : alert.bug_id,
      bugLabels: alert.bug_labels,
      deltaUnit: baseUnit.correspondingDeltaUnit,
      deltaValue,
      key: alert.key,
      improvement: alert.improvement,
      isSelected: false,
      master: alert.master,
      measurement: testParts[0],
      percentDeltaUnit: tr.b.Unit.byName[
          'normalizedPercentageDelta' + unitSuffix],
      percentDeltaValue,
      startRevision: alert.start_revision,
      endRevision: alert.end_revision,
      testCase,
      testSuite: alert.testsuite,
      v1ReportLink: alert.dashboard_link,
    };
  };

  AlertsSection.transformBug = bug => {
    // Save memory by stripping out all the unnecessary data.
    // TODO save bandwidth by stripping out the unnecessary data in the
    // backend request handler.
    let revisionRange = bug.summary.match(/.* (\d+):(\d+)$/);
    if (revisionRange === null) {
      revisionRange = new tr.b.math.Range();
    } else {
      revisionRange = tr.b.math.Range.fromExplicitRange(
          parseInt(revisionRange[1]), parseInt(revisionRange[2]));
    }
    return {
      id: '' + bug.id,
      status: bug.status,
      owner: bug.owner ? bug.owner.name : '',
      summary: cp.AlertsSection.breakWords(bug.summary),
      revisionRange,
    };
  };

  AlertsSection.unpackSourceOptions = source => {
    let sheriff;
    let bugId;
    let releasingReport;
    let milestone;
    const sourceParts = source.split(':');
    const sourceType = sourceParts[0];
    if (sourceParts.length === 1) {
      sheriff = sourceType;
    } else if (sourceType === 'Bug') {
      bugId = sourceParts[1];
    } else if (sourceType === 'Releasing') {
      milestone = sourceParts[1];
      releasingReport = sourceParts[2];
    }
    return {
      sheriff,
      bugId,
      milestone,
      releasingReport,
    };
  };

  const ZERO_WIDTH_SPACE = String.fromCharCode(0x200b);

  AlertsSection.breakWords = str => {
    if (str === undefined) return '';

    // Insert spaces before underscores.
    str = str.replace(/_/g, ZERO_WIDTH_SPACE + '_');

    // Insert spaces after colons and dots.
    str = str.replace(/\./g, '.' + ZERO_WIDTH_SPACE);
    str = str.replace(/:/g, ':' + ZERO_WIDTH_SPACE);

    // Insert spaces before camel-case words.
    str = str.split(/([a-z][A-Z])/g);
    str = str.map((s, i) => {
      if ((i % 2) === 0) return s;
      return s[0] + ZERO_WIDTH_SPACE + s[1];
    });
    str = str.join('');
    return str;
  };

  AlertsSection.getSessionState = state => {
    return {
      sources: state.source.selectedOptions,
      showingImprovements: state.showingImprovements,
      showingTriaged: state.showingTriaged,
      sortColumn: state.sortColumn,
      sortDescending: state.sortDescending,
    };
  };

  AlertsSection.getQueryParams = state => {
    const queryParams = {
      bug: [],
      releasing: [],
      sheriff: [],
    };
    for (const source of state.source.selectedOptions) {
      if (source.startsWith('Bug:')) {
        queryParams.bug.push(source.split(':')[1]);
      } else if (source.startsWith('Releasing:')) {
        queryParams.releasing.push(source.split(':').slice(1).join(':'));
      } else {
        queryParams.sheriff.push(source.replace(/ /g, '_'));
      }
    }
    queryParams.bug = queryParams.bug.join(',');
    queryParams.releasing = queryParams.releasing.join(',');
    queryParams.sheriff = queryParams.sheriff.join(',');
    if (!queryParams.bug) delete queryParams.bug;
    if (!queryParams.releasing) delete queryParams.releasing;
    if (!queryParams.sheriff) delete queryParams.sheriff;
    if (state.showingImprovements) queryParams.improvements = '';
    if (state.showingTriaged) queryParams.triaged = '';
    if (state.sortColumn !== 'revisions') queryParams.sort = state.sortColumn;
    if (state.sortDescending) queryParams.descending = '';
    return queryParams;
  };

  cp.ElementBase.register(AlertsSection);

  return {
    AlertsSection,
  };
});
