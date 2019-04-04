/* Copyright 2019 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class AlertDetail extends cp.ElementBase {
  }

  AlertDetail.State = {
    bugId: options => 0,
  };
  AlertDetail.properties = cp.buildProperties('state', AlertDetail.State);
  AlertDetail.buildState = options => cp.buildState(AlertDetail.State, options);

  AlertDetail.actions = {
  };

  AlertDetail.reducers = {
  };

  cp.ElementBase.register(AlertDetail);
  return {AlertDetail};
});
