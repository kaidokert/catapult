/*
Copyright 2017 The Chromium Authors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be
found in the LICENSE file.
*/
'use strict';

tr.exportTo('cp.as', () => {
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
      });
    }

    async ready() {
      super.ready();
      this.dispatch(cp.updateSectionWidth(this));
    }

    any_(arr) {
      return arr && (arr.length > 0);
    }

    onMenuFocus_(e) {
      this.dispatch({
        type: 'focusAlertsMenu',
        sectionId: this.sectionId,
        isFocused: true,
      });
    }

    onMenuBlur_(e) {
      this.dispatch({
        type: 'focusAlertsMenu',
        sectionId: this.sectionId,
        isFocused: false,
      });
    }

    onMenuKeydown_(e) {
      this.dispatch({
        type: 'alertsMenuKeydown',
        sectionId: this.sectionId,
        sheriffOrBug: e.detail.value,
      });
    }

    onMenuClear_(e) {
      this.dispatch({
        type: 'alertsMenuClear',
        sectionId: this.sectionId,
      });
    }

    onMenuSelect_(e) {
      this.dispatch(loadAlerts(this.sectionId, e.detail.value));
    }

    toggleShowingImprovements_() {
      // TODO this.dispatch('toggleShowingImprovements', this.sectionId);
    }

    toggleShowingTriaged_() {
      // TODO this.dispatch('toggleShowingTriaged', this.sectionId);
    }

    toggleGroupExpanded_(event) {
      const tbody = event.path[6];
      if (tbody.tagName !== 'TBODY') throw new Error('tbody?');
      const tr = event.path[5];
      if (tr.tagName !== 'TR') throw new Error('tr?');

      this.dispatch({
        type: 'toggleAlertGroupExpanded',
        sectionId: this.sectionId,
        rowIndex: Array.from(tbody.children).indexOf(tr),
      });
    }

    closeSection_() {
      this.dispatch({
        type: 'chromeperf-app.closeSection',
        sectionId: this.sectionId,
      });
    }
  }
  customElements.define(AlertsSection.is, AlertsSection);

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

  const loadAlerts = (sectionId, sheriff) => async (dispatch, getState) => {
    dispatch(Object.assign({
      type: 'receiveAlerts',
      sectionId,
    }, DUMMY_ALERTS));
  };

  cp.REDUCERS.set('receiveAlerts', (state, action) => {
    return cp.assignSection(state, action.sectionId, {
      areRowsPlaceholders: false,
      isMenuFocused: false,
      rows: action.rows,
      summary: action.summary,
    });
  });

  cp.REDUCERS.set('toggleAlertGroupExpanded', (state, action) => {
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
  cp.REDUCERS.set('focusAlertsMenu', (state, action) => {
    return cp.assignSection(state, action.sectionId, {
      isMenuFocused: action.isFocused,
    });
  });

  /**
   * @param {Number} action.sectionId
   * @param {String} action.sheriffOrBug
   */
  cp.REDUCERS.set('alertsMenuKeydown', (state, action) => {
    return cp.assignSection(state, action.sectionId, {
      sheriffOrBug: action.sheriffOrBug,
    });
  });

  /**
   * @param {Number} action.sectionId
   */
  cp.REDUCERS.set('alertsMenuClear', (state, action) => {
    return cp.assignSection(state, action.sectionId, {
      sheriffOrBug: '',
      isMenuFocused: true,
    });
  });

  return {
  };
});
