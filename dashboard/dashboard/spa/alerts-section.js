/*
Copyright 2017 The Chromium Authors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be
found in the LICENSE file.
*/
'use strict';

tr.exportTo('cp', () => {
  const DUMMY_ALERTS = {
    summary:  '6 alerts in 3 groups',
    rows: [
      {
        revisions: '543210 - 543221',
        bot: 'nexus5X',
        testSuite: 'system_health.common_mobile',
        testParts: ['story:power_avg', 'load_chrome_blank', '', '', ''],
        delta: '1.000 W',
        deltaPct: '100%',
      },
      {
        revisions: '543222 - 543230',
        bot: 'nexus5X',
        testSuite: 'system_health.common_mobile',
        testParts: ['story:power_avg', 'load_chrome_blank', '', '', ''],
        delta: '1.000 W',
        deltaPct: '100%',
      },
      {
        isGroupExpanded: false,
        numGroupMembers: 4,
        subRows: [
          {
            isGroupExpanded: true,
            revisions: '543210 - 543221',
            bot: 'nexus5X',
            testSuite: 'system_health.common_mobile',
            testParts: ['story:power_avg', 'load_chrome_blank', '', '', ''],
            delta: '1.000 W',
            deltaPct: '100%',
          },
          {
            isGroupExpanded: true,
            revisions: '543210 - 543221',
            bot: 'nexus5X',
            testSuite: 'system_health.common_mobile',
            testParts: ['story:power_avg', 'load_chrome_blank', '', '', ''],
            delta: '1.000 W',
            deltaPct: '100%',
          },
          {
            isGroupExpanded: true,
            revisions: '543210 - 543221',
            bot: 'nexus5X',
            testSuite: 'system_health.common_mobile',
            testParts: ['story:power_avg', 'load_chrome_blank', '', '', ''],
            delta: '1.000 W',
            deltaPct: '100%',
          },
        ],
        revisions: '543240 - 543250',
        bot: 'nexus5X',
        testSuite: 'system_health.common_mobile',
        testParts: ['story:power_avg', 'load_chrome_blank', '', '', ''],
        delta: '1.000 W',
        deltaPct: '100%',
      },
    ]
  };

  class AlertsSection extends cp.Element {
    static get is() { return 'alerts-section'; }

    static get properties() {
      return cp.sectionProperties({
        isLoading: {type: Boolean},
        source: {type: Object},
        summary: {type: String},
        showingImprovements: {type: Boolean},
        showingTriaged: {type: Boolean},
        areRowsPlaceholders: {type: Boolean},
        rows: {type: Array},
        anyAlertsSelected: {type: Boolean},
        isPreviewing: {type: Boolean},
        previewLayout: {type: Object},
      });
    }

    async ready() {
      super.ready();
      this.scrollIntoView(true);
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
      this.dispatch(AlertsSection.keydownSource(this.sectionId, e.detail.value));
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
      this.dispatch(AlertsSection.selectSource(this.sectionId, e.detail.value));
    }

    static selectSource(sectionId, sheriff) {
      return async (dispatch, getState) => {
        dispatch(Object.assign({
          type: 'alerts-section.receiveAlerts',
          sectionId,
        }, DUMMY_ALERTS));
      };
    }

    toggleShowingImprovements_() {
      // TODO this.dispatch('toggleShowingImprovements', this.sectionId);
    }

    toggleShowingTriaged_() {
      // TODO this.dispatch('toggleShowingTriaged', this.sectionId);
    }

    toggleGroupExpanded_(event) {
      this.dispatch(AlertsSection.toggleGroupExpanded(
        this.sectionId, event.model.item));
    }

    static toggleGroupExpanded(sectionId, alertRow) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'alerts-section.toggleGroupExpanded',
          sectionId,
          rowIndex: getState().sections[sectionId].rows.indexOf(alertRow),
        });
      };
    }

    closeSection_() {
      this.dispatch(cp.ChromeperfApp.closeSection(this.sectionId));
    }

    togglePreviewing_() {
      this.dispatch(AlertsSection.togglePreviewing(this.sectionId));
    }

    static async layoutPreview(sectionState) {
      const alerts = AlertsSection.getSelectedAlerts(sectionState.rows);
      const colors = tr.b.generateFixedColorScheme(alerts.length);
      const sequenceLength = 100;

      // TODO LineChart.layout()

      const maxYAxisTickWidth = 30;
      const textHeight = 15;
      const chartHeight = 200;

      const chartSequences = [];
      for (const color of colors) {
        const y0 = parseInt(100 * Math.random());
        const sequence = {
          path: 'M0,' + y0,
          color: '' + color,
          dotColor: '' + color,
          data: [{x: 0, y: y0 + '%'}],
        };
        chartSequences.push(sequence);
        for (let i = 0; i < sequenceLength; i += 1) {
          const datum = {
            x: parseInt(100 * (i + 1) / sequenceLength),
            y: parseInt(100 * Math.random()),
          };
          sequence.data.push(datum);
          sequence.path += ' L' + datum.x + ',' + datum.y;
          datum.x += '%';
          datum.y += '%';
        }
      }

      const chartXAxisTicks = [
        'Dec', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13',
        '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24',
        '25', '26', '27', '28', '29', '30', '31', '2018', '2', '3',
      ].map((text, index, texts) => ({
        text,
        x: (100 * (index + 0.5) / texts.length) + '%',
        y: chartHeight - 5,
      }));

      return {
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
        antiBrushes: [],
      };
    }

    static maybeLayoutPreview(sectionId) {
      return async (dispatch, getState) => {
        const section = getState().sections[sectionId];
        if (!section.isPreviewing || !section.anyAlertsSelected) {
          dispatch({
            type: 'alerts-section.layoutPreview',
            sectionId,
            previewLayout: false,
          });
          return;
        }

        dispatch({
          type: 'alerts-section.startLoadingPreview',
          sectionId,
        });
        dispatch({
          type: 'alerts-section.layoutPreview',
          sectionId,
          previewLayout: await AlertsSection.layoutPreview(section),
        });
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

    fileNewBug_() {
      this.dispatch(AlertsSection.fileNewBug(this.sectionId));
    }

    fileExistingBug_() {
      this.dispatch(AlertsSection.fileExistingBug(this.sectionId));
    }

    ignore_() {
      this.dispatch(AlertsSection.ignore(this.sectionId));
    }

    reportInvalid_() {
      this.dispatch(AlertsSection.reportInvalid(this.sectionId));
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
      this.dispatch(AlertsSection.selectAlert(this.sectionId, event.model.item));
    }

    static selectAlert(sectionId, alert) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'alerts-section.selectAlert',
          sectionId,
          alert,
        });
        dispatch(AlertsSection.maybeLayoutPreview(sectionId));
      };
    }

    static getSelectedAlerts(rows) {
      const selectedAlerts = [];
      for (const row of rows) {
        if (row.isSelected) {
          selectedAlerts.push(row);
        }
        for (const subRow of (row.subRows || [])) {
          if (subRow.isSelected) {
            selectedAlerts.push(subRow);
          }
        }
      }
      return selectedAlerts;
    }
  }
  customElements.define(AlertsSection.is, AlertsSection);

  AlertsSection.NEW_STATE = {
    isPreviewing: false,
    previewLayout: false,
    anyAlertsSelected: false,
    rows: [
      {
        revisions: '-----',
        bot: '-----',
        testSuite: '-----',
        testParts: ['-----', '', '', '', ''],
        delta: '-----',
        deltaPct: '-----',
      },
      {
        revisions: '-----',
        bot: '-----',
        testSuite: '-----',
        testParts: ['-----', '', '', '', ''],
        delta: '-----',
        deltaPct: '-----',
      },
      {
        revisions: '-----',
        bot: '-----',
        testSuite: '-----',
        testParts: ['-----', '', '', '', ''],
        delta: '-----',
        deltaPct: '-----',
      },
      {
        revisions: '-----',
        bot: '-----',
        testSuite: '-----',
        testParts: ['-----', '', '', '', ''],
        delta: '-----',
        deltaPct: '-----',
      },
      {
        revisions: '-----',
        bot: '-----',
        testSuite: '-----',
        testParts: ['-----', '', '', '', ''],
        delta: '-----',
        deltaPct: '-----',
      },
    ],
    areRowsPlaceholders: true,
    isLoading: false,
    showingImprovements: false,
    showingTriaged: false,
    source: {
      inputValue: '',
      isFocused: true,
      selectedOptions: [],
      options: [
        "ARC Perf Sheriff",
        "Angle Perf Sheriff",
        "Binary Size Sheriff",
        "Blink Memory Mobile Sheriff",
        "Chrome OS Graphics Perf Sheriff",
        "Chrome OS Installer Perf Sheriff",
        "Chrome OS Perf Sheriff",
        "Chrome Perf Accessibility Sheriff",
        "Chromium Perf AV Sheriff",
        "Chromium Perf Sheriff",
        "Chromium Perf Sheriff - Sub-series",
        "CloudView Perf Sheriff",
        "Cronet Perf Sheriff",
        "Jochen",
        "Mojo Perf Sheriff",
        "NaCl Perf Sheriff",
        "Network Service Sheriff",
        "OWP Storage Perf Sheriff",
        "Oilpan Perf Sheriff",
        "Pica Sheriff",
        "Power Perf Sheriff",
        "Service Worker Perf Sheriff",
        "Tracing Perftests Sheriff",
        "V8 Memory Perf Sheriff",
        "V8 Perf Sheriff",
        "WebView Perf Sheriff",
      ],
    },
  };

  cp.REDUCERS.set('alerts-section.selectAlert', (state, action) => {
    // TODO simplify this by storing rows separately from grouped alerts.
    let section = state.sections[action.sectionId];
    for (let rowIndex = 0; rowIndex < section.rows.length; ++rowIndex) {
      if (section.rows[rowIndex] === action.alert) {
        state = cp.assignSection(state, action.sectionId, {
          rows: cp.assignInArray(section.rows, rowIndex, {
            isSelected: !action.alert.isSelected,
            subRows: (action.alert.subRows || []).map(subRow => cp.assign(subRow, {
              isSelected: !action.alert.isSelected,
            })),
          }),
        });
        section = state.sections[action.sectionId];
        if (action.alert.isGroupExpanded && action.alert.subRows) {
          for (let i = rowIndex + 1; i < (rowIndex + action.alert.subRows.length + 1); ++i) {
            state = cp.assignSection(state, action.sectionId, {
              rows: cp.assignInArray(section.rows, i, {
                isSelected: !action.alert.isSelected,
              }),
            });
            section = state.sections[action.sectionId];
          }
        }
        break;
      }
      let found = false;
      for (let subRowIndex = 0; subRowIndex < (section.rows[rowIndex].subRows || []).length; ++subRowIndex) {
        if (section.rows[rowIndex] === action.alert) {
          state = cp.assignSection(state, action.sectionId, {
            rows: cp.assignInArray(section.rows, rowIndex, {
              subRows: cp.assignInArray(section.rows[rowIndex].subRows, subRowIndex, {
                isSelected: !action.alert.isSelected,
              }),
            }),
          });
          section = state.sections[action.sectionId];
          found = true;
          break;
        }
      }
      if (found) break;
    }
    return cp.assignSection(state, action.sectionId, {
      anyAlertsSelected: AlertsSection.getSelectedAlerts(section.rows).length > 0,
    });
  });

  cp.REDUCERS.set('alerts-section.selectAllAlerts', (state, action) => {
    const section = state.sections[action.sectionId];
    const select = !section.anyAlertsSelected;
    return cp.assignSection(state, action.sectionId, {
      anyAlertsSelected: select,
      rows: section.rows.map(row => cp.assign(row, {
        isSelected: select,
        subRows: (row.subRows || []).map(subRow => cp.assign(subRow, {
          isSelected: select,
        })),
      })),
    });
  });

  cp.REDUCERS.set('alerts-section.receiveAlerts', (state, action) => {
    return cp.assignSection(state, action.sectionId, {
      areRowsPlaceholders: false,
      source: cp.assign(state.sections[action.sectionId].source, {
        isFocused: false,
        inputValue: 'Chromium Perf Sheriff',
      }),
      rows: action.rows,
      summary: action.summary,
    });
  });

  cp.REDUCERS.set('alerts-section.toggleGroupExpanded', (state, action) => {
    const oldRows = state.sections[action.sectionId].rows;
    const oldRow = oldRows[action.rowIndex];

    const newRow = cp.assign(oldRow, {
      isGroupExpanded: !oldRow.isGroupExpanded,
    });

    let newRows = oldRows.slice(0, action.rowIndex);
    newRows.push(newRow);

    if (newRow.isGroupExpanded) {
      newRows = newRows.concat(newRow.subRows);
      newRows = newRows.concat(oldRows.slice(action.rowIndex + 1));
    } else {
      newRows = newRows.concat(oldRows.slice(
        action.rowIndex + 1 + newRow.subRows.length));
    }

    return cp.assignSection(state, action.sectionId, {
      rows: newRows,
    });
  });

  /**
   * @param {Number} action.sectionId
   * @param {Boolean} action.isFocused
   */
  cp.REDUCERS.set('alerts-section.focusSource', (state, action) => {
    return cp.assignSection(state, action.sectionId, {
      source: cp.assign(state.sections[action.sectionId].source, {
        isFocused: action.isFocused,
      }),
    });
  });

  /**
   * @param {Number} action.sectionId
   * @param {String} action.inputValue
   */
  cp.REDUCERS.set('alerts-section.keydownSource', (state, action) => {
    return cp.assignSection(state, action.sectionId, {
      source: cp.assign(state.sections[action.sectionId].source, {
        inputValue: action.inputValue,
      }),
    });
  });

  /**
   * @param {Number} action.sectionId
   */
  cp.REDUCERS.set('alerts-section.clearSource', (state, action) => {
    return cp.assignSection(state, action.sectionId, {
      source: cp.assign(state.sections[action.sectionId].source, {
        inputValue: '',
        isFocused: true,
      }),
    });
  });

  cp.REDUCERS.set('alerts-section.togglePreviewing', (state, action) => {
    return cp.assignSection(state, action.sectionId, {
      isPreviewing: !state.sections[action.sectionId].isPreviewing,
    });
  });

  cp.REDUCERS.set('alerts-section.startLoadingPreview', (state, action) => {
    return cp.assignSection(state, action.sectionId, {
      isLoading: true,
    });
  });

  cp.REDUCERS.set('alerts-section.layoutPreview', (state, action) => {
    return cp.assignSection(state, action.sectionId, {
      isLoading: false,
      previewLayout: action.previewLayout,
    });
  });

  return {
    AlertsSection,
  };
});
