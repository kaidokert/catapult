/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class ChartPlaceholder extends cp.ElementBase {
    static get is() { return 'chart-placeholder'; }
  }

  ChartPlaceholder.reducers = {};

  cp.ElementBase.register(ChartPlaceholder);

  return {
    ChartPlaceholder,
  };
});
