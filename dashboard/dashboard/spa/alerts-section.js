/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class AlertsSection extends cp.ElementBase {
    ready() {
      super.ready();
      this.scrollIntoView(true);
    }

    async connectedCallback() {
      super.connectedCallback();
      this.dispatch('connected', this.statePath);
    }

    isLoading_(isLoading, isPreviewLoading) {
      return isLoading || isPreviewLoading;
    }

    allTriaged_(alertGroups, showingTriaged) {
      if (showingTriaged) return alertGroups.length === 0;
      return alertGroups.filter(group =>
        group.alerts.length > group.triaged.count).length === 0;
    }

    canTriage_(alertGroups) {
      const selectedAlerts = AlertsSection.getSelectedAlerts(alertGroups);
      if (selectedAlerts.length === 0) return false;
      for (const alert of selectedAlerts) {
        if (alert.bugId) return false;
      }
      return true;
    }

    canUnassignAlerts_(alertGroups) {
      const selectedAlerts = AlertsSection.getSelectedAlerts(alertGroups);
      for (const alert of selectedAlerts) {
        if (alert.bugId) return true;
      }
      return false;
    }

    async onSources_(event) {
      await this.dispatch('loadAlerts', this.statePath, event.detail.sources);
    }

    async onUnassign_(event) {
      await this.dispatch('changeBugId', this.statePath, 0);
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

    onSelected_(event) {
      this.dispatch('maybeLayoutPreview', this.statePath);
    }

    onSelectAlert_(event) {
      this.dispatch('selectAlert', this.statePath,
          event.detail.alertGroupIndex, event.detail.alertIndex);
    }

    onSort_(event) {
      this.dispatch('prefetchPreviewAlertGroup', this.statePath,
          this.alertGroups[0]);
    }
  }

  AlertsSection.State = {
    ...cp.AlertsTable.State,
    ...cp.AlertsControls.State,
    existingBug: options => cp.TriageExisting.buildState({}),
    isLoading: options => false,
    newBug: options => cp.TriageNew.buildState({}),
    preview: options => cp.ChartPair.buildState(options),
    sectionId: options => 0,
    selectedAlertPath: options => undefined,
    selectedAlertsCount: options => 0,
  };

  AlertsSection.buildState = options =>
    cp.buildState(AlertsSection.State, options);

  AlertsSection.properties = {
    ...cp.buildProperties('state', AlertsSection.State),
    ...cp.buildProperties('linkedState', {
      // AlertsSection only needs the linkedStatePath property to forward to
      // ChartPair.
    }),
  };

  AlertsSection.actions = {
    selectAlert: (statePath, alertGroupIndex, alertIndex) =>
      async(dispatch, getState) => {
        dispatch({
          type: AlertsSection.reducers.selectAlert.name,
          statePath,
          alertGroupIndex,
          alertIndex,
        });
      },

    cancelTriagedExisting: statePath => async(dispatch, getState) => {
      dispatch(Redux.UPDATE(statePath, {
        hasTriagedExisting: false,
        triagedBugId: 0,
      }));
    },

    connected: statePath => async(dispatch, getState) => {
      const state = Polymer.Path.get(getState(), statePath);
      if (state &&
          (state.sheriff.selectedOptions.length > 0 ||
           state.bug.selectedOptions.length > 0 ||
           state.report.selectedOptions.length > 0)) {
        dispatch(AlertsSection.actions.loadAlerts(statePath));
      }
    },

    restoreState: (statePath, options) => async(dispatch, getState) => {
      // Don't use buildState, which would drop state that was computed/fetched
      // in actions.connected.
      dispatch({
        type: AlertsSection.reducers.restoreState.name,
        statePath,
        options,
      });
      const state = Polymer.Path.get(getState(), statePath);
      if (state.sheriff.selectedOptions.length > 0 ||
          state.bug.selectedOptions.lenght > 0) {
        dispatch(AlertsSection.actions.loadAlerts(statePath));
      } else {
        dispatch(cp.MenuInput.actions.focus(statePath + '.sheriff'));
      }
    },

    submitExistingBug: statePath => async(dispatch, getState) => {
      let state = Polymer.Path.get(getState(), statePath);
      const triagedBugId = state.existingBug.bugId;
      dispatch(Redux.UPDATE(`${statePath}.existingBug`, {isOpen: false}));
      await dispatch(AlertsSection.actions.changeBugId(
          statePath, triagedBugId));
      dispatch({
        type: AlertsSection.reducers.showTriagedExisting.name,
        statePath,
        triagedBugId,
      });

      // Persist recentlyModifiedBugs to localStorage.
      state = Polymer.Path.get(getState(), statePath);
      localStorage.setItem('recentlyModifiedBugs', JSON.stringify(
          state.recentlyModifiedBugs));

      await cp.timeout(5000);
      state = Polymer.Path.get(getState(), statePath);
      if (state.triagedBugId !== triagedBugId) return;
      dispatch(AlertsSection.actions.cancelTriagedExisting(statePath));
    },

    changeBugId: (statePath, bugId) => async(dispatch, getState) => {
      dispatch(Redux.UPDATE(statePath, {isLoading: true}));
      const rootState = getState();
      let state = Polymer.Path.get(rootState, statePath);
      const selectedAlerts = AlertsSection.getSelectedAlerts(state.alertGroups);
      const alertKeys = new Set(selectedAlerts.map(a => a.key));
      try {
        const request = new ExistingBugRequest({alertKeys, bugId});
        await request.response;
        dispatch({
          type: AlertsSection.reducers.removeOrUpdateAlerts.name,
          statePath,
          alertKeys,
          bugId,
        });

        state = Polymer.Path.get(getState(), statePath);
        dispatch(AlertsSection.actions.prefetchPreviewAlertGroup(
            statePath, state.alertGroups[0]));
        if (bugId !== 0) {
          dispatch(Redux.UPDATE(`${statePath}.preview`, {lineDescriptors: []}));
        }
      } catch (err) {
        // eslint-disable-next-line no-console
        console.error(err);
      }
      dispatch(Redux.UPDATE(statePath, {isLoading: false}));
    },

    ignore: statePath => async(dispatch, getState) => {
      let state = Polymer.Path.get(getState(), statePath);
      const alerts = AlertsSection.getSelectedAlerts(state.alertGroups);
      const ignoredCount = alerts.length;
      await dispatch(AlertsSection.actions.changeBugId(statePath, -2));

      dispatch(Redux.UPDATE(statePath, {
        hasTriagedExisting: false,
        hasTriagedNew: false,
        hasIgnored: true,
        ignoredCount,
      }));
      await cp.timeout(5000);
      state = Polymer.Path.get(getState(), statePath);
      if (state.ignoredCount !== ignoredCount) return;
      dispatch(Redux.UPDATE(statePath, {
        hasIgnored: false,
        ignoredCount: 0,
      }));
    },

    openNewBugDialog: statePath => async(dispatch, getState) => {
      let userEmail = getState().userEmail;
      if (window.IS_DEBUG) {
        userEmail = 'you@chromium.org';
      }
      if (!userEmail) return;
      dispatch({
        type: AlertsSection.reducers.openNewBugDialog.name,
        statePath,
        userEmail,
      });
    },

    openExistingBugDialog: statePath => async(dispatch, getState) => {
      let userEmail = getState().userEmail;
      if (window.IS_DEBUG) {
        userEmail = 'you@chromium.org';
      }
      if (!userEmail) return;
      dispatch({
        type: AlertsSection.reducers.openExistingBugDialog.name,
        statePath,
      });
    },

    submitNewBug: statePath => async(dispatch, getState) => {
      dispatch(Redux.UPDATE(statePath, {isLoading: true}));
      const rootState = getState();
      let state = Polymer.Path.get(rootState, statePath);
      const selectedAlerts = AlertsSection.getSelectedAlerts(state.alertGroups);
      const alertKeys = new Set(selectedAlerts.map(a => a.key));
      let bugId;
      try {
        const request = new NewBugRequest({
          alertKeys,
          ...state.newBug,
          labels: state.newBug.labels.filter(
              x => x.isEnabled).map(x => x.name),
          components: state.newBug.components.filter(
              x => x.isEnabled).map(x => x.name),
        });
        const summary = state.newBug.summary;
        bugId = await request.response;
        dispatch({
          type: AlertsSection.reducers.showTriagedNew.name,
          statePath,
          bugId,
          summary,
        });

        // Persist recentlyModifiedBugs to localStorage.
        state = Polymer.Path.get(getState(), statePath);
        localStorage.setItem('recentlyModifiedBugs', JSON.stringify(
            state.recentlyModifiedBugs));

        dispatch({
          type: AlertsSection.reducers.removeOrUpdateAlerts.name,
          statePath,
          alertKeys,
          bugId,
        });
        state = Polymer.Path.get(getState(), statePath);
        dispatch(AlertsSection.actions.prefetchPreviewAlertGroup(
            statePath, state.alertGroups[0]));
        dispatch(Redux.UPDATE(`${statePath}.preview`, {lineDescriptors: []}));
      } catch (err) {
        // eslint-disable-next-line no-console
        console.error(err);
      }
      dispatch(Redux.UPDATE(statePath, {isLoading: false}));

      if (bugId === undefined) return;
      await cp.timeout(5000);
      state = Polymer.Path.get(getState(), statePath);
      if (state.triagedBugId !== bugId) return;
      dispatch(Redux.UPDATE(statePath, {
        hasTriagedNew: false,
        triagedBugId: 0,
      }));
    },

    loadAlerts: statePath => async(dispatch, getState) => {
      dispatch({
        type: AlertsSection.reducers.startLoadingAlerts.name,
        statePath,
      });
      const rootState = getState();
      let state = Polymer.Path.get(rootState, statePath);

      const alerts = [];
      const errors = [];
      const revisions = {};
      if (state.minRevision && state.minRevision.match(/^\d+$/)) {
        revisions.min_end_revision = parseInt(state.minRevision);
      }
      if (state.maxRevision && state.maxRevision.match(/^\d+$/)) {
        revisions.max_start_revision = parseInt(state.maxRevision);
      }
      const sources = [
        ...state.sheriff.selectedOptions.map(sheriff => {
          const options = {sheriff, limit: 2000, ...revisions};
          if (!state.showingImprovements) {
            options.is_improvement = 'false';
          }
          return options;
        }),
        ...state.bug.selectedOptions.map(bug => {
          return {bug_id: bug, ...revisions};
        }),
      ];
      if (state.report.selectedOptions.length) {
        const reportTemplateInfos = await new cp.ReportNamesRequest().response;
        for (const name of state.report.selectedOptions) {
          for (const reportId of reportTemplateInfos) {
            if (reportId.name === name) {
              sources.push({report: reportId.id, ...revisions});
              break;
            }
          }
        }
      }
      if (sources.length > 0) {
        dispatch(cp.MenuInput.actions.blurAll());
      }
      await Promise.all(sources.map(async body => {
        const request = new cp.AlertsRequest({body});
        try {
          const response = await request.response;
          alerts.push.apply(alerts, response.anomalies);
        } catch (err) {
          errors.push('Failed to fetch alerts: ' + err);
        }
      }));

      dispatch({
        type: AlertsSection.reducers.receiveAlerts.name,
        statePath,
        alerts,
        errors,
      });
      state = Polymer.Path.get(getState(), statePath);
      if (!state.areAlertGroupsPlaceholders) {
        dispatch(AlertsSection.actions.prefetchPreviewAlertGroup(
            statePath, state.alertGroups[0]));
      }
    },

    prefetchPreviewAlertGroup: (statePath, alertGroup) =>
      async(dispatch, getState) => {
        if (!alertGroup) return;
        const testSuites = new Set();
        const lineDescriptors = [];
        for (const alert of alertGroup.alerts) {
          testSuites.add(alert.testSuite);
          lineDescriptors.push(AlertsSection.computeLineDescriptor(alert));
        }
        dispatch(cp.ChartTimeseries.actions.prefetch(
            `${statePath}.preview`, lineDescriptors));
        await Promise.all([...testSuites].map(testSuite =>
          new cp.DescribeRequest({testSuite}).response));
      },

    layoutPreview: statePath => async(dispatch, getState) => {
      const rootState = getState();
      const state = Polymer.Path.get(rootState, statePath);
      const alerts = AlertsSection.getSelectedAlerts(state.alertGroups);
      const lineDescriptors = alerts.map(AlertsSection.computeLineDescriptor);
      if (lineDescriptors.length === 1) {
        lineDescriptors.push({
          ...lineDescriptors[0],
          buildType: 'ref',
        });
      }
      dispatch(Redux.UPDATE(`${statePath}.preview`, {lineDescriptors}));

      const testSuites = new Set();
      for (const descriptor of lineDescriptors) {
        testSuites.add(descriptor.testSuites[0]);
      }
      await Promise.all([...testSuites].map(testSuite =>
        new cp.DescribeRequest({testSuite}).response));
    },

    maybeLayoutPreview: statePath => async(dispatch, getState) => {
      const state = Polymer.Path.get(getState(), statePath);
      if (!state.selectedAlertsCount) {
        dispatch(Redux.UPDATE(`${statePath}.preview`, {lineDescriptors: []}));
        return;
      }

      dispatch(AlertsSection.actions.layoutPreview(statePath));
    },
  };

  AlertsSection.computeLineDescriptor = alert => {
    return {
      baseUnit: alert.baseUnit,
      testSuites: [alert.testSuite],
      measurement: alert.measurement,
      bots: [alert.master + ':' + alert.bot],
      testCases: [alert.testCase],
      statistic: 'avg', // TODO
      buildType: 'test',
    };
  };

  AlertsSection.reducers = {
    selectAlert: (state, action, rootState) => {
      if (state.areAlertGroupsPlaceholders) return state;
      const alertPath =
        `alertGroups.${action.alertGroupIndex}.alerts.${action.alertIndex}`;
      const alert = Polymer.Path.get(state, alertPath);
      if (!alert.isSelected) {
        state = cp.setImmutable(
            state, `${alertPath}.isSelected`, true);
      }
      if (state.selectedAlertPath === alertPath) {
        return {
          ...state,
          selectedAlertPath: undefined,
          preview: {
            ...state.preview,
            lineDescriptors: AlertsSection.getSelectedAlerts(
                state.alertGroups).map(AlertsSection.computeLineDescriptor),
          },
        };
      }
      return {
        ...state,
        selectedAlertPath: alertPath,
        preview: {
          ...state.preview,
          lineDescriptors: [AlertsSection.computeLineDescriptor(alert)],
        },
      };
    },

    restoreState: (state, action, rootState) => {
      if (!action.options) return state;
      if (action.options.sheriffs) {
        const sheriff = {...state.sheriff};
        sheriff.selectedOptions = action.options.sheriffs;
        state = {...state, sheriff};
      }
      if (action.options.bugs) {
        const bug = {...state.bug};
        bug.selectedOptions = action.options.bugs;
        state = {...state, bug};
      }
      return {
        ...state,
        showingImprovements: action.options.showingImprovements || false,
        showingTriaged: action.options.showingTriaged || false,
        sortColumn: action.options.sortColumn || 'revisions',
        sortDescending: action.options.sortDescending || false,
      };
    },

    showTriagedNew: (state, action, rootState) => {
      return {
        ...state,
        hasTriagedExisting: false,
        hasTriagedNew: true,
        hasIgnored: false,
        triagedBugId: action.bugId,
        recentlyModifiedBugs: [
          {
            id: action.bugId,
            summary: action.summary,
          },
          ...state.recentlyModifiedBugs,
        ],
      };
    },

    showTriagedExisting: (state, action, rootState) => {
      const recentlyModifiedBugs = state.recentlyModifiedBugs.filter(bug =>
        bug.id !== action.triagedBugId);
      let triagedBugSummary = '(TODO fetch bug summary)';
      for (const bug of rootState.recentPerformanceBugs) {
        if (bug.id === action.triagedBugId) {
          triagedBugSummary = bug.summary;
          break;
        }
      }
      recentlyModifiedBugs.unshift({
        id: action.triagedBugId,
        summary: triagedBugSummary,
      });
      return {
        ...state,
        hasTriagedExisting: true,
        hasTriagedNew: false,
        hasIgnored: false,
        triagedBugId: action.triagedBugId,
        recentlyModifiedBugs,
      };
    },

    updateAlertColors: (state, action, rootState) => {
      const colorByDescriptor = new Map();
      for (const line of state.preview.chartLayout.lines) {
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
                  AlertsSection.computeLineDescriptor(alert));
              return {
                ...alert,
                color: colorByDescriptor.get(descriptor),
              };
            }),
          };
        }),
      };
    },

    updateSelectedAlertsCount: state => {
      const selectedAlertsCount = AlertsSection.getSelectedAlerts(
          state.alertGroups).length;
      return {...state, selectedAlertsCount};
    },

    removeAlerts: (state, {alertKeys}, rootState) => {
      const alertGroups = [];
      for (const group of state.alertGroups) {
        const alerts = group.alerts.filter(a => !alertKeys.has(a.key));
        if (alerts.filter(a => !a.bugId).length) {
          alertGroups.push({...group, alerts});
        }
      }
      state = {...state, alertGroups};
      return AlertsSection.reducers.updateSelectedAlertsCount(state);
    },

    updateBugId: (state, {alertKeys, bugId}, rootState) => {
      if (bugId === 0) bugId = '';
      const alertGroups = state.alertGroups.map(alertGroup => {
        const alerts = alertGroup.alerts.map(a =>
          (alertKeys.has(a.key) ? {...a, bugId} : a));
        return {...alertGroup, alerts};
      });
      state = {...state, alertGroups};
      return AlertsSection.reducers.updateSelectedAlertsCount(state);
    },

    removeOrUpdateAlerts: (state, action, rootState) => {
      if (state.showingTriaged || action.bugId === 0) {
        return AlertsSection.reducers.updateBugId(state, action, rootState);
      }
      return AlertsSection.reducers.removeAlerts(state, action, rootState);
    },

    openNewBugDialog: (state, action, rootState) => {
      const alerts = AlertsSection.getSelectedAlerts(state.alertGroups);
      if (alerts.length === 0) return state;
      const newBug = cp.TriageNew.buildState({
        isOpen: true, alerts, cc: action.userEmail,
      });
      return {...state, newBug};
    },

    openExistingBugDialog: (state, action, rootState) => {
      const alerts = AlertsSection.getSelectedAlerts(state.alertGroups);
      if (alerts.length === 0) return state;
      return {
        ...state,
        existingBug: {
          ...state.existingBug,
          ...cp.TriageExisting.buildState({alerts, isOpen: true}),
        },
      };
    },

    receiveAlerts: (state, action, rootState) => {
      state = {
        ...state,
        isLoading: false,
        selectedAlertsCount: 0,
      };

      if (!action.alerts.length) {
        state = {
          ...state,
          alertGroups: cp.AlertsTable.PLACEHOLDER_ALERT_GROUPS,
          areAlertGroupsPlaceholders: true,
          showBugColumn: true,
          showMasterColumn: true,
          showTestCaseColumn: true,
        };
        if (state.sheriff.selectedOptions.length === 0 &&
            state.bug.selectedOptions.length === 0 &&
            state.report.selectedOptions.length === 0) {
          return state;
        }
        return {
          ...state,
          alertGroups: [],
          areAlertGroupsPlaceholders: false,
        };
      }

      let alertGroups = d.groupAlerts(action.alerts, state.showingTriaged);
      alertGroups = alertGroups.map((alerts, groupIndex) => {
        alerts = alerts.map(AlertsSection.transformAlert);
        return {
          isExpanded: false,
          alerts,
          triaged: {
            isExpanded: false,
            count: alerts.filter(a => a.bugId).length,
          }
        };
      });

      alertGroups = AlertsSection.sortGroups(
          alertGroups, state.sortColumn, state.sortDescending,
          state.showingTriaged);

      // Don't automatically select the first group. Users often want to sort
      // the table by some column before previewing any alerts.

      return AlertsSection.reducers.updateColumns({
        ...state, alertGroups, areAlertGroupsPlaceholders: false,
      });
    },

    updateColumns: (state, action, rootState) => {
      // Hide the Triaged, Bug, Master, and Test Case columns if they're boring.
      let showBugColumn = false;
      let showTriagedColumn = false;
      const masters = new Set();
      const testCases = new Set();
      for (const group of state.alertGroups) {
        if (group.triaged.count < group.alerts.length) {
          showTriagedColumn = true;
        }
        for (const alert of group.alerts) {
          if (alert.bugId) {
            showBugColumn = true;
          }
          masters.add(alert.master);
          testCases.add(alert.testCase);
        }
      }
      if (state.showingTriaged) showTriagedColumn = false;

      return {
        ...state,
        showBugColumn,
        showMasterColumn: masters.size > 1,
        showTestCaseColumn: testCases.size > 1,
        showTriagedColumn,
      };
    },

    startLoadingAlerts: (state, action, rootState) => {
      return {...state, isLoading: true};
    },

    onBugKeyup: (state, action, rootState) => {
      const options = state.bug.options.filter(option => !option.manual);
      const bugIds = options.map(option => option.value);
      if (action.bugId.match(/^\d+$/) &&
          !bugIds.includes(action.bugId)) {
        options.unshift({
          value: action.bugId,
          label: action.bugId,
          manual: true,
        });
      }
      return {
        ...state,
        bug: {
          ...state.bug,
          options,
        },
      };
    },

    receiveRecentPerformanceBugs: (state, action, rootState) => {
      return {
        ...state,
        bug: {
          ...state.bug,
          options: rootState.recentPerformanceBugs.map(
              AlertsSection.transformRecentPerformanceBugOption),
        }
      };
    },

    receiveRecentlyModifiedBugs: (state, action, rootState) => {
      const recentlyModifiedBugs = JSON.parse(action.recentlyModifiedBugs);
      return {...state, recentlyModifiedBugs};
    },
  };

  AlertsSection.transformRecentPerformanceBugOption = bug => {
    return {
      label: bug.id + ' ' + bug.summary,
      value: bug.id,
    };
  };

  AlertsSection.newStateOptionsFromQueryParams = queryParams => {
    return {
      sheriffs: queryParams.getAll('sheriff').map(
          sheriffName => sheriffName.replace(/_/g, ' ')),
      bugs: queryParams.getAll('bug'),
      reports: queryParams.getAll('ar'),
      minRevision: queryParams.get('minRev'),
      maxRevision: queryParams.get('maxRev'),
      sortColumn: queryParams.get('sort') || 'revisions',
      showingImprovements: queryParams.get('improvements') !== null,
      showingTriaged: queryParams.get('triaged') !== null,
      sortDescending: queryParams.get('descending') !== null,
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

  AlertsSection.sortGroups = (
      alertGroups, sortColumn, sortDescending, showingTriaged) => {
    const factor = sortDescending ? -1 : 1;
    if (sortColumn === 'count') {
      alertGroups = [...alertGroups];
      // See AlertsTable.getExpandGroupButtonLabel_.
      if (showingTriaged) {
        alertGroups.sort((groupA, groupB) =>
          factor * (groupA.alerts.length - groupB.alerts.length));
      } else {
        alertGroups.sort((groupA, groupB) =>
          factor * ((groupA.alerts.length - groupA.triaged.count) -
            (groupB.alerts.length - groupB.triaged.count)));
      }
    } else if (sortColumn === 'triaged') {
      alertGroups = [...alertGroups];
      alertGroups.sort((groupA, groupB) =>
        factor * (groupA.triaged.count - groupB.triaged.count));
    } else {
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
    }
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

    let baseUnit = tr.b.Unit.byName[alert.units];
    if (!baseUnit ||
        baseUnit.improvementDirection !== improvementDirection) {
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
      baseUnit = tr.b.Unit.byName[unitName + unitSuffix];
    }
    const [master, bot] = alert.descriptor.bot.split(':');

    return {
      baseUnit,
      bot,
      bugComponents: alert.bug_components,
      bugId: alert.bug_id === undefined ? '' : alert.bug_id,
      bugLabels: alert.bug_labels,
      deltaUnit: baseUnit.correspondingDeltaUnit,
      deltaValue,
      key: alert.key,
      improvement: alert.improvement,
      isSelected: false,
      master,
      measurement: alert.descriptor.measurement,
      statistic: alert.descriptor.statistic,
      percentDeltaUnit: tr.b.Unit.byName[
          'normalizedPercentageDelta' + unitSuffix],
      percentDeltaValue,
      startRevision: alert.start_revision,
      endRevision: alert.end_revision,
      testCase: alert.descriptor.testCase,
      testSuite: alert.descriptor.testSuite,
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

  const ZERO_WIDTH_SPACE = String.fromCharCode(0x200b);
  const NON_BREAKING_SPACE = String.fromCharCode(0xA0);

  AlertsSection.breakWords = str => {
    if (!str) return NON_BREAKING_SPACE;

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
      sheriffs: state.sheriff.selectedOptions,
      bugs: state.bug.selectedOptions,
      showingImprovements: state.showingImprovements,
      showingTriaged: state.showingTriaged,
      sortColumn: state.sortColumn,
      sortDescending: state.sortDescending,
    };
  };

  AlertsSection.getRouteParams = state => {
    const queryParams = new URLSearchParams();
    for (const sheriff of state.sheriff.selectedOptions) {
      queryParams.append('sheriff', sheriff.replace(/ /g, '_'));
    }
    for (const bug of state.bug.selectedOptions) {
      queryParams.append('bug', bug);
    }
    for (const name of state.report.selectedOptions) {
      queryParams.append('ar', name);
    }
    if (state.minRevision && state.minRevision.match(/^\d+$/)) {
      queryParams.set('minRev', state.minRevision);
    }
    if (state.maxRevision && state.maxRevision.match(/^\d+$/)) {
      queryParams.set('maxRev', state.maxRevision);
    }
    if (state.showingImprovements) queryParams.set('improvements', '');
    if (state.showingTriaged) queryParams.set('triaged', '');
    if (state.sortColumn !== 'revisions') {
      queryParams.set('sort', state.sortColumn);
    }
    if (state.sortDescending) queryParams.set('descending', '');
    return queryParams;
  };

  AlertsSection.isEmpty = state => (
    state &&
    (!state.sheriff || (state.sheriff.selectedOptions.length === 0)) &&
    (!state.bug || (state.bug.selectedOptions.length === 0)) &&
    (!state.report || (state.report.selectedOptions.length === 0)));

  AlertsSection.matchesOptions = (state, options) => {
    if (!tr.b.setsEqual(new Set(options.reports),
        new Set(state.report.selectedOptions))) {
      return false;
    }
    if (!tr.b.setsEqual(new Set(options.sheriffs),
        new Set(state.sheriff.selectedOptions))) {
      return false;
    }
    if (!tr.b.setsEqual(new Set(options.bugs),
        new Set(state.bug.selectedOptions))) {
      return false;
    }
    return true;
  };

  AlertsSection.getTitle = state => {
    if (state.sheriff.selectedOptions.length === 1) {
      return state.sheriff.selectedOptions[0];
    }
    if (state.bug.selectedOptions.length === 1) {
      return state.bug.selectedOptions[0];
    }
  };

  cp.ElementBase.register(AlertsSection);

  return {
    AlertsSection,
    MS_PER_MONTH,
  };
});
