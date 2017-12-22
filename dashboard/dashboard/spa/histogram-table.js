/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class HistogramTable extends Polymer.GestureEventListeners(cp.Element) {
    static get is() { return 'histogram-table'; }

    static get properties() {
      return cp.buildProperties('histogramTable', {
        columns: {
          type: Array,
          value: [],
        },
        rows: {
          type: Array,
          value: [],
        },
        sortColumn: {
          type: String,
        },
        sortDescending: {
          type: Boolean,
        },
        commonDiagnostics: {
          type: Array,
          value: [],
        },
      });
    }

    visibleRows_(rows) {
      return HistogramTable.visibleRows(rows, 0);
    }

    static visibleRows(groupedRows, depth) {
      const rows = [];
      for (const row of groupedRows) {
        row.depth = depth;
        rows.push(row);
        if (row.isExpanded) {
          rows.push.apply(rows, HistogramTable.visibleRows(
              row.subRows, depth + 1));
        }
      }
      return rows;
    }

    getCommonDiagnostic_(diagnosticName, columnName) {
      return HistogramTable.getCommonDiagnostic(
          diagnosticName, columnName, this.rows);
    }

    static getCommonDiagnostic(diagnosticName, columnName, rows) {
      return rows[0].columns[columnName].diagnostics.get(diagnosticName);
    }

    sort_(event) {
      // eslint-disable-next-line no-console
      console.log('TODO sort', event);
    }
  }
  cp.Element.register(HistogramTable);

  return {
    HistogramTable,
  };
});
