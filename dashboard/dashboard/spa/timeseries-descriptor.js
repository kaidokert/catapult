/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class TimeseriesDescriptor extends cp.ElementBase {
  }

  TimeseriesDescriptor.State = {
  };

  TimeseriesDescriptor.buildState = options => cp.buildState(
      TimeseriesDescriptor.State, options);

  TimeseriesDescriptor.properties = {
    ...cp.buildProperties('state', TimeseriesDescriptor.State),
  };

  TimeseriesDescriptor.actions = {
  };

  TimeseriesDescriptor.reducers = {
  };

  cp.ElementBase.register(TimeseriesDescriptor);
  return {TimeseriesDescriptor};
});
