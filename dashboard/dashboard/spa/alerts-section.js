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

    static clearAllFocused(sectionState) {
      return cp.ElementBase.setStateAtPath(sectionState, 'source', {
        isFocused: false,
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
      this.dispatch('selectSource', this.statePath, e.detail.selectedOptions);
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
      this.dispatch(cp.ChromeperfApp.actions.closeSection(this.statePath));
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
      // eslint-disable-next-line no-console
      console.log('TODO open timeseries in new chart-section');
    }

    onDotMouseOver_(event) {
      // TODO
    }

    onDotMouseOut_(event) {
      // TODO
    }

    onSourceToggleGroupExpanded_(event) {
      this.dispatch('toggleSourceGroupExpanded',
          this.statePath, event.detail.path);
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
    isPreviewing: false,
    previewLayout: false,
    sortColumn: 'revisions',
    sortDescending: false,
    selectedAlertsCount: 0,
    isOwner: false,
    alertGroups: [
      {
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
      },
      {
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
      },
      {
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
      },
      {
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
      },
      {
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
      },
    ],
    areAlertGroupsPlaceholders: true,
    isLoading: false,
    showingImprovements: false,
    showingTriaged: false,
    source: {
      inputValue: '',
      isFocused: true,
      selectedOptions: [],
      options: [
        {
          label: 'Bug',
          isExpanded: false,
          children: [
            '654321',
          ],
        },
        {
          label: 'Sheriffs',
          isExpanded: true,
          children: [
            'ARC',
            'Angle',
            'Binary Size',
            'Blink Memory Mobile',
            'Chrome OS Graphics',
            'Chrome OS Installer',
            'Chrome OS',
            'Chrome Accessibility',
            'Chromium AV',
            'Chromium',
            'CloudView',
            'Cronet',
            'Jochen',
            'Mojo',
            'NaCl',
            'Network Service',
            'OWP Storage',
            'Oilpan',
            'Pica',
            'Power',
            'Service Worker',
            'Tracing',
            'V8 Memory',
            'V8',
            'WebView',
          ],
        },
        {
          label: 'Releasing Reports',
          isExpanded: false,
          children: [
            {
              label: 'M63',
              children: [
                {label: 'Public', value: 'Releasing Public M63'},
                {label: 'Memory', value: 'Releasing Memory M63'},
                {label: 'Power', value: 'Releasing Power M63'},
              ],
            },
            {
              label: 'M64',
              children: [
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

  AlertsSection.actions = {
    submitExistingBug: statePath => async (dispatch, getState) => {
      dispatch({
        type: 'alerts-section.submitExistingBug',
        statePath,
      });
    },

    fileExistingBug: statePath => async (dispatch, getState) => {
      dispatch({
        type: 'alerts-section.fileExistingBug',
        statePath,
      });
    },

    ignore: statePath => async (dispatch, getState) => {
      // eslint-disable-next-line no-console
      console.log('TODO ignore selected alerts');
    },

    reportInvalid: statePath => async (dispatch, getState) => {
      // eslint-disable-next-line no-console
      console.log('TODO report invalid selected alerts');
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
      dispatch({
        type: 'alerts-section.cancelExistingBug',
        statePath,
      });
    },

    openCharts: (statePath, ctrlKey) => async (dispatch, getState) => {
      // eslint-disable-next-line no-console
      console.log('TODO if ctrlKey, open charts in a new tab');

      const state = getState();
      const section = cp.ElementBase.getStateAtPath(state, action.statePath);
      for (const alert of AlertsSection.getSelectedAlerts(
          section.alertGroups)) {
        const testPath = [
          [alert.testSuite],
          [alert.bot],
          [alert.measurement],
          [alert.story],
        ];
        const chartId = tr.b.GUID.allocateSimple();

        // eslint-disable-next-line no-console
        console.log('TODO refactor NEW_STATE to a static method');
        // eslint-disable-next-line no-console
        console.log('TODO select alert revisions in chart');

        dispatch({
          type: 'chromeperf-app.newSection',
          sectionType: 'chart-section',
          sectionId: chartId,
        });
        for (let i = 0; i < testPath.length; ++i) {
          dispatch({
            type: 'test-path-component.select',
            sectionId: chartId,
            componentIndex: i,
            selectedOptions: testPath[i],
          });
        }
        dispatch(cp.ChartSection.actions.maybeLoadTimeseries(chartId));
      }
      dispatch({type: 'chromeperf-app.clearAllFocused'});
    },

    fileNewBug: statePath => async (dispatch, getState) => {
      dispatch({
        type: 'alerts-section.fileNewBug',
        statePath,
      });
    },

    submitNewBug: statePath => async (dispatch, getState) => {
      dispatch({
        type: 'alerts-section.submitNewBug',
        statePath,
      });
    },

    focusSource: (statePath, isFocused) => async (dispatch, getState) => {
      dispatch({
        type: 'alerts-section.focusSource',
        statePath,
        isFocused,
      });
    },

    keydownSource: (statePath, inputValue) => async (dispatch, getState) => {
      dispatch({
        type: 'alerts-section.keydownSource',
        statePath,
        inputValue,
      });
    },

    clearSource: statePath => async (dispatch, getState) => {
      dispatch({
        type: 'alerts-section.clearSource',
        statePath,
      });
    },

    updateLocation: sectionState => async (dispatch, getState) => {
      const selectedOptions = sectionState.source.selectedOptions;
      if (selectedOptions.length === 0) {
        dispatch(cp.ChromeperfApp.updateRoute('', {}));
        return;
      }
      const queryParams = {};
      for (const option of selectedOptions) {
        queryParams[option.replace(' ', '_')] = '';
      }
      // eslint-disable-next-line no-console
      console.log('TODO store showingImprovements, showingTriaged');
      dispatch(cp.ChromeperfApp.updateRoute('alerts', queryParams));
    },

    restoreFromQueryParams: (statePath, queryParams) =>
      async (dispatch, getState) => {
        const selectedOptions = [];
        for (const param of Object.keys(queryParams)) {
          selectedOptions.push(param.replace('_', ' '));
        }
        dispatch(AlertsSection.actions.selectSource(
            statePath, selectedOptions));

        // eslint-disable-next-line no-console
        console.log('TODO if ?charts: open charts for all alerts');
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
        // eslint-disable-next-line no-console
        console.log('TODO fetch Alerts from backend via cache');
        await tr.b.timeout(500);
        fetchMark.end();

        dispatch({
          type: 'alerts-section.receiveAlerts',
          statePath,
          alertGroups: cp.dummyAlerts(),
        });
      },

    toggleShowingImprovements: statePath => async (dispatch, getState) => {
      // eslint-disable-next-line no-console
      console.log('TODO toggle improvements');
    },

    toggleShowingTriaged: statePath => async (dispatch, getState) => {
      // eslint-disable-next-line no-console
      console.log('TODO toggle triaged');
    },

    toggleGroupExpanded: (statePath, alertGroupIndex) =>
      async (dispatch, getState) => {
        dispatch({
          type: 'alerts-section.toggleGroupExpanded',
          statePath,
          alertGroupIndex,
        });
      },

    layoutPreview: statePath => async (dispatch, getState) => {
      dispatch({
        type: 'element-base.setStateAtPath',
        statePath: statePath.concat(['isLoading']),
        value: true,
      });
      await tr.b.timeout(500);

      const state = getState();
      const section = cp.ElementBase.getStateAtPath(state, action.statePath);
      const alerts = AlertsSection.getSelectedAlerts(section.alertGroups);
      const colors = tr.b.generateFixedColorScheme(
          alerts.length, {hueOffset: 0.64});
      const colorForAlertGuid = new Map(alerts.map((alert, index) =>
        [alert.guid, colors[index].toString()]));
      const sequenceLength = 100;

      // eslint-disable-next-line no-console
      console.log('TODO refactor to call cp.LineChart.layout()');

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
      const section = cp.ElementBase.getStateAtPath(state, action.statePath);
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
      dispatch({
        type: 'alerts-section.togglePreviewing',
        statePath,
      });
      dispatch(AlertsSection.actions.maybeLayoutPreview(statePath));
    },

    sort: (statePath, column) => async (dispatch, getState) => {
      dispatch({
        type: 'alerts-section.sort',
        statePath,
        column,
      });
    },
  };

  AlertsSection.reducers = {
    selectAlert: cp.statePathReducer((section, action) => {
      const alertGroup = section.alertGroups[action.alertGroupIndex];
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
        alerts = cp.ElementBase.setStateAtPath(
            alerts, [action.alertIndex], {isSelected}, {assignObject: true});
      }

      const alertGroups = cp.ElementBase.setStateAtPath(
          section.alertGroups, [action.alertGroupIndex], {alerts},
          {assignObject: true});
      const selectedAlertsCount = AlertsSection.getSelectedAlerts(
          alertGroups).length;
      return {
        alertGroups,
        selectedAlertsCount,
      };
    }, {assignObject: true}),

    selectAllAlerts: cp.statePathReducer((section, action) => {
      const select = (section.selectedAlertsCount === 0);
      const alertGroups = section.alertGroups.map(alertGroup => {
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
        alertGroups,
        selectedAlertsCount: AlertsSection.getSelectedAlerts(
            alertGroups).length,
      };
    }),

    receiveAlerts: cp.statePathReducer((section, action) => {
      return {
        isLoading: false,
        isPreviewing: true,
        isOwner: Math.random() < 0.5,
        areAlertGroupsPlaceholders: false,
        alertGroups: action.alertGroups,
      };
    }),

    toggleGroupExpanded: cp.statePathReducer((section, action) => {
      const alertGroup = section.alertGroups[action.alertGroupIndex];
      return cp.ElementBase.setStateAtPath(
          section, ['alertGroups', action.alertGroupIndex, 'isExpanded'],
          !alertGroup.isExpanded);
    }),

    focusSource: (state, action) => {
      state = cp.ChromeperfApp.clearAllFocused(state);
      if (!action.isFocused) return state;
      // When focusing a dropdown-input, all other dropdown-inputs must be
      // blurred in the same reducer due to how dropdown-input propagates focus
      // between redux and the DOM. Otherwise, infinite recursion can occur.
      return cp.ElementBase.setStateAtPath(
          state, action.statePath.concat(['source', 'isFocused']), true);
    },

    keydownSource: cp.statePathReducer((section, action) =>
      cp.ElementBase.setStateAtPath(
          section, ['source', 'inputValue'], action.inputValue)),

    clearSource: cp.statePathReducer((section, action) =>
      cp.ElementBase.setStateAtPath(
          section, ['source'], {
            inputValue: '',
            isFocused: true,
          }, {assignObject: true})),

    togglePreviewing: cp.statePathReducer((section, action) => {
      return {isPreviewing: !section.isPreviewing};
    }, {assignObject: true}),

    startLoadingAlerts: cp.statePathReducer((section, action) => {
      return {
        isLoading: true,
        source: {
          ...section.source,
          isFocused: false,
          inputValue: action.selectedOptions.join(', '),
          selectedOptions: action.selectedOptions,
        },
      };
    }, {assignObject: true}),

    layoutPreview: cp.statePathReducer((section, action) => {
      return {
        isLoading: false,
        previewLayout: action.previewLayout,
        alertGroups: section.alertGroups.map(alertGroup => {
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
    }, {assignObject: true}),

    toggleSourceGroupExpanded: cp.statePathReducer((section, action) => {
      return {
        source: {
          ...section.source,
          options: cp.DropdownInput.toggleGroupExpanded(
              section.source.options, action.path),
        },
      };
    }),

    fileNewBug: cp.statePathReducer((section, action) => {
      return {isFilingNewBug: true};
    }),

    submitNewBug: cp.statePathReducer((section, action) => {
      return {
        isFilingNewBug: false,
      };
    }),

    submitNewBug: cp.statePathReducer((section, action) => {
      return {isFilingNewBug: false};
    }),

    fileExistingBug: cp.statePathReducer((section, action) => {
      return {isFilingExistingBug: true};
    }),

    submitExistingBug: cp.statePathReducer((section, action) => {
      return {isFilingExistingBug: false};
    }),

    cancelExistingBug: cp.statePathReducer((section, action) => {
      return {isFilingExistingBug: false};
    }),

    sort: cp.statePathReducer((section, action) => {
      return {
        sortColumn: action.column,
        sortDescending:
            section.sortDescending ^ (section.sortColumn === action.column),
      };
    }),
  };

  cp.ElementBase.register(AlertsSection);

  return {
    AlertsSection,
  };
});
