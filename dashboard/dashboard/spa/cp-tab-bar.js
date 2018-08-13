/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class CpTabBar extends cp.ElementBase {
    async ready() {
      super.ready();
      await cp.afterRender();
      this.observeSelected_();
    }

    async observeSelected_() {
      for (const item of this.querySelectorAll('cp-tab')) {
        item.checked = (item.name === this.selected);
      }
    }
  }

  CpTabBar.properties = {
    selected: {
      type: String,
      observer: 'observeSelected_',
    },
  };

  cp.ElementBase.register(CpTabBar);

  return {
    CpTabBar,
  };
});
