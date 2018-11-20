/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class AlertsControls extends cp.ElementBase {
    connectedCallback() {
      super.connectedCallback();
      this.dispatch('connected', this.statePath);
    }

    showSheriff_(bug, report) {
      return ((bug.selectedOptions.length === 0) &&
              (report.selectedOptions.length === 0));
    }

    showBug_(sheriff, report) {
      return ((sheriff.selectedOptions.length === 0) &&
              (report.selectedOptions.length === 0));
    }

    showReport_(sheriff, bug) {
      return ((sheriff.selectedOptions.length === 0) &&
              (bug.selectedOptions.length === 0));
    }

    crbug_(bugId) {
      return `http://crbug.com/${bugId}`;
    }

    summary_(showingTriaged, alertGroups) {
      if (!alertGroups) return '';
      let groups = 0;
      let total = 0;
      for (const group of alertGroups) {
        if (showingTriaged) {
          ++groups;
          total += group.alerts.length;
        } else if (group.alerts.length > group.triaged.count) {
          ++groups;
          total += group.alerts.length - group.triaged.count;
        }
      }
      return (
        `${total} alert${this.plural_(total)} in ` +
        `${groups} group${this.plural_(groups)}`);
    }

    async dispatchSources_() {
      const sources = await AlertsControls.compileSources(
          this.sheriff.selectedOptions,
          this.bug.selectedOptions,
          this.report.selectedOptions,
          this.minRevision, this.maxRevision,
          this.showingImprovements);
      this.dispatchEvent(new CustomEvent('sources', {
        bubbles: true,
        composed: true,
        detail: {sources},
      }));
    }

    async onSheriffClear_(event) {
      this.dispatch(cp.MenuInput.actions.focus(this.statePath + '.sheriff'));
      this.dispatchSources_();
    }

    async onSheriffSelect_(event) {
      this.dispatchSources_();
    }

    async onBugClear_(event) {
      this.dispatch(cp.MenuInput.actions.focus(this.statePath + '.bug'));
      this.dispatchSources_();
    }

    async onBugKeyup_(event) {
      await this.dispatch('onBugKeyup', this.statePath, event.detail.value);
    }

    async onBugSelect_(event) {
      this.dispatchSources_();
    }

    async onReportClear_(event) {
      this.dispatch(cp.MenuInput.actions.focus(this.statePath + '.report'));
      this.dispatchSources_();
    }

    async onReportKeyup_(event) {
      await this.dispatch('onReportKeyup', this.statePath, event.detail.value);
    }

    async onReportSelect_(event) {
      this.dispatchSources_();
    }

    async onMinRevisionKeyup_(event) {
      this.dispatch(Redux.UPDATE(this.statePath, {
        minRevision: event.detail.value,
      }));
      this.dispatchSources_();
    }

    async onMaxRevisionKeyup_(event) {
      this.dispatch(Redux.UPDATE(this.statePath, {
        maxRevision: event.detail.value,
      }));
      this.dispatchSources_();
    }

    async onToggleImprovements_(event) {
      this.dispatch(Redux.TOGGLE(this.statePath + '.showingImprovements'));
      this.dispatchSources_();
    }

    async onToggleTriaged_(event) {
      await this.dispatch('toggleShowingTriaged', this.statePath);
    }

    async onTapRecentlyModifiedBugs_(event) {
      await this.dispatch('toggleRecentlyModifiedBugs', this.statePath);
    }

    async onRecentlyModifiedBugsBlur_(event) {
      await this.dispatch('toggleRecentlyModifiedBugs', this.statePath);
    }

    async onClose_(event) {
      this.dispatchEvent(new CustomEvent('close-section', {
        bubbles: true,
        composed: true,
        detail: {sectionId: this.sectionId},
      }));
    }

    observeTriaged_() {
      if (this.hasTriagedNew || this.hasTriagedExisting || this.hasIgnored) {
        this.$.recent_bugs.scrollIntoView(true);
      }
    }

    observeRecentPerformanceBugs_() {
      this.dispatch('observeRecentPerformanceBugs', this.statePath);
    }
  }

  AlertsControls.State = {
    bug: options => cp.MenuInput.buildState({
      label: 'Bug',
      options: [],
      selectedOptions: options.bugs,
    }),
    hasTriagedNew: options => false,
    hasTriagedExisting: options => false,
    hasIgnored: options => false,
    ignoredCount: options => 0,
    isLoading: options => false,
    isOwner: options => false,
    maxRevision: options => options.maxRevision || '',
    minRevision: options => options.minRevision || '',
    recentlyModifiedBugs: options => [],
    report: options => cp.MenuInput.buildState({
      label: 'Report',
      options: [],
      selectedOptions: options.reports || [],
    }),
    sectionId: options => 0,
    selectedAlertPath: options => undefined,
    selectedAlertsCount: options => 0,
    selectedAlertsCount: options => 0,
    sheriff: options => cp.MenuInput.buildState({
      label: 'Sheriff',
      options: [],
      selectedOptions: options.sheriffs || [],
    }),
    showingImprovements: options => options.showingImprovements || false,
    showingRecentlyModifiedBugs: options => false,
    triagedBugId: options => 0,
  };

  AlertsControls.observers = [
    'observeTriaged_(hasIgnored, hasTriagedExisting, hasTriagedNew)',
    'observeRecentPerformanceBugs_(recentPerformanceBugs)',
  ];

  AlertsControls.buildState = options =>
    cp.buildState(AlertsControls.State, options);

  AlertsControls.properties = {
    ...cp.buildProperties('state', AlertsControls.State),
    recentPerformanceBugs: {statePath: 'recentPerformanceBugs'},
  };

  AlertsControls.actions = {
    toggleRecentlyModifiedBugs: statePath => async(dispatch, getState) => {
      dispatch(Redux.TOGGLE(`${statePath}.showingRecentlyModifiedBugs`));
    },

    onBugKeyup: (statePath, bugId) => async(dispatch, getState) => {
      dispatch({
        type: AlertsControls.reducers.onBugKeyup.name,
        statePath,
        bugId,
      });
    },

    loadReportNames: statePath => async(dispatch, getState) => {
      const reportTemplateInfos = await new cp.ReportNamesRequest().response;
      const reportNames = reportTemplateInfos.map(t => t.name);
      dispatch(Redux.UPDATE(statePath + '.report', {
        options: cp.OptionGroup.groupValues(reportNames),
        label: `Reports (${reportNames.length})`,
      }));
    },

    connected: statePath => async(dispatch, getState) => {
      AlertsControls.actions.loadReportNames(statePath)(dispatch, getState);
      const recentlyModifiedBugs = localStorage.getItem('recentlyModifiedBugs');
      if (recentlyModifiedBugs) {
        dispatch({
          type: AlertsControls.reducers.receiveRecentlyModifiedBugs.name,
          statePath,
          recentlyModifiedBugs,
        });
      }
    },

    restoreState: (statePath, options) => async(dispatch, getState) => {
      // Don't use buildState, which would drop state that was computed/fetched
      // in actions.connected.
      dispatch({
        type: AlertsControls.reducers.restoreState.name,
        statePath,
        options,
      });
      const state = Polymer.Path.get(getState(), statePath);
      if (state && state.sheriff && state.bug && state.report &&
          !state.sheriff.selectedOptions.length &&
          !state.bug.selectedOptions.length &&
          !state.report.selectedOptions.length) {
        dispatch(cp.MenuInput.actions.focus(statePath + '.sheriff'));
      }
    },

    toggleShowingImprovements: statePath => async(dispatch, getState) => {
    },

    toggleShowingTriaged: statePath => async(dispatch, getState) => {
      dispatch(Redux.CHAIN(
          Redux.TOGGLE(`${statePath}.showingTriaged`),
          {type: AlertsControls.reducers.updateColumns.name, statePath}));
    },

    observeRecentPerformanceBugs: statePath => async(dispatch, getState) => {
      dispatch({
        type: AlertsControls.reducers.receiveRecentPerformanceBugs.name,
        statePath,
      });
    },
  };

  AlertsControls.computeLineDescriptor = alert => {
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

  AlertsControls.reducers = {
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

    updateSelectedAlertsCount: state => {
      const selectedAlertsCount = AlertsControls.getSelectedAlerts(
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
      return AlertsControls.reducers.updateSelectedAlertsCount(state);
    },

    updateBugId: (state, {alertKeys, bugId}, rootState) => {
      if (bugId === 0) bugId = '';
      const alertGroups = state.alertGroups.map(alertGroup => {
        const alerts = alertGroup.alerts.map(a =>
          (alertKeys.has(a.key) ? {...a, bugId} : a));
        return {...alertGroup, alerts};
      });
      state = {...state, alertGroups};
      return AlertsControls.reducers.updateSelectedAlertsCount(state);
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
              AlertsControls.transformRecentPerformanceBugOption),
        }
      };
    },

    receiveRecentlyModifiedBugs: (state, action, rootState) => {
      const recentlyModifiedBugs = JSON.parse(action.recentlyModifiedBugs);
      return {...state, recentlyModifiedBugs};
    },
  };

  AlertsControls.transformRecentPerformanceBugOption = bug => {
    return {
      label: bug.id + ' ' + bug.summary,
      value: bug.id,
    };
  };

  AlertsControls.newStateOptionsFromQueryParams = queryParams => {
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

  AlertsControls.getSelectedAlerts = alertGroups => {
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

  AlertsControls.compareAlerts = (alertA, alertB, sortColumn) => {
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

  AlertsControls.sortGroups = (
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
        alerts.sort((alertA, alertB) => factor * AlertsControls.compareAlerts(
            alertA, alertB, sortColumn));
        return {
          ...group,
          alerts,
        };
      });
      alertGroups.sort((groupA, groupB) =>
        factor * AlertsControls.compareAlerts(
            groupA.alerts[0], groupB.alerts[0], sortColumn));
    }
    return alertGroups;
  };

  AlertsControls.transformAlert = alert => {
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

  AlertsControls.transformBug = bug => {
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
      summary: cp.AlertsControls.breakWords(bug.summary),
      revisionRange,
    };
  };

  const ZERO_WIDTH_SPACE = String.fromCharCode(0x200b);
  const NON_BREAKING_SPACE = String.fromCharCode(0xA0);

  AlertsControls.breakWords = str => {
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

  AlertsControls.getSessionState = state => {
    return {
      sheriffs: state.sheriff.selectedOptions,
      bugs: state.bug.selectedOptions,
      showingImprovements: state.showingImprovements,
      showingTriaged: state.showingTriaged,
      sortColumn: state.sortColumn,
      sortDescending: state.sortDescending,
    };
  };

  AlertsControls.getRouteParams = state => {
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

  AlertsControls.isEmpty = state => (
    state &&
    (!state.sheriff || (state.sheriff.selectedOptions.length === 0)) &&
    (!state.bug || (state.bug.selectedOptions.length === 0)) &&
    (!state.report || (state.report.selectedOptions.length === 0)));

  AlertsControls.matchesOptions = (state, options) => {
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

  function maybeInt(x) {
    x = parseInt(x);
    return isNaN(x) ? undefined : x;
  }

  AlertsControls.compileSources = async(
    sheriffs, bugs, reports, minRevision, maxRevision, improvements) => {
    const revisions = {
      minRevision: maybeInt(minRevision),
      maxRevision: maybeInt(maxRevision),
    };
    const sources = [];
    for (const sheriff of sheriffs) {
      sources.push({
        sheriff,
        improvements,
        ...revisions,
      });
    }
    for (const bug of bugs) {
      sources.push({bug, ...revisions});
    }
    if (reports.length) {
      const reportTemplateInfos = await new cp.ReportNamesRequest().response;
      for (const name of reports) {
        for (const reportId of reportTemplateInfos) {
          if (reportId.name === name) {
            sources.push({report: reportId.id, ...revisions});
            break;
          }
        }
      }
    }
    return sources;
  };

  cp.ElementBase.register(AlertsControls);
  return {AlertsControls};
});
