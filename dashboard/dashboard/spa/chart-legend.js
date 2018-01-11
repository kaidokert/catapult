/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class ChartLegend extends Polymer.GestureEventListeners(cp.ElementBase) {
    static get is() { return 'chart-legend'; }

    static get properties() {
      return {
        items: {
          type: Array,
        },
      };
    }

    onLeafMouseOver_(event) {
      this.dispatchEvent(new CustomEvent('leaf-mouseover', {
        bubbles: true,
        composed: true,
        detail: event.model.item,
      }));
    }

    onLeafMouseOut_(event) {
      this.dispatchEvent(new CustomEvent('leaf-mouseout', {
        bubbles: true,
        composed: true,
        detail: event.model.item,
      }));
    }
  }

  ChartLegend.reducers = {};

  cp.ElementBase.register(ChartLegend);

  return {
    ChartLegend,
  };
});
