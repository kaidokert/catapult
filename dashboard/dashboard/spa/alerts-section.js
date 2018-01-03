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

    static clearAllFocused(state) {
      return Polymer.Path.setImmutable(state, 'source', source => {
        return {...source, isFocused: false};
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

    ready() {
      super.ready();
      this.scrollIntoView(true);
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

    onSourceFocus_(e) {
      this.dispatch('focusSource', this.statePath, true);
    }

    onSourceBlur_(e) {
      this.dispatch('focusSource', this.statePath, false);
    }

    onSourceKeydown_(e) {
      this.dispatch('keydownSource', this.statePath, e.detail.value);
    }

    onSourceClear_(e) {
      this.dispatch('clearSource', this.statePath);
    }

    onSourceSelect_(e) {
      this.dispatch('selectSource', this.statePath,
          this.source.selectedOptions);
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
  }

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
      isFocused: true,
      selectedOptions: [],
      options: [
        {
          label: 'Bug',
          isExpanded: false,
          options: [
            '654321',
          ],
        },
        {
          label: 'Sheriffs',
          isExpanded: true,
          options: cp.dummySheriffs(),
        },
        {
          label: 'Releasing Reports',
          isExpanded: false,
          options: [
            {
              label: 'M63',
              isExpanded: false,
              options: [
                {label: 'Public', value: 'Releasing Public M63'},
                {label: 'Memory', value: 'Releasing Memory M63'},
                {label: 'Power', value: 'Releasing Power M63'},
              ],
            },
            {
              label: 'M64',
              isExpanded: false,
              options: [
                {label: 'Public', value: 'Releasing Public M64'},
                {label: 'Memory', value: 'Releasing Memory M64'},
                {label: 'Power', value: 'Releasing Power M64'},
              ],
            },
          ],
        }
      ],
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
          story: '-----',
        },
      ],
    });
  }

  AlertsSection.actions = {
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
      cp.todo('if ctrlKey, open charts in a new tab');

      const state = getState();
      const section = Polymer.Path.get(state, statePath);
      for (const alert of AlertsSection.getSelectedAlerts(
          section.alertGroups)) {
        const testPath = [
          [alert.testSuite],
          [alert.bot],
          [alert.measurement],
          [alert.story],
        ];
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
              testPath[i]));
        }
        dispatch(cp.ChartSection.actions.selectTestPathComponent(
            `sectionsById.${chartId}`, 0));
      }
      dispatch(cp.ChromeperfApp.actions.focus('', false));
    },

    fileNewBug: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObjectAtPath(
          statePath, {isFilingNewBug: true}));
    },

    submitNewBug: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObjectAtPath(
          statePath, {isFilingNewBug: false}));
    },

    focusSource: (statePath, isFocused) => async (dispatch, getState) => {
      dispatch(cp.ChromeperfApp.actions.focus(
          `${statePath}.source`, isFocused));
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
        dispatch(AlertsSection.actions.selectSource(
            statePath, selectedOptions));

        cp.todo('if ?charts: open charts for all alerts');
      },

    selectSource: (statePath, selectedOptions) =>
      async (dispatch, getState) => {
        dispatch({
          type: 'alerts-section.startLoadingAlerts',
          statePath,
          selectedOptions,
        });
        dispatch(cp.ChromeperfApp.actions.updateLocation());

        const fetchMark = tr.b.Timing.mark('alerts-section', 'fetch');
        cp.todo('fetch Alerts from backend via cache');
        await tr.b.timeout(500);
        fetchMark.end();

        dispatch({
          type: 'alerts-section.receiveAlerts',
          statePath,
          alertGroups: cp.dummyAlerts(),
        });
      },

    toggleShowingImprovements: statePath => async (dispatch, getState) => {
      cp.todo('toggle improvements');
    },

    toggleShowingTriaged: statePath => async (dispatch, getState) => {
      cp.todo('toggle triaged');
    },

    layoutPreview: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObjectAtPath(
          statePath, {isLoading: true}));

      await tr.b.timeout(500);

      const state = getState();
      const section = Polymer.Path.get(state, statePath);
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
      const state = getState();
      const section = Polymer.Path.get(state, statePath);
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
      dispatch(cp.ElementBase.actions.updateObjectAtPath(statePath, {
        sortColumn,
        sortDescending:
            section.sortDescending ^ (section.sortColumn === sortColumn),
      }));
    },
  };

  AlertsSection.reducers = {
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
      return {
        ...state,
        isLoading: false,
        isOwner: Math.random() < 0.5,
        areAlertGroupsPlaceholders: false,
        alertGroups: action.alertGroups,
      };
    }),

    startLoadingAlerts: cp.ElementBase.statePathReducer((state, action) => {
      return {
        ...state,
        isLoading: true,
        source: {
          ...state.source,
          isFocused: false,
          inputValue: action.selectedOptions.join(', '),
          selectedOptions: action.selectedOptions,
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
