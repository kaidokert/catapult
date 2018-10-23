/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class ChartPlaceholder extends Polymer.Element {
    static get is() { return 'cp-input'; }
  }

  customElements.define(ChartPlaceholder.is, ChartPlaceholder);
  return {ChartPlaceholder};
});
