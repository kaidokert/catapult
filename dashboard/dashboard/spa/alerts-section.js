/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  const ZERO_WIDTH_SPACE = String.fromCharCode(0x200b);

  const DUMMY_ALERTS = {
    alertGroups: [
      {
        isExpanded: false,
        alerts: [
          {
            isSelected: true,
            guid: tr.b.GUID.allocateSimple(),
            isSelected: false,
            revisions: '543210 - 543221',
            bot: 'nexus5X',
            testSuite: 'system_health.common_mobile',
            measurement: 'story:power_avg',
            story: 'load:chrome:blank',
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
            percentDeltaValue: 1,
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
          },
        ],
      },
      {
        isExpanded: false,
        alerts: [
          {
            guid: tr.b.GUID.allocateSimple(),
            isSelected: false,
            revisions: '543222 - 543230',
            bot: 'nexus5X',
            testSuite: 'system_health.common_mobile',
            measurement: 'story:power_avg',
            story: 'load:chrome:blank',
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
            percentDeltaValue: 1,
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
          },
        ],
      },
      {
        isExpanded: false,
        alerts: [
          {
            guid: tr.b.GUID.allocateSimple(),
            isSelected: false,
            revisions: '543210 - 543221',
            bot: 'nexus5X',
            testSuite: 'system_health.common_mobile',
            measurement: 'story:power_avg',
            story: 'load:chrome:blank',
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
            percentDeltaValue: 1,
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
          },
          {
            guid: tr.b.GUID.allocateSimple(),
            isSelected: false,
            revisions: '543210 - 543221',
            bot: 'nexus5X',
            testSuite: 'system_health.common_mobile',
            measurement: 'story:power_avg',
            story: 'load:chrome:blank',
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
            percentDeltaValue: 1,
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
          },
          {
            guid: tr.b.GUID.allocateSimple(),
            isSelected: false,
            revisions: '543210 - 543221',
            bot: 'nexus5X',
            testSuite: 'system_health.common_mobile',
            measurement: 'story:power_avg',
            story: 'load:chrome:blank',
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
            percentDeltaValue: 1,
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
          },
          {
            guid: tr.b.GUID.allocateSimple(),
            isSelected: false,
            revisions: '543240 - 543250',
            bot: 'nexus5X',
            testSuite: 'system_health.common_mobile',
            measurement: 'story:power_avg',
            story: 'load:chrome:blank',
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
            percentDeltaValue: 1,
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
          },
        ],
      },
    ]
  };

  class AlertsSection extends cp.Element {
    static get is() { return 'alerts-section'; }

    static get properties() {
      return cp.sectionProperties({
        alertGroups: {type: Array},
        selectedAlertsCount: {type: Number},
        areAlertGroupsPlaceholders: {type: Boolean},
        isFilingExistingBug: {type: Boolean},
        isFilingNewBug: {type: Boolean},
        isLoading: {type: Boolean},
        isOwner: {type: Boolean},
        isPreviewing: {type: Boolean},
        previewLayout: {type: Object},
        showingImprovements: {type: Boolean},
        showingTriaged: {type: Boolean},
        sortColumn: {type: String},
        sortDescending: {type: Boolean},
        source: {type: Object},
      });
    }

    static clearAllFocused(sectionState) {
      return {
        ...sectionState,
        source: {
          ...sectionState.source,
          isFocused: false,
        },
      };
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
      this.dispatch('focusSource', this.sectionId, true);
    }

    onSourceBlur_(e) {
      this.dispatch('focusSource', this.sectionId, false);
    }

    onSourceKeydown_(e) {
      this.dispatch('keydownSource', this.sectionId, e.detail.value);
    }

    onSourceClear_(e) {
      this.dispatch('clearSource', this.sectionId);
    }

    onSourceSelect_(e) {
      this.dispatch('selectSource', this.sectionId, e.detail.selectedOptions);
    }

    toggleShowingImprovements_() {
      this.dispatch('toggleShowingImprovements', this.sectionId);
    }

    toggleShowingTriaged_() {
      this.dispatch('toggleShowingTriaged', this.sectionId);
    }

    toggleGroupExpanded_(event) {
      this.dispatch('toggleGroupExpanded', this.sectionId,
          event.model.parentModel.alertGroupIndex);
    }

    closeSection_() {
      this.dispatch(cp.ChromeperfApp.actions.closeSection(this.sectionId));
    }

    togglePreviewing_() {
      this.dispatch('togglePreviewing', this.sectionId);
    }

    openCharts_(e) {
      const ctrlKey = e.detail.sourceEvent.ctrlKey;
      this.dispatch('openCharts', this.sectionId, ctrlKey);
    }

    fileNewBug_() {
      this.dispatch('fileNewBug', this.sectionId);
    }

    submitNewBug_() {
      this.dispatch('submitNewBug', this.sectionId);
    }

    submitExistingBug_() {
      this.dispatch('submitExistingBug', this.sectionId);
    }

    fileExistingBug_() {
      this.dispatch('fileExistingBug', this.sectionId);
    }

    ignore_() {
      this.dispatch('ignore', this.sectionId);
    }

    reportInvalid_() {
      this.dispatch('reportInvalid', this.sectionId);
    }

    selectAllAlerts_(event) {
      event.target.checked = !event.target.checked;
      this.dispatch('selectAllAlerts', this.sectionId);
    }

    selectAlert_(event) {
      this.dispatch('selectAlert', this.sectionId,
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
          this.sectionId, event.detail.path);
    }

    onCancelNewBug_() {
      this.dispatch('cancelNewBug', this.sectionId);
    }

    onCancelExistingBug_() {
      this.dispatch('cancelExistingBug', this.sectionId);
    }

    sort_(e) {
      this.dispatch('sort', this.sectionId, e.target.name);
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
    submitExistingBug: (sectionId) => async (dispatch, getState) => {
      dispatch({
        type: 'alerts-section.submitExistingBug',
        sectionId,
      });
    },

    fileExistingBug: (sectionId) => async (dispatch, getState) => {
      dispatch({
        type: 'alerts-section.fileExistingBug',
        sectionId,
      });
    },

    ignore: (sectionId) => async (dispatch, getState) => {
      // eslint-disable-next-line no-console
      console.log('TODO ignore selected alerts');
    },

    reportInvalid: (sectionId) => async (dispatch, getState) => {
      // eslint-disable-next-line no-console
      console.log('TODO report invalid selected alerts');
    },

    selectAllAlerts: (sectionId) => async (dispatch, getState) => {
      dispatch({
        type: 'alerts-section.selectAllAlerts',
        sectionId,
      });
      dispatch(AlertsSection.actions.maybeLayoutPreview(sectionId));
    },

    selectAlert: (sectionId, alertGroupIndex, alertIndex) =>
      async (dispatch, getState) => {
        dispatch({
          type: 'alerts-section.selectAlert',
          sectionId,
          alertGroupIndex,
          alertIndex,
        });
        dispatch(AlertsSection.actions.maybeLayoutPreview(sectionId));
      },

    toggleSourceGroupExpanded: (sectionId, path) =>
      async (dispatch, getState) => {
        dispatch({
          type: 'alerts-section.toggleSourceGroupExpanded',
          sectionId,
          path,
        });
      },

    cancelNewBug: (sectionId) => async (dispatch, getState) => {
      dispatch({
        type: 'alerts-section.cancelNewBug',
        sectionId,
      });
    },

    cancelExistingBug: (sectionId) => async (dispatch, getState) => {
      dispatch({
        type: 'alerts-section.cancelExistingBug',
        sectionId,
      });
    },

    openCharts: (sectionId, ctrlKey) => async (dispatch, getState) => {
      // eslint-disable-next-line no-console
      console.log('TODO if ctrlKey, open charts in a new tab');

      const alertGroups = getState().sectionsById[sectionId].alertGroups;
      for (const alert of AlertsSection.getSelectedAlerts(alertGroups)) {
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

    fileNewBug: (sectionId) => async (dispatch, getState) => {
      dispatch({
        type: 'alerts-section.fileNewBug',
        sectionId,
      });
    },

    submitNewBug: (sectionId) => async (dispatch, getState) => {
      dispatch({
        type: 'alerts-section.submitNewBug',
        sectionId,
      });
    },

    focusSource: (sectionId, isFocused) => async (dispatch, getState) => {
      dispatch({
        type: 'alerts-section.focusSource',
        sectionId,
        isFocused,
      });
    },

    keydownSource: (sectionId, inputValue) => async (dispatch, getState) => {
      dispatch({
        type: 'alerts-section.keydownSource',
        sectionId,
        inputValue,
      });
    },

    clearSource: (sectionId) => async (dispatch, getState) => {
      dispatch({
        type: 'alerts-section.clearSource',
        sectionId,
      });
    },

    updateLocation: (sectionState) => async (dispatch, getState) => {
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

    restoreFromQueryParams: (sectionId, queryParams) =>
      async (dispatch, getState) => {
        const selectedOptions = [];
        for (const param of Object.keys(queryParams)) {
          selectedOptions.push(param.replace('_', ' '));
        }
        dispatch(AlertsSection.actions.selectSource(
            sectionId, selectedOptions));

        // eslint-disable-next-line no-console
        console.log('TODO if ?charts: open charts for all alerts');
      },

    selectSource: (sectionId, selectedOptions) =>
      async (dispatch, getState) => {
        dispatch({
          type: 'alerts-section.startLoadingAlerts',
          sectionId,
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
          sectionId,
          ...DUMMY_ALERTS,
        });
      },

    toggleShowingImprovements: (sectionId) => async (dispatch, getState) => {
      // eslint-disable-next-line no-console
      console.log('TODO toggle improvements');
    },

    toggleShowingTriaged: (sectionId) => async (dispatch, getState) => {
      // eslint-disable-next-line no-console
      console.log('TODO toggle triaged');
    },

    toggleGroupExpanded: (sectionId, alertGroupIndex) =>
      async (dispatch, getState) => {
        dispatch({
          type: 'alerts-section.toggleGroupExpanded',
          sectionId,
          alertGroupIndex,
        });
      },

    layoutPreview: (sectionId) => async (dispatch, getState) => {
      dispatch({
        type: 'alerts-section.startLoadingPreview',
        sectionId,
      });
      await tr.b.timeout(500);

      const sectionState = getState().sectionsById[sectionId];
      const alerts = AlertsSection.getSelectedAlerts(
          sectionState.alertGroups);
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

      const chartSequences = [];
      for (const color of colors) {
        const y0 = parseInt(100 * Math.random());
        const sequence = {
          color: '' + color,
          dotColor: '' + color,
          data: [{x: 0, y: y0}],
          strokeWidth: 1,
        };
        chartSequences.push(sequence);
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
        sectionId,
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
          sequences: chartSequences,
          yAxisTicks: [],
          xAxisTicks: chartXAxisTicks,
          brushes: [],
        },
      });
    },

    maybeLayoutPreview: (sectionId) => async (dispatch, getState) => {
      const section = getState().sectionsById[sectionId];
      if (!section.isPreviewing || !section.selectedAlertsCount) {
        dispatch({
          type: 'alerts-section.layoutPreview',
          sectionId,
          previewLayout: false,
          colorForAlertGuid: new Map(),
        });
        return;
      }

      dispatch(AlertsSection.actions.layoutPreview(sectionId));
    },

    togglePreviewing: (sectionId) => async (dispatch, getState) => {
      dispatch({
        type: 'alerts-section.togglePreviewing',
        sectionId,
      });
      dispatch(AlertsSection.actions.maybeLayoutPreview(sectionId));
    },

    sort: (sectionId, column) => async (dispatch, getState) => {
      dispatch({
        type: 'alerts-section.sort',
        sectionId,
        column,
      });
    },
  };

  AlertsSection.reducers = {
    selectAlert: cp.sectionReducer((section, action) => {
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
        alerts = cp.assignInArray(alerts, action.alertIndex, {
          isSelected,
        });
      }

      const alertGroups = cp.assignInArray(
          section.alertGroups, action.alertGroupIndex, {alerts});
      const selectedAlertsCount = AlertsSection.getSelectedAlerts(
          alertGroups).length;
      return {
        alertGroups,
        selectedAlertsCount,
      };
    }),

    selectAllAlerts: cp.sectionReducer((section, action) => {
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

    receiveAlerts: cp.sectionReducer((section, action) => {
      return {
        isLoading: false,
        isPreviewing: true,
        isOwner: Math.random() < 0.5,
        areAlertGroupsPlaceholders: false,
        alertGroups: action.alertGroups,
      };
    }),

    toggleGroupExpanded: cp.sectionReducer((section, action) => {
      const alertGroup = section.alertGroups[action.alertGroupIndex];
      return {
        alertGroups: cp.assignInArray(
            section.alertGroups, action.alertGroupIndex, {
              isExpanded: !alertGroup.isExpanded,
            }),
      };
    }),

    focusSource: (state, action) => {
      const sectionsById = cp.ChromeperfApp.clearAllFocused(state.sectionsById);
      const section = sectionsById[action.sectionId];
      sectionsById[action.sectionId] = {
        ...section,
        source: {
          ...section.source,
          isFocused: action.isFocused,
        },
      };
      return {...state, sectionsById};
    },

    keydownSource: cp.sectionReducer((section, action) => {
      return {
        source: {
          ...section.source,
          inputValue: action.inputValue,
        },
      };
    }),

    clearSource: cp.sectionReducer((section, action) => {
      return {
        source: {
          ...section.source,
          inputValue: '',
          isFocused: true,
        },
      };
    }),

    togglePreviewing: cp.sectionReducer((section, action) => {
      return {isPreviewing: !section.isPreviewing};
    }),

    startLoadingAlerts: cp.sectionReducer((section, action) => {
      return {
        isLoading: true,
        source: {
          ...section.source,
          isFocused: false,
          inputValue: action.selectedOptions.join(', '),
          selectedOptions: action.selectedOptions,
        },
      };
    }),

    startLoadingPreview: cp.sectionReducer((section, action) => {
      return {isLoading: true};
    }),

    layoutPreview: cp.sectionReducer((section, action) => {
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
    }),

    toggleSourceGroupExpanded: cp.sectionReducer((section, action) => {
      return {
        source: {
          ...section.source,
          options: cp.DropdownInput.toggleGroupExpanded(
              section.source.options, action.path),
        },
      };
    }),

    fileNewBug: cp.sectionReducer((section, action) => {
      return {isFilingNewBug: true};
    }),

    submitNewBug: cp.sectionReducer((section, action) => {
      return {
        isFilingNewBug: false,
      };
    }),

    submitNewBug: cp.sectionReducer((section, action) => {
      return {isFilingNewBug: false};
    }),

    fileExistingBug: cp.sectionReducer((section, action) => {
      return {isFilingExistingBug: true};
    }),

    submitExistingBug: cp.sectionReducer((section, action) => {
      return {isFilingExistingBug: false};
    }),

    cancelExistingBug: cp.sectionReducer((section, action) => {
      return {isFilingExistingBug: false};
    }),

    sort: cp.sectionReducer((section, action) => {
      return {
        sortColumn: action.column,
        sortDescending:
            section.sortDescending ^ (section.sortColumn === action.column),
      };
    }),
  };

  cp.Element.register(AlertsSection);

  return {
    AlertsSection,
  };
});
