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
        sheriffOrBug: {type: String},
        isMenuFocused: {type: Boolean},
        summary: {type: String},
        sheriffList: {type: Array},
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

    onMenuFocus_(e) {
      this.dispatch(AlertsSection.focusMenu(this.sectionId, true));
    }

    onMenuBlur_(e) {
      this.dispatch(AlertsSection.focusMenu(this.sectionId, false));
    }

    static focusMenu(sectionId, isFocused) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'alerts-section.focusMenu',
          sectionId,
          isFocused,
        });
      };
    }

    onMenuKeydown_(e) {
      this.dispatch(AlertsSection.keydownMenu(this.sectionId, e.detail.value));
    }

    static keydownMenu(sectionId, sheriffOrBug) {
      return async (dispatch, getState) => {
        this.dispatch({
          type: 'alerts-section.keydownMenu',
          sectionId,
          sheriffOrBug,
        });
      };
    }

    onMenuClear_(e) {
      this.dispatch(AlertsSection.clearMenu(this.sectionId));
    }

    static clearMenu(sectionId) {
      return async (dispatch, getState) => {
        this.dispatch({
          type: 'alerts-section.clearMenu',
          sectionId,
        });
      };
    }

    onMenuSelect_(e) {
      this.dispatch(AlertsSection.selectMenu(this.sectionId, e.detail.value));
    }

    static selectMenu(sectionId, sheriff) {
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
  }
  customElements.define(AlertsSection.is, AlertsSection);

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
      isMenuFocused: false,
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
  cp.REDUCERS.set('alerts-section.focusMenu', (state, action) => {
    return cp.assignSection(state, action.sectionId, {
      isMenuFocused: action.isFocused,
    });
  });

  /**
   * @param {Number} action.sectionId
   * @param {String} action.sheriffOrBug
   */
  cp.REDUCERS.set('alerts-section.keydownMenu', (state, action) => {
    return cp.assignSection(state, action.sectionId, {
      sheriffOrBug: action.sheriffOrBug,
    });
  });

  /**
   * @param {Number} action.sectionId
   */
  cp.REDUCERS.set('alerts-section.clearMenu', (state, action) => {
    return cp.assignSection(state, action.sectionId, {
      sheriffOrBug: '',
      isMenuFocused: true,
    });
  });

  return {
    AlertsSection,
  };
});
