/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class RecommendedOptions extends cp.ElementBase {
  }

  RecommendedOptions.State = {
    ...cp.OptionGroup.RootState,
    ...cp.OptionGroup.State,
    recommended: options => options.recommended || {},
  };

  RecommendedOptions.buildState = options => cp.buildState(
      RecommendedOptions.State, options);

  RecommendedOptions.properties = {
    ...cp.buildProperties('state', RecommendedOptions.State),
  };

  cp.ElementBase.register(RecommendedOptions);
  return {RecommendedOptions};
});
