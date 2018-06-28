/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp.config', () => {
  // When true, state is recursively frozen so that improper property setting
  // causes an error to be thrown. Freezing significantly impacts performance,
  // so set to false in order to measure performance on localhost.
  const IS_DEBUG = location.hostname === 'localhost';

  // When both IS_DEBUG and SHOULD_MOCK_DURING_DEBUG are true, the app will use
  // mock data instead of fetching from the backend.
  const SHOULD_MOCK_DURING_DEBUG = true;

  const IS_MOCKING = IS_DEBUG && SHOULD_MOCK_DURING_DEBUG;

  const PRODUCTION_ORIGIN = 'v2spa-dot-chromeperf.appspot.com';

  // When true, Redux Dev Tools will not record changes automatically, which
  // increases runtime performance of the app.
  const IS_PRODUCTION = location.hostname === PRODUCTION_ORIGIN;

  // Override BACKEND_ORIGIN to set a different URL for backend queries.
  // When set to empty string, the origin will be the same as the frontend.
  //   e.g. BACKEND_ORIGIN = "https://some-other-url.appspot.com"
  const BACKEND_ORIGIN = '';

  return {
    IS_DEBUG,
    IS_MOCKING,
    IS_PRODUCTION,
    BACKEND_ORIGIN,
  };
});
