/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class ColumnHead extends cp.Element {
    static get is() { return 'column-head'; }

    static get properties() {
      return {
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
    }
  }
  customElements.define(ColumnHead.is, ColumnHead);

  return {
    ColumnHead,
  };
});
