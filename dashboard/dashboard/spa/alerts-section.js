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
      if (sourceType === 'Sheriff') {
        sheriff = sourceParts[1];
        if (!['Jochen', 'Histogram FYI'].includes(sheriff)) {
          sheriff += ' Perf Sheriff';
        }
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
      const body = new FormData();
      body.append('json', JSON.stringify(options));
      let signal;
      if (window.AbortController) {
        const controller = new AbortController();
        signal = controller.signal;
        cp.todo('store AbortController in state');
      }
      try {
        const response = await fetch('/alerts', {
          method: 'POST',
          body,
          signal,
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

    toggleGroupExpanded_(event) {
      this.dispatch('toggleGroupExpanded', this.statePath,
          event.model.parentModel.alertGroupIndex);
    }

    closeSection_() {
      this.dispatchEvent(new CustomEvent('close-section', {
        bubbles: true,
        composed: true,
        detail: {sectionId: this.sectionId},
      }));
    }

    togglePreviewing_() {
      this.dispatch('togglePreviewing', this.statePath);
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
          event.model.alertIndex);
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

  const sourceOptions = cp.OptionGroup.groupValues(cp.dummyAlertsSources());
  sourceOptions[1].isExpanded = true;

  AlertsSection.NEW_STATE = {
    isPreviewing: true,
    previewLayout: false,
    sortColumn: 'revisions',
    sortDescending: false,
    selectedAlertsCount: 0,
    isOwner: false,
    alertGroups: [],
    areAlertGroupsPlaceholders: true,
    isLoading: false,
    showingImprovements: false,
    showingTriaged: false,
    source: {
      placeholder: 'Source',
      inputValue: '',
      selectedOptions: [],
      options: sourceOptions,
    },
  };

  for (let i = 0; i < 5; ++i) {
    AlertsSection.NEW_STATE.alertGroups.push({
      isSelected: false,
      alerts: [
        {
          revisions: '-----',
          bot: '-----',
          testSuite: '-----',
          measurement: '-----',
          testCase: '-----',
        },
      ],
    });
  }

  AlertsSection.actions = {
    connected: statePath => async (dispatch, getState) => {
      const sourcePath = statePath + '.source';
      const source = Polymer.Path.get(getState(), sourcePath);
      if (source.selectedOptions.length === 0) {
        dispatch(cp.DropdownInput.actions.focus(sourcePath));
      }
    },

    toggleGroupExpanded: (statePath, alertGroupIndex) =>
      async (dispatch, getState) => {
        dispatch(cp.ElementBase.actions.toggleBooleanAtPath(
            `${statePath}.alertGroups.${alertGroupIndex}.isExpanded`));
      },

    submitExistingBug: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObjectAtPath(
          statePath, {isFilingExistingBug: false}));
    },

    fileExistingBug: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObjectAtPath(
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
        type: 'alerts-section.selectAllAlerts',
        statePath,
      });
      dispatch(AlertsSection.actions.maybeLayoutPreview(statePath));
    },

    selectAlert: (statePath, alertGroupIndex, alertIndex) =>
      async (dispatch, getState) => {
        dispatch({
          type: 'alerts-section.selectAlert',
          statePath,
          alertGroupIndex,
          alertIndex,
        });
        dispatch(AlertsSection.actions.maybeLayoutPreview(statePath));
      },

    toggleSourceGroupExpanded: (statePath, path) =>
      async (dispatch, getState) => {
        dispatch({
          type: 'alerts-section.toggleSourceGroupExpanded',
          statePath,
          path,
        });
      },

    cancelNewBug: statePath => async (dispatch, getState) => {
      dispatch({
        type: 'alerts-section.cancelNewBug',
        statePath,
      });
    },

    cancelExistingBug: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObjectAtPath(
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
          type: 'chromeperf-app.newSection',
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
      dispatch(cp.ElementBase.actions.updateObjectAtPath(
          statePath, {isFilingNewBug: true}));
    },

    submitNewBug: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObjectAtPath(
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
        queryParams[option.replace(' ', '_')] = '';
      }
      cp.todo('store showingImprovements, showingTriaged');
      dispatch(cp.ChromeperfApp.actions.updateRoute('alerts', queryParams));
    },

    restoreFromQueryParams: (statePath, queryParams) =>
      async (dispatch, getState) => {
        const selectedOptions = [];
        for (const param of Object.keys(queryParams)) {
          selectedOptions.push(param.replace('_', ' '));
        }
        dispatch(cp.ElementBase.actions.updateObjectAtPath(
            `${statePath}.source`, {selectedOptions}));
        dispatch(AlertsSection.actions.loadAlerts(statePath));

        cp.todo('if ?charts: open charts for all alerts');
      },

    loadAlerts: statePath => async (dispatch, getState) => {
      dispatch(cp.DropdownInput.actions.blurAll());
      dispatch({
        type: 'alerts-section.startLoadingAlerts',
        statePath,
      });
      dispatch(cp.ChromeperfApp.actions.updateLocation());
      const state = Polymer.Path.get(getState(), statePath);

      const alerts = [];
      const fetchMark = tr.b.Timing.mark('alerts-section', 'fetch');
      cp.todo('cache alerts');
      cp.todo('parallelize fetch alerts');
      for (const source of state.source.selectedOptions) {
        alerts.push.apply(alerts, await AlertsSection.fetchAlerts({
          ...AlertsSection.unpackSourceOptions(source),
          improvements: state.showingImprovements,
          triaged: state.showingTriaged,
        }));
      }
      fetchMark.end();

      dispatch({
        type: 'alerts-section.receiveAlerts',
        statePath,
        alerts,
      });
      dispatch(AlertsSection.actions.maybeLayoutPreview(statePath));
    },

    toggleShowingImprovements: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.toggleBooleanAtPath(
          `${statePath}.showingImprovements`));
      dispatch(AlertsSection.actions.loadAlerts(statePath));
    },

    toggleShowingTriaged: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.toggleBooleanAtPath(
          `${statePath}.showingTriaged`));
      dispatch(AlertsSection.actions.loadAlerts(statePath));
    },

    layoutPreview: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObjectAtPath(
          statePath, {isLoading: true}));

      await tr.b.timeout(500);

      const section = Polymer.Path.get(getState(), statePath);
      const alerts = AlertsSection.getSelectedAlerts(section.alertGroups);
      const colors = tr.b.generateFixedColorScheme(
          alerts.length, {hueOffset: 0.64});
      const colorForAlertGuid = new Map(alerts.map((alert, index) =>
        [alert.guid, colors[index].toString()]));
      const sequenceLength = 100;

      cp.todo('refactor to call cp.LineChart.layout()');

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
        type: 'alerts-section.layoutPreview',
        statePath,
        colorForAlertGuid,
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
          type: 'alerts-section.layoutPreview',
          statePath,
          previewLayout: false,
          colorForAlertGuid: new Map(),
        });
        return;
      }

      dispatch(AlertsSection.actions.layoutPreview(statePath));
    },

    togglePreviewing: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.toggleBooleanAtPath(
          `${statePath}.isPreviewing`));
      dispatch(AlertsSection.actions.maybeLayoutPreview(statePath));
    },

    sort: (statePath, sortColumn) => async (dispatch, getState) => {
      dispatch({
        type: 'alerts-section.sort',
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
            deltaUnit: baseUnit.correspondingDeltaUnit,
            deltaValue,
            guid: tr.b.GUID.allocateSimple(),
            isSelected: groupIndex === 0,
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
      let selectedAlertsCount = 0;
      if (alertGroups.length) {
        selectedAlertsCount = alertGroups[0].alerts.length;
      }
      return {
        ...state,
        isLoading: false,
        isOwner: Math.random() < 0.5,
        areAlertGroupsPlaceholders: false,
        selectedAlertsCount,
        alertGroups,
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
                color: action.colorForAlertGuid.get(alert.guid),
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
