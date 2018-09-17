/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class ColumnHead extends Polymer.Element {
    static get is() { return 'column-head'; }

    isIconHidden_(name, sortColumn) {
      return name !== sortColumn;
    }

    getIcon_(name, sortColumn, sortDescending) {
      return ColumnHead.getIcon(name, sortColumn, sortDescending);
    }
  }

  ColumnHead.getIcon = (name, sortColumn, sortDescending) => {
    if (name !== sortColumn) return '';
    return sortDescending ? 'cp:arrow-downward' : 'cp:arrow-upward';
  };

  ColumnHead.properties = {
    name: {
      type: String,
      value: '',
    },
    sortColumn: {
      type: String,
      value: '',
    },
    sortDescending: {
      type: Boolean,
      value: false,
    },
  };

  customElements.define(ColumnHead.is, ColumnHead);

  return {ColumnHead};
});
