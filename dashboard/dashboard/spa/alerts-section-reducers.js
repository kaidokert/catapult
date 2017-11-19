/*
Copyright 2017 The Chromium Authors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be
found in the LICENSE file.
*/
'use strict';

tr.exportTo('cp', () => {
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
