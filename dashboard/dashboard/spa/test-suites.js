/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class TestSuitesRequest extends cp.RequestBase {
    get url_() {
      // The TestSuitesHandler doesn't use this query parameter, but it helps
      // the browser cache understand that it returns different data depending
      // on whether the user is authorized to access internal data.
      let internal = '';
      if (this.headers_.has('Authorization')) internal = '?internal';
      return `/api/test_suites${internal}`;
    }

    async localhostResponse_() {
      return [
        'system_health.common_desktop',
        'system_health.common_mobile',
        'system_health.memory_desktop',
        'system_health.memory_mobile',
      ];
    }

    postProcess_(json) {
      const options = cp.OptionGroup.groupValues(json);
      return {options, count: json.length};
    }
  }

  class TestSuitesCache extends cp.CacheBase {
    async computeCacheKey_() {
      let internal = '';
      if (this.rootState_.authHeaders) internal = 'Internal';
      return `testSuites${internal}`;
    }

    get isInCache_() {
      return this.rootState_[this.cacheKey_] !== undefined;
    }

    async readFromCache_() {
      // The cache entry may be a promise: see onStartRequest_().
      return await this.rootState_[this.cacheKey_];
    }

    async fetch_() {
      return await new TestSuitesRequest({
        headers: this.rootState_.authHeaders,
      }).response;
    }

    onStartRequest_(promise) {
      this.dispatch_(cp.ElementBase.actions.updateObject('', {
        [this.cacheKey_]: promise,
      }));
    }

    onFinishRequest_(result) {
      this.dispatch_(cp.ElementBase.actions.updateObject('', {
        [this.cacheKey_]: result,
      }));
    }
  }

  const ReadTestSuites = () => async(dispatch, getState) =>
    await new TestSuitesCache({}, dispatch, getState).read();

  return {
    ReadTestSuites,
  };
});
