/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  // TODO insert zero-width spaces after colons in measurements and stories.

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

    async ready() {
      super.ready();
      this.scrollIntoView(true);
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
      this.dispatch(AlertsSection.focusSource(this.sectionId, true));
    }

    onSourceBlur_(e) {
      this.dispatch(AlertsSection.focusSource(this.sectionId, false));
    }

    static focusSource(sectionId, isFocused) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'alerts-section.focusSource',
          sectionId,
          isFocused,
        });
      };
    }

    onSourceKeydown_(e) {
      this.dispatch(AlertsSection.keydownSource(
          this.sectionId, e.detail.value));
    }

    static keydownSource(sectionId, inputValue) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'alerts-section.keydownSource',
          sectionId,
          inputValue,
        });
      };
    }

    onSourceClear_(e) {
      this.dispatch(AlertsSection.clearSource(this.sectionId));
    }

    static clearSource(sectionId) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'alerts-section.clearSource',
          sectionId,
        });
      };
    }

    onSourceSelect_(e) {
      this.dispatch(AlertsSection.selectSource(
          this.sectionId, e.detail.selectedOptions));
    }

    static selectSource(sectionId, selectedOptions) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'alerts-section.startLoadingAlerts',
          sectionId,
          selectedOptions,
        });

        const state = getState();
        if (state.sectionIds.length === 1) {
          if (selectedOptions.length === 0) {
            dispatch(cp.ChromeperfApp.clearRoute());
          } else {
            const queryParams = {};
            for (const option of selectedOptions) {
              queryParams[option.replace(' ', '_')] = '';
            }
            // TODO also save showingImprovements, showingTriaged, etc
            dispatch(cp.ChromeperfApp.routeChange('alerts', queryParams));
          }
        } else {
          dispatch(cp.ChromeperfApp.saveSession());
        }

        // TODO fetch alerts via cache
        await tr.b.timeout(500);

        dispatch({
          type: 'alerts-section.receiveAlerts',
          sectionId,
          ...DUMMY_ALERTS,
        });
      };
    }

    toggleShowingImprovements_() {
      this.dispatch(AlertsSection.toggleShowingImprovements(this.sectionId));
    }

    static toggleShowingImprovements(sectionId) {
      return async (dispatch, getState) => {
        // TODO
      };
    }

    toggleShowingTriaged_() {
      this.dispatch(AlertsSection.toggleShowingTriaged(this.sectionId));
    }

    static toggleShowingTriaged(sectionId) {
      return async (dispatch, getState) => {
        // TODO
      };
    }

    toggleGroupExpanded_(event) {
      this.dispatch(AlertsSection.toggleGroupExpanded(
          this.sectionId, event.model.parentModel.alertGroupIndex));
    }

    static toggleGroupExpanded(sectionId, alertGroupIndex) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'alerts-section.toggleGroupExpanded',
          sectionId,
          alertGroupIndex,
        });
      };
    }

    closeSection_() {
      this.dispatch(cp.ChromeperfApp.closeSection(this.sectionId));
    }

    togglePreviewing_() {
      this.dispatch(AlertsSection.togglePreviewing(this.sectionId));
    }

    static layoutPreview(sectionId) {
      return async (dispatch, getState) => {
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

        // TODO LineChart.layout()

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
      };
    }

    static maybeLayoutPreview(sectionId) {
      return async (dispatch, getState) => {
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

        dispatch(AlertsSection.layoutPreview(sectionId));
      };
    }

    static togglePreviewing(sectionId) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'alerts-section.togglePreviewing',
          sectionId,
        });
        dispatch(AlertsSection.maybeLayoutPreview(sectionId));
      };
    }

    openCharts_(e) {
      const ctrlKey = e.detail.sourceEvent.ctrlKey;
      this.dispatch(AlertsSection.openCharts(this.sectionId, ctrlKey));
    }

    static openCharts(sectionId, ctrlKey) {
      return async (dispatch, getState) => {
        // TODO: if ctrlKey, open charts in a new tab.
        const alertGroups = getState().sectionsById[sectionId].alertGroups;
        for (const alert of AlertsSection.getSelectedAlerts(alertGroups)) {
          const testPath = [
            [alert.testSuite],
            [alert.bot],
            [alert.measurement],
            [alert.story],
          ];
          const chartId = tr.b.GUID.allocateSimple();
          // TODO pass state through newSection, change NEW_STATE to a static
          // method
          // TODO plumb revisions
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
          dispatch(cp.ChartSection.maybeLoadTimeseries(chartId));
        }
        dispatch({type: 'chromeperf-app.clearAllFocused'});
      };
    }

    fileNewBug_() {
      this.dispatch(AlertsSection.fileNewBug(this.sectionId));
    }

    static fileNewBug(sectionId) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'alerts-section.fileNewBug',
          sectionId,
        });
      };
    }

    submitNewBug_() {
      this.dispatch(AlertsSection.submitNewBug(this.sectionId));
    }

    static submitNewBug(sectionId) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'alerts-section.submitNewBug',
          sectionId,
        });
      };
    }

    submitExistingBug_() {
      this.dispatch(AlertsSection.submitExistingBug(this.sectionId));
    }

    static submitExistingBug(sectionId) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'alerts-section.submitExistingBug',
          sectionId,
        });
      };
    }

    fileExistingBug_() {
      this.dispatch(AlertsSection.fileExistingBug(this.sectionId));
    }

    static fileExistingBug(sectionId) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'alerts-section.fileExistingBug',
          sectionId,
        });
      };
    }

    ignore_() {
      this.dispatch(AlertsSection.ignore(this.sectionId));
    }

    static ignore(sectionId) {
      return async (dispatch, getState) => {
        // TODO
      };
    }

    reportInvalid_() {
      this.dispatch(AlertsSection.reportInvalid(this.sectionId));
    }

    static reportInvalid(sectionId) {
      return async (dispatch, getState) => {
        // TODO
      };
    }

    selectAllAlerts_(event) {
      event.target.checked = !event.target.checked;
      this.dispatch(AlertsSection.selectAllAlerts(this.sectionId));
    }

    static selectAllAlerts(sectionId) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'alerts-section.selectAllAlerts',
          sectionId,
        });
        dispatch(AlertsSection.maybeLayoutPreview(sectionId));
      };
    }

    selectAlert_(event) {
      this.dispatch(AlertsSection.selectAlert(
          this.sectionId,
          event.model.parentModel.alertGroupIndex,
          event.model.alertIndex));
    }

    static selectAlert(sectionId, alertGroupIndex, alertIndex) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'alerts-section.selectAlert',
          sectionId,
          alertGroupIndex,
          alertIndex,
        });
        dispatch(AlertsSection.maybeLayoutPreview(sectionId));
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

    onDotClick_(event) {
      // TODO
    }

    onDotMouseOver_(event) {
      // TODO
    }

    onDotMouseOut_(event) {
      // TODO
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

    onSourceToggleGroupExpanded_(event) {
      this.dispatch(AlertsSection.toggleSourceGroupExpanded(
          this.sectionId, event.detail.path));
    }

    static toggleSourceGroupExpanded(sectionId, path) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'alerts-section.toggleSourceGroupExpanded',
          sectionId,
          path,
        });
      };
    }

    onCancelNewBug_() {
      this.dispatch(AlertsSection.cancelNewBug(this.sectionId));
    }

    static cancelNewBug(sectionId) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'alerts-section.cancelNewBug',
          sectionId,
        });
      };
    }

    onCancelExistingBug_() {
      this.dispatch(AlertsSection.cancelExistingBug(this.sectionId));
    }

    static cancelExistingBug(sectionId) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'alerts-section.cancelExistingBug',
          sectionId,
        });
      };
    }

    sort_(e) {
      this.dispatch(AlertsSection.sort(this.sectionId, e.target.name));
    }

    static sort(sectionId, column) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'alerts-section.sort',
          sectionId,
          column,
        });
      };
    }
  }
  customElements.define(AlertsSection.is, AlertsSection);

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

  cp.sectionReducer('alerts-section.selectAlert', (state, action, section) => {
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
    return {
      alertGroups,
      selectedAlertsCount: AlertsSection.getSelectedAlerts(alertGroups).length,
    };
  });

  cp.sectionReducer('alerts-section.selectAllAlerts',
      (state, action, section) => {
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
      });

  cp.sectionReducer('alerts-section.receiveAlerts',
      (state, action, section) => {
        return {
          isLoading: false,
          isPreviewing: true,
          isOwner: Math.random() < 0.5,
          areAlertGroupsPlaceholders: false,
          alertGroups: action.alertGroups,
        };
      });

  cp.sectionReducer('alerts-section.toggleGroupExpanded',
      (state, action, section) => {
        const alertGroup = section.alertGroups[action.alertGroupIndex];
        return {
          alertGroups: cp.assignInArray(
              section.alertGroups, action.alertGroupIndex, {
                isExpanded: !alertGroup.isExpanded,
              }),
        };
      });

  cp.REDUCERS.set('alerts-section.focusSource', (state, action) => {
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
  });

  cp.sectionReducer('alerts-section.keydownSource',
      (state, action, section) => {
        return {
          source: {
            ...section.source,
            inputValue: action.inputValue,
          },
        };
      });

  cp.sectionReducer('alerts-section.clearSource', (state, action, section) => {
    return {
      source: {
        ...section.source,
        inputValue: '',
        isFocused: true,
      },
    };
  });

  cp.sectionReducer('alerts-section.togglePreviewing',
      (state, action, section) => {
        return {
          isPreviewing: !section.isPreviewing,
        };
      });

  cp.sectionReducer('alerts-section.startLoadingAlerts',
      (state, action, section) => {
        return {
          isLoading: true,
          source: {
            ...section.source,
            isFocused: false,
            inputValue: action.selectedOptions.join(', '),
            selectedOptions: action.selectedOptions,
          },
        };
      });

  cp.sectionReducer('alerts-section.startLoadingPreview',
      (state, action, section) => {
        return {
          isLoading: true,
        };
      });

  cp.sectionReducer('alerts-section.layoutPreview',
      (state, action, section) => {
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
      });

  cp.sectionReducer('alerts-section.toggleSourceGroupExpanded',
      (state, action, section) => {
        return {
          source: {
            ...section.source,
            options: cp.DropdownInput.toggleGroupExpanded(
                section.source.options, action.path),
          },
        };
      });

  cp.sectionReducer('alerts-section.fileNewBug', (state, action, section) => {
    return {
      isFilingNewBug: true,
    };
  });

  cp.sectionReducer('alerts-section.submitNewBug', (state, action, section) => {
    return {
      isFilingNewBug: false,
    };
  });

  cp.sectionReducer('alerts-section.cancelNewBug',
      (state, action, section) => {
        return {
          isFilingNewBug: false,
        };
      });

  cp.sectionReducer('alerts-section.fileExistingBug',
      (state, action, section) => {
        return {
          isFilingExistingBug: true,
        };
      });

  cp.sectionReducer('alerts-section.submitExistingBug',
      (state, action, section) => {
        return {
          isFilingExistingBug: false,
        };
      });

  cp.sectionReducer('alerts-section.cancelExistingBug',
      (state, action, section) => {
        return {
          isFilingExistingBug: false,
        };
      });

  cp.sectionReducer('alerts-section.sort', (state, action, section) => {
    return {
      sortColumn: action.column,
      sortDescending:
          section.sortDescending ^ (section.sortColumn === action.column),
    };
  });

  return {
    AlertsSection,
  };
});
