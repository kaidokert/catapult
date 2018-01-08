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
        isFilingExistingBug: {type: Boolean},
        isFilingNewBug: {type: Boolean},
        isLoading: {type: Boolean},
        isOwner: {type: Boolean},
        isPreviewing: {type: Boolean},
        previewLayout: {type: Object},
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

    static async fetchAlerts(options) {
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
      const headers = new Headers();
      headers.append('Content-type', 'application/x-www-form-urlencoded');
      try {
        const response = await fetch('/alerts', {
          method: 'POST',
          body,
          signal,
          headers,
        });
        const jsonResponse = await response.json();
        return jsonResponse.anomaly_list;
      } catch (err) {
        return cp.dummyAlerts(options.improvements);
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

    breakWords_(str) {
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

    countTotalAlerts_(alertGroups) {
    }

    onSourceKeydown_(e) {
      this.dispatch('keydownSource', this.statePath, e.detail.value);
    }

    onSourceClear_(e) {
      this.dispatch('loadAlerts', this.statePath);
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

    submitExistingBug_() {
      this.dispatch('submitExistingBug', this.statePath);
    }

    fileExistingBug_() {
      this.dispatch('fileExistingBug', this.statePath);
    }

    ignore_() {
      this.dispatch('ignore', this.statePath);
    }

    reportInvalid_() {
      this.dispatch('reportInvalid', this.statePath);
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

    onCancelExistingBug_() {
      this.dispatch('cancelExistingBug', this.statePath);
    }

    sort_(e) {
      this.dispatch('sort', this.statePath, e.target.name);
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
          return alertA.percentDeltaValue - alertB.percentDeltaValue;
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
    isPreviewing: true,
    previewLayout: false,
    sortColumn: 'revisions',
    sortDescending: false,
    selectedAlertsCount: 0,
    isOwner: false,
    alertGroups: placeholderAlertGroups,
    areAlertGroupsPlaceholders: true,
    isLoading: false,
    showBugColumn: true,
    showMasterColumn: true,
    showTestCaseColumn: true,
    showingImprovements: false,
    showingTriaged: false,
    source: {
      placeholder: 'Source',
      inputValue: '',
      selectedOptions: [],
      options: cp.dummyAlertsSources(),
    },
  };

  AlertsSection.actions = {
    connected: statePath => async (dispatch, getState) => {
      const sourcePath = statePath + '.source';
      const source = Polymer.Path.get(getState(), sourcePath);
      if (source.selectedOptions.length === 0) {
        dispatch(cp.DropdownInput.actions.focus(sourcePath));
      }
    },

    submitExistingBug: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(
          statePath, {isFilingExistingBug: false}));
    },

    fileExistingBug: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(
          statePath, {isFilingExistingBug: true}));
    },

    ignore: statePath => async (dispatch, getState) => {
      cp.todo('ignore selected alerts');
    },

    reportInvalid: statePath => async (dispatch, getState) => {
      cp.todo('report invalid selected alerts');
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

    toggleSourceGroupExpanded: (statePath, path) =>
      async (dispatch, getState) => {
        dispatch({
          type: AlertsSection.reducers.toggleSourceGroupExpanded.typeName,
          statePath,
          path,
        });
      },

    cancelNewBug: statePath => async (dispatch, getState) => {
      dispatch({
        type: AlertsSection.reducers.cancelNewBug.typeName,
        statePath,
      });
    },

    cancelExistingBug: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(
          statePath, {isFilingExistingBug: false}));
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
      dispatch(cp.ElementBase.actions.updateObject(
          statePath, {isFilingNewBug: true}));
    },

    submitNewBug: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(
          statePath, {isFilingNewBug: false}));
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
      const state = Polymer.Path.get(getState(), statePath);

      const alerts = [];
      const fetchMark = tr.b.Timing.mark('fetch', 'alerts');
      cp.todo('cache alerts');
      cp.todo('parallelize fetch alerts');
      for (const source of state.source.selectedOptions) {
        alerts.push.apply(alerts, await AlertsSection.fetchAlerts({
          ...AlertsSection.unpackSourceOptions(source),
          improvements: state.showingImprovements ? 'true' : '',
          triaged: state.showingTriaged ? 'true' : '',
        }));
      }
      fetchMark.end();

      dispatch({
        type: AlertsSection.reducers.receiveAlerts.typeName,
        statePath,
        alerts,
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
        return {
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
      }

      let alertGroups = d.groupAlerts(action.alerts);
      alertGroups = alertGroups.map((alerts, groupIndex) => {
        alerts = alerts.map(alert => {
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

          return {
            bot: alert.bot,
            bugId: alert.bug_id === undefined ? '' : alert.bug_id,
            deltaUnit: baseUnit.correspondingDeltaUnit,
            deltaValue,
            key: alert.key,
            isSelected: false,
            master: alert.master,
            measurement: testParts[0],
            percentDeltaUnit: tr.b.Unit.byName[
              'normalizedPercentageDelta' + unitSuffix],
            percentDeltaValue,
            revisions: `${alert.start_revision} - ${alert.end_revision}`,
            startRevision: alert.start_revision,
            testCase: testParts.slice(1).join('/'),
            testSuite: alert.testsuite,
          };
        });
        return {isExpanded: false, alerts};
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

      return {
        ...state,
        alertGroups,
        areAlertGroupsPlaceholders: false,
        isLoading: false,
        isOwner: Math.random() < 0.5,
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
