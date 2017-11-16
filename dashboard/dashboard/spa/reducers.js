/*
Copyright 2017 The Chromium Authors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be
found in the LICENSE file.
*/
'use strict';

(function() {
  // Reducers MUST NOT have side effects.
  // Reducers MUST NOT modify state.
  // Reducers MUST return a new object.
  // Reducers MAY copy properties from state.

  function assign(obj, delta) {
    return Object.assign({}, obj, delta);
  }

  function assignInArray(arr, index, delta) {
    return arr.slice(0, index).concat([
      assign(arr[index], delta),
    ]).concat(arr.slice(index + 1));
  }

  const REDUCERS = (state, action) => {
    if (state === undefined) return DEFAULT_STATE;
    if (!REDUCERS[action.type]) return state;
    return REDUCERS[action.type](state, action);
  };

  REDUCERS.appendSection = (state, action) => {
    return assign(state, {
      sections: state.sections.concat([
        assign(action.section),
      ]),
    });
  };

  REDUCERS.closeSection = (state, action) => {
    return assign(state, {
      sections: state.sections.slice(0, action.sectionId).concat(
        state.sections.slice(action.sectionId + 1)),
    });
  };

  REDUCERS.receiveAlerts = (state, action) => {
    return assign(state, {
      sections: assignInArray(state.sections, action.sectionId, {
        summary: action.summary,
        rows: action.rows,
      }),
    });
  };

  REDUCERS.toggleAlertGroupExpanded = (state, action) => {
    const oldRows = state.sections[action.sectionId].rows;
    const oldRow = oldRows[action.rowIndex];

    const newRow = assign(oldRow, {
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

    return assign(state, {
      sections: assignInArray(state.sections, action.sectionId, {
        rows: newRows,
      }),
    });
  };

  window.REDUCERS = REDUCERS;
})();
