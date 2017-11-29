/*
Copyright 2017 The Chromium Authors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be
found in the LICENSE file.
*/
'use strict';

tr.exportTo('cp.as', () => {
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

    static get actions() { return cp.as.ACTIONS; }

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
      });
    }

    async ready() {
      super.ready();
      this.scrollIntoView(true);
      this.dispatch(cp.ChromeperfApp.updateSectionWidth(this));
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
        this.dispatch({
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
        this.dispatch({
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
          sectionId: sectionId,
          rowIndex: getState().sections[sectionId].rows.indexOf(alertRow),
        });
      };
    }

    closeSection_() {
      this.dispatch(cp.ChromeperfApp.closeSection(this.sectionId));
    }

    fileNewBug_() {
      // TODO
    }

    fileExistingBug_() {
      // TODO
    }

    ignore_() {
      // TODO
    }

    reportInvalid_() {
      // TODO
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

  return {
    AlertsSection,
  };
});
