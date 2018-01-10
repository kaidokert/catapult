/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  const ZERO_WIDTH_SPACE = String.fromCharCode(0x200b);

  class AlertsSection extends cp.ElementBase {
    static get is() { return 'alerts-section'; }

    static get properties() {
      return cp.ElementBase.statePathProperties('statePath', {
        alertGroups: {type: Array},
        selectedAlertsCount: {type: Number},
        areAlertGroupsPlaceholders: {type: Boolean},
        existingBug: {type: Object},
        newBug: {type: Object},
        isLoading: {type: Boolean},
        isOwner: {type: Boolean},
        isPreviewing: {type: Boolean},
        previewLayout: {type: Object},
        recentBugs: {type: Array},
        sectionId: {type: String},
        showBugColumn: {type: Boolean},
        showMasterColumn: {type: Boolean},
        showTestCaseColumn: {type: Boolean},
        showingImprovements: {type: Boolean},
        showingTriaged: {type: Boolean},
        sortColumn: {type: String},
        sortDescending: {type: Boolean},
        source: {type: Object},
      });
    }

    static getSelectedAlerts(alertGroups) {
      const selectedAlerts = [];
      for (const alertGroup of alertGroups) {
        for (const alert of alertGroup.alerts) {
          if (alert.isSelected) {
            selectedAlerts.push(alert);
          }
        }
      }
      return selectedAlerts;
    }

    static compareAlerts(alertA, alertB, sortColumn) {
      switch (sortColumn) {
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
    }

    static sortGroups(alertGroups, sortColumn, sortDescending) {
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
    }

    static transformAlert(alert) {
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

      return {
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
      };
    }

    static transformBug(bug) {
      // Save memory by stripping out all the unnecessary data.
      // TODO save bandwidth by stripping out the unnecessary data in the
      // backend request handler.
      return {
        id: bug.id,
        status: bug.status,
        owner: bug.owner ? bug.owner.name : '',
        description: bug.summary,
      };
    }

    static newBugSummary(alerts) {
      // 2.6%-2.7% regression in system_health.common_desktop at 526280:526293
      const pctDeltaRange = new tr.b.math.Range();
      const revisionRange = new tr.b.math.Range();
      const testSuites = new Set();
      cp.todo('handle non-numeric revisions');
      for (const alert of alerts) {
        if (!alert.improvement) {
          pctDeltaRange.addValue(Math.abs(100 * alert.percentDeltaValue));
        }
        revisionRange.addValue(alert.startRevision);
        revisionRange.addValue(alert.endRevision);
        testSuites.add(alert.testSuite);
      }

      let summary = pctDeltaRange.min.toLocaleString(undefined, {
        maximumFractionDigits: 1,
      }) + '%';
      if (pctDeltaRange.min !== pctDeltaRange.max) {
        summary += '-' + pctDeltaRange.max.toLocaleString(undefined, {
          maximumFractionDigits: 1,
        }) + '%';
      }
      summary += ' regression in ';
      summary += Array.from(testSuites).join(',');
      summary += ' at ';
      summary += revisionRange.min;
      if (revisionRange.min !== revisionRange.max) {
        summary += ':' + revisionRange.max;
      }
      return summary;
    }

    static newBugLabels(alerts) {
      let labels = new Set();
      labels.add('Pri-2');
      labels.add('Type-Bug-Regression');
      for (const alert of alerts) {
        for (const label of alert.bugLabels) {
          labels.add(label);
        }
      }
      labels = Array.from(labels);
      labels.sort((x, y) => x.localeCompare(y));
      return labels;
    }

    static newBugComponents(alerts) {
      let components = new Set();
      for (const alert of alerts) {
        for (const component of alert.bugComponents) {
          components.add(component);
        }
      }
      components = Array.from(components);
      components.sort((x, y) => x.localeCompare(y));
      return components;
    }

    static async fileBug(options) {
      const headers = new Headers(options.headers);

      const body = new FormData();
      for (const key of options.alertKeys) body.append('key', key);
      for (const label of options.labels) body.append('label', label);
      for (const component of options.components) {
        body.append('component', component);
      }
      body.set('summary', options.summary);
      body.set('description', options.description);
      body.set('owner', options.owner);
      body.set('cc', options.cc);

      await fetch('/api/alerts/new_bug', {
        method: 'POST',
        headers,
        body,
      });
    }

    static async fileExistingBug(options) {
      const headers = new Headers(options.headers);

      const body = new FormData();
      for (const key of options.alertKeys) body.append('key', key);
      body.set('bugId', options.bugId);

      await fetch('/api/alerts/existing_bug', {
        method: 'POST',
        headers,
        body,
      });
    }

    static unpackSourceOptions(source) {
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
    }

    static async fetchAlerts(headers, options) {
      headers = new Headers(headers);
      headers.set('Content-type', 'application/x-www-form-urlencoded');

      const body = new URLSearchParams();
      for (const [key, value] of Object.entries(options)) {
        if (value === undefined) continue;
        body.set(key, value);
      }

      let signal;
      if (window.AbortController) {
        const controller = new AbortController();
        signal = controller.signal;
        cp.todo('store AbortController in state');
      }

      try {
        const response = await fetch('/alerts', {
          method: 'POST',
          headers,
          body,
          signal,
        });
        return await response.json();
      } catch (err) {
        return {
          anomaly_list: cp.dummyAlerts(Boolean(options.improvements)),
          recent_bugs: cp.dummyRecentBugs(),
        };
      }
    }

    ready() {
      super.ready();
      this.scrollIntoView(true);
    }

    connectedCallback() {
      super.connectedCallback();
      this.dispatch('connected', this.statePath);
    }

    alertRevisionString_(alert) {
      if (alert.startRevision === alert.endRevision) return alert.startRevision;
      return alert.startRevision + '-' + alert.endRevision;
    }

    alertRevisionHref_(alert) {
      if (alert.master === 'ChromiumPerf') return `http://test-results.appspot.com/revision_range?start=${alert.startRevision}&end=${alert.endRevision}&n=1000`;
      return '';
    }

    breakWords_(str) {
      if (str === undefined) return '';
      return str.replace(/:/g, ':' + ZERO_WIDTH_SPACE)
          .replace(/\./g, '.' + ZERO_WIDTH_SPACE);
    }

    shouldDisplayAlert_(alertGroup, alertIndex) {
      return alertGroup.isExpanded || (alertIndex === 0);
    }

    shouldDisplayExpandGroupButton_(alertGroup, alertIndex) {
      if (alertIndex !== 0) return false;
      return alertGroup.alerts.length > 1;
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

    onSourceKeydown_(e) {
      this.dispatch('keydownSource', this.statePath, e.detail.value);
    }

    onSourceClear_(e) {
      this.dispatch('onSourceClear', this.statePath);
    }

    onSourceSelect_(e) {
      this.dispatch('loadAlerts', this.statePath);
    }

    toggleShowingImprovements_() {
      this.dispatch('toggleShowingImprovements', this.statePath);
    }

    toggleShowingTriaged_() {
      this.dispatch('toggleShowingTriaged', this.statePath);
    }

    closeSection_() {
      this.dispatchEvent(new CustomEvent('close-section', {
        bubbles: true,
        composed: true,
        detail: {sectionId: this.sectionId},
      }));
    }

    openCharts_(e) {
      const ctrlKey = e.detail.sourceEvent.ctrlKey;
      this.dispatch('openCharts', this.statePath, ctrlKey);
    }

    fileNewBug_() {
      this.dispatch('fileNewBug', this.statePath);
    }

    submitNewBug_() {
      this.dispatch('submitNewBug', this.statePath);
    }

    fileExistingBug_() {
      this.dispatch('fileExistingBug', this.statePath);
    }

    submitExistingBug_() {
      this.dispatch('submitExistingBug', this.statePath);
    }

    ignore_() {
      this.dispatch('ignore', this.statePath);
    }

    selectAllAlerts_(event) {
      event.target.checked = !event.target.checked;
      this.dispatch('selectAllAlerts', this.statePath);
    }

    selectAlert_(event) {
      this.dispatch('selectAlert', this.statePath,
          event.model.parentModel.alertGroupIndex,
          event.model.alertIndex,
          event.detail.sourceEvent.shiftKey);
    }

    onDotClick_(event) {
      cp.todo('open timeseries in new chart-section');
    }

    onDotMouseOver_(event) {
      // TODO
    }

    onDotMouseOut_(event) {
      // TODO
    }

    onCancelNewBug_() {
      this.dispatch('cancelNewBug', this.statePath);
    }

    onNewBugSummary_(event) {
      this.dispatch('newBugSummary', this.statePath, event.target.value);
    }

    onNewBugDescription_(event) {
      this.dispatch('newBugDescription', this.statePath, event.target.value);
    }

    onNewBugOwner_(event) {
      this.dispatch('newBugOwner', this.statePath, event.target.value);
    }

    onNewBugCC_(event) {
      this.dispatch('newBugCC', this.statePath, event.target.value);
    }

    onNewBugLabel_(event) {
      this.dispatch('toggleNewBugLabel', this.statePath,
          event.model.label.name);
    }

    onNewBugComponent_(event) {
      this.dispatch('toggleNewBugComponent', this.statePath,
          event.model.component.name);
    }

    onExistingBugId_(event) {
      this.dispatch('existingBugId', this.statePath, event.target.value);
    }

    onExistingRecentBug_(event) {
      this.dispatch('existingBugId', this.statePath, event.model.bug.id);
    }

    onCancelExistingBug_() {
      this.dispatch('cancelExistingBug', this.statePath);
    }

    sort_(e) {
      this.dispatch('sort', this.statePath, e.target.name);
    }
  }

  const placeholderAlertGroups = [];
  const placeholderString = '-'.repeat(5);
  for (let i = 0; i < 5; ++i) {
    placeholderAlertGroups.push({
      isSelected: false,
      alerts: [
        {
          bugId: placeholderString,
          revisions: placeholderString,
          testSuite: placeholderString,
          measurement: placeholderString,
          master: placeholderString,
          bot: placeholderString,
          testCase: placeholderString,
          deltaValue: 0,
          deltaUnit: tr.b.Unit.byName.countDelta_biggerIsBetter,
          percentDeltaValue: 0,
          percentDeltaUnit:
            tr.b.Unit.byName.normalizedPercentageDelta_biggerIsBetter,
        },
      ],
    });
  }

  AlertsSection.NEW_STATE = {
    alertGroups: placeholderAlertGroups,
    areAlertGroupsPlaceholders: true,
    existingBug: {isOpen: false},
    isLoading: false,
    isOwner: false,
    isPreviewing: true,
    newBug: {isOpen: false},
    previewLayout: false,
    recentBugs: [],
    selectedAlertsCount: 0,
    showBugColumn: true,
    showMasterColumn: true,
    showTestCaseColumn: true,
    showingImprovements: false,
    showingTriaged: false,
    sortColumn: 'revisions',
    sortDescending: false,
    source: {
      placeholder: 'Source',
      inputValue: '',
      selectedOptions: [],
      options: cp.dummyAlertsSources(),
    },
  };

  AlertsSection.actions = {
    onSourceClear: statePath => async (dispatch, getState) => {
      dispatch(AlertsSection.actions.loadAlerts(statePath));
      dispatch(cp.DropdownInput.actions.focus(statePath + '.source'));
    },

    existingBugId: (statePath, bugId) => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(
          `${statePath}.existingBug`, {bugId}));
    },

    newBugSummary: (statePath, summary) => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(
          `${statePath}.newBug`, {summary}));
    },

    newBugOwner: (statePath, owner) => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(
          `${statePath}.newBug`, {owner}));
    },

    newBugCC: (statePath, cc) => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(
          `${statePath}.newBug`, {cc}));
    },

    toggleNewBugLabel: (statePath, name) => async (dispatch, getState) => {
      dispatch({
        type: AlertsSection.reducers.toggleNewBugLabel.typeName,
        statePath,
        name,
      });
    },

    toggleNewBugComponent: (statePath, name) => async (dispatch, getState) => {
      dispatch({
        type: AlertsSection.reducers.toggleNewBugComponent.typeName,
        statePath,
        name,
      });
    },

    newBugDescription: (statePath, description) =>
      async (dispatch, getState) => {
        dispatch(cp.ElementBase.actions.updateObject(
            `${statePath}.newBug`, {description}));
      },

    connected: statePath => async (dispatch, getState) => {
      const sourcePath = statePath + '.source';
      const source = Polymer.Path.get(getState(), sourcePath);
      if (source.selectedOptions.length === 0) {
        dispatch(cp.DropdownInput.actions.focus(sourcePath));
      }
    },

    submitExistingBug: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(
          statePath, {isLoading: true}));
      const rootState = getState();
      const state = Polymer.Path.get(rootState, statePath);
      const alerts = AlertsSection.getSelectedAlerts(state.alertGroups);
      try {
        await AlertsSection.fileExistingBug({
          headers: rootState.authHeaders,
          alertKeys: alerts.map(a => a.key),
          bugId: state.existingBug.bugId,
        });
      } catch (err) {
        // eslint-disable-next-line no-console
        console.error(err);
      }
      dispatch(cp.ElementBase.actions.updateObject(
          statePath, {isLoading: false}));
      dispatch(cp.ElementBase.actions.updateObject(
          `${statePath}.existingBug`, {isOpen: false}));
    },

    fileExistingBug: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(`${statePath}.existingBug`, {
        isOpen: true,
        bugId: '',
      }));
    },

    ignore: statePath => async (dispatch, getState) => {
      cp.todo('ignore selected alerts');
    },

    selectAllAlerts: statePath => async (dispatch, getState) => {
      dispatch({
        type: AlertsSection.reducers.selectAllAlerts.typeName,
        statePath,
      });
      dispatch(AlertsSection.actions.maybeLayoutPreview(statePath));
    },

    selectAlert: (statePath, alertGroupIndex, alertIndex, shiftKey) =>
      async (dispatch, getState) => {
        dispatch({
          type: AlertsSection.reducers.selectAlert.typeName,
          statePath,
          alertGroupIndex,
          alertIndex,
          shiftKey,
        });
        dispatch(AlertsSection.actions.maybeLayoutPreview(statePath));
      },

    cancelNewBug: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(
          `${statePath}.newBug`, {isOpen: false}));
    },

    cancelExistingBug: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(
          `${statePath}.existingBug`, {isOpen: false}));
    },

    openCharts: (statePath, ctrlKey) => async (dispatch, getState) => {
      if (ctrlKey) {
        cp.todo('open charts in a new tab');
      }

      const state = getState();
      const section = Polymer.Path.get(state, statePath);
      for (const alert of AlertsSection.getSelectedAlerts(
          section.alertGroups)) {
        const testPath = [
          alert.testSuite, alert.bot, alert.measurement, alert.testCase];
        const chartId = tr.b.GUID.allocateSimple();

        cp.todo('select alert revisions in chart');

        dispatch({
          type: cp.ChromeperfApp.reducers.newSection.typeName,
          sectionType: 'chart-section',
          sectionId: chartId,
        });
        for (let i = 0; i < testPath.length; ++i) {
          dispatch(cp.TestPathComponent.actions.select(
              `sectionsById.${chartId}.testPathComponents.${i}`,
              [testPath[i]]));
        }
        dispatch(cp.ChartSection.actions.selectTestPathComponent(
            `sectionsById.${chartId}`, 0));
      }
      dispatch(cp.DropdownInput.actions.blurAll());
    },

    fileNewBug: statePath => async (dispatch, getState) => {
      const userEmail = getState().userEmail;
      if (!userEmail) {
        cp.todo('you must signin to triage alerts');
      }
      dispatch({
        type: AlertsSection.reducers.fileNewBug.typeName,
        statePath,
        userEmail,
      });
    },

    submitNewBug: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(
          statePath, {isLoading: true}));
      const rootState = getState();
      const state = Polymer.Path.get(rootState, statePath);
      const alerts = AlertsSection.getSelectedAlerts(state.alertGroups);
      try {
        await AlertsSection.fileBug({
          headers: rootState.authHeaders,
          alertKeys: alerts.map(a => a.key),
          ...state.newBug,
          labels: state.newBug.labels.filter(
              x => x.isEnabled).map(x => x.name),
          components: state.newBug.components.filter(
              x => x.isEnabled).map(x => x.name),
        });
      } catch (err) {
        // eslint-disable-next-line no-console
        console.error(err);
      }
      dispatch(cp.ElementBase.actions.updateObject(
          statePath, {isLoading: false}));
      dispatch(cp.ElementBase.actions.updateObject(
          `${statePath}.newBug`, {isOpen: false}));
    },

    keydownSource: (statePath, inputValue) => async (dispatch, getState) => {
      // TODO filter options?
    },

    clearSource: statePath => async (dispatch, getState) => {
      // TODO unfilter options?
    },

    updateLocation: sectionState => async (dispatch, getState) => {
      const selectedOptions = sectionState.source.selectedOptions;
      if (selectedOptions.length === 0) {
        dispatch(cp.ChromeperfApp.actions.updateRoute('', {}));
        return;
      }
      const queryParams = {};
      for (const option of selectedOptions) {
        queryParams[option.replace(/ /g, '_')] = '';
      }
      cp.todo('store showingImprovements, showingTriaged');
      dispatch(cp.ChromeperfApp.actions.updateRoute('alerts', queryParams));
    },

    restoreFromQueryParams: (statePath, queryParams) =>
      async (dispatch, getState) => {
        const selectedOptions = [];
        for (const param of Object.keys(queryParams)) {
          selectedOptions.push(param.replace(/_/g, ' '));
        }
        dispatch(cp.ElementBase.actions.updateObject(
            `${statePath}.source`, {selectedOptions}));
        dispatch(AlertsSection.actions.loadAlerts(statePath));

        cp.todo('if ?charts: open charts for all alerts');
      },

    loadAlerts: statePath => async (dispatch, getState) => {
      dispatch(cp.DropdownInput.actions.blurAll());
      dispatch({
        type: AlertsSection.reducers.startLoadingAlerts.typeName,
        statePath,
      });
      dispatch(cp.ChromeperfApp.actions.updateLocation());
      const rootState = getState();
      const state = Polymer.Path.get(rootState, statePath);

      const alerts = [];
      let recentBugs = [];
      const fetchMark = tr.b.Timing.mark('fetch', 'alerts');
      cp.todo('cache alerts');
      cp.todo('parallelize fetch alerts');
      for (const source of state.source.selectedOptions) {
        const options = AlertsSection.unpackSourceOptions(source);
        options.improvements = state.showingImprovements ? 'true' : '';
        options.triaged = state.showingTriaged ? 'true' : '';
        const response = await AlertsSection.fetchAlerts(
            rootState.authHeaders, options);
        alerts.push.apply(alerts, response.anomaly_list);
        recentBugs = response.recent_bugs;
      }
      fetchMark.end();

      dispatch({
        type: AlertsSection.reducers.receiveAlerts.typeName,
        statePath,
        alerts,
        recentBugs,
      });
      dispatch(AlertsSection.actions.maybeLayoutPreview(statePath));
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

    layoutPreview: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(
          statePath, {isLoading: true}));

      await tr.b.timeout(500);

      const section = Polymer.Path.get(getState(), statePath);
      const alerts = AlertsSection.getSelectedAlerts(section.alertGroups);
      const colors = tr.b.generateFixedColorScheme(
          alerts.length, {hueOffset: 0.64});
      const colorForAlert = new Map(alerts.map((alert, index) =>
        [alert.key, colors[index].toString()]));
      const sequenceLength = 100;

      cp.todo('refactor to call cp.MultiChart.layout()');

      const maxYAxisTickWidth = 30;
      const textHeight = 15;
      const chartHeight = 200;

      const chartLines = [];
      for (const color of colors) {
        const y0 = parseInt(100 * Math.random());
        const sequence = {
          color: '' + color,
          dotColor: '' + color,
          data: [{x: 0, y: y0}],
          strokeWidth: 1,
        };
        chartLines.push(sequence);
        for (let i = 0; i < sequenceLength; i += 1) {
          const datum = {
            x: parseInt(100 * (i + 1) / sequenceLength),
            y: parseInt(100 * Math.random()),
          };
          sequence.data.push(datum);
        }
      }

      const chartXAxisTicks = [
        'Dec', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13',
        '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24',
        '25', '26', '27', '28', '29', '30', '31', '2018', '2', '3',
      ].map((text, index, texts) => {
        return {
          text,
          x: parseInt(100 * (index + 0.5) / texts.length),
          y: chartHeight - 5,
        };
      });

      dispatch({
        type: AlertsSection.reducers.layoutPreview.typeName,
        statePath,
        colorForAlert,
        previewLayout: {
          height: chartHeight,
          yAxisWidth: 0,
          xAxisHeight: textHeight,
          graphHeight: chartHeight - textHeight - 15,
          dotRadius: 6,
          dotCursor: 'pointer',
          showYAxisTickLines: false,
          showXAxisTickLines: true,
          lines: chartLines,
          yAxisTicks: [],
          xAxisTicks: chartXAxisTicks,
          brushes: [],
        },
      });
    },

    maybeLayoutPreview: statePath => async (dispatch, getState) => {
      const section = Polymer.Path.get(getState(), statePath);
      if (!section.isPreviewing || !section.selectedAlertsCount) {
        dispatch({
          type: AlertsSection.reducers.layoutPreview.typeName,
          statePath,
          previewLayout: false,
          colorForAlert: new Map(),
        });
        return;
      }

      dispatch(AlertsSection.actions.layoutPreview(statePath));
    },

    sort: (statePath, sortColumn) => async (dispatch, getState) => {
      dispatch({
        type: AlertsSection.reducers.sort.typeName,
        statePath,
        sortColumn,
      });
    },
  };

  AlertsSection.reducers = {
    toggleNewBugLabel: cp.ElementBase.statePathReducer((state, action) => {
      for (let i = 0; i < state.newBug.labels.length; ++i) {
        if (state.newBug.labels[i].name === action.name) {
          return Polymer.Path.setImmutable(
              state, `newBug.labels.${i}.isEnabled`, e => !e);
        }
      }
      return state;
    }),

    toggleNewBugComponent: cp.ElementBase.statePathReducer((state, action) => {
      for (let i = 0; i < state.newBug.components.length; ++i) {
        if (state.newBug.components[i].name === action.name) {
          return Polymer.Path.setImmutable(
              state, `newBug.components.${i}.isEnabled`, e => !e);
        }
      }
      return state;
    }),

    fileNewBug: cp.ElementBase.statePathReducer((state, action) => {
      const alerts = AlertsSection.getSelectedAlerts(state.alertGroups);
      return {
        ...state,
        newBug: {
          isOpen: true,
          summary: AlertsSection.newBugSummary(alerts),
          description: '',
          owner: '',
          cc: action.userEmail,
          labels: AlertsSection.newBugLabels(alerts).map(name => {
            return {
              isEnabled: true,
              name,
            };
          }),
          components: AlertsSection.newBugComponents(alerts).map(name => {
            return {
              isEnabled: true,
              name,
            };
          }),
        },
      };
    }),

    sort: cp.ElementBase.statePathReducer((state, action) => {
      const sortDescending = state.sortDescending ^ (state.sortColumn ===
          action.sortColumn);
      const alertGroups = AlertsSection.sortGroups(
          state.alertGroups, action.sortColumn, sortDescending);
      return {
        ...state,
        sortColumn: action.sortColumn,
        sortDescending,
        alertGroups,
      };
    }),

    selectAlert: cp.ElementBase.statePathReducer((state, action) => {
      const alertGroup = state.alertGroups[action.alertGroupIndex];
      let alerts = alertGroup.alerts;
      const isSelected = !alerts[action.alertIndex].isSelected;

      if (!alertGroup.isExpanded && (action.alertIndex === 0)) {
        // Toggle all alerts in this group
        alerts = alerts.map(alert => {
          return {
            ...alert,
            isSelected,
          };
        });
      } else {
        // Only toggle this alert.
        alerts = Polymer.Path.setImmutable(
            alerts, `${action.alertIndex}.isSelected`, isSelected);
      }

      const alertGroups = Polymer.Path.setImmutable(
          state.alertGroups, `${action.alertGroupIndex}.alerts`, alerts);
      const selectedAlertsCount = AlertsSection.getSelectedAlerts(
          alertGroups).length;
      return {
        ...state,
        alertGroups,
        selectedAlertsCount,
      };
    }),

    selectAllAlerts: cp.ElementBase.statePathReducer((state, action) => {
      const select = (state.selectedAlertsCount === 0);
      const alertGroups = state.alertGroups.map(alertGroup => {
        return {
          ...alertGroup,
          alerts: alertGroup.alerts.map(alert => {
            return {
              ...alert,
              isSelected: select,
            };
          }),
        };
      });
      return {
        ...state,
        alertGroups,
        selectedAlertsCount: AlertsSection.getSelectedAlerts(
            alertGroups).length,
      };
    }),

    receiveAlerts: cp.ElementBase.statePathReducer((state, action) => {
      if (!action.alerts.length) {
        state = {
          ...state,
          alertGroups: placeholderAlertGroups,
          areAlertGroupsPlaceholders: true,
          isLoading: false,
          isOwner: false,
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

      // Automatically select the first group.
      let selectedAlertsCount = 0;
      if (alertGroups.length) {
        for (const alert of alertGroups[0].alerts) {
          alert.isSelected = true;
        }
        selectedAlertsCount = alertGroups[0].alerts.length;
      }

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

      const recentBugs = action.recentBugs.map(AlertsSection.transformBug);

      return {
        ...state,
        alertGroups,
        areAlertGroupsPlaceholders: false,
        isLoading: false,
        isOwner: Math.random() < 0.5,
        recentBugs,
        selectedAlertsCount,
        showBugColumn: bugs.size > 1,
        showMasterColumn: masters.size > 1,
        showTestCaseColumn: testCases.size > 1,
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

    layoutPreview: cp.ElementBase.statePathReducer((state, action) => {
      return {
        ...state,
        isLoading: false,
        previewLayout: action.previewLayout,
        alertGroups: state.alertGroups.map(alertGroup => {
          return {
            ...alertGroup,
            alerts: alertGroup.alerts.map(alert => {
              return {
                ...alert,
                color: action.colorForAlert.get(alert.key),
              };
            }),
          };
        }),
      };
    }),
  };

  cp.ElementBase.register(AlertsSection);

  return {
    AlertsSection,
  };
});
