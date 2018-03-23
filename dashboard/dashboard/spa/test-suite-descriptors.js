/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class DescribeRequest extends cp.RequestBase {
    constructor(options) {
      super(options);
      this.testSuite_ = options.testSuite;
    }

    get url_() {
      return `/api/describe/${this.testSuite_}`;
    }

    async localhostResponse_() {
      return {
        bots: [
          'master:bot0',
          'master:bot1',
          'master:bot2',
        ],
        measurements: [
          'memory:a_size',
          'memory:b_size',
          'memory:c_size',
          'cpu:a',
          'cpu:b',
          'cpu:c',
          'power',
          'loading',
          'startup',
        ],
        testCases: [
          'browse:media:facebook_photos',
          'browse:media:imgur',
          'browse:media:youtube',
          'browse:news:flipboard',
          'browse:news:hackernews',
          'browse:news:nytimes',
          'browse:social:facebook',
          'browse:social:twitter',
          'load:chrome:blank',
          'load:games:bubbles',
          'load:games:lazors',
          'load:games:spychase',
          'load:media:google_images',
          'load:media:imgur',
          'load:media:youtube',
          'search:portal:google',
        ],
      };
    }

    postProcess_(json) {
      if (json.unparsed) {
        // eslint-disable-next-line no-console
        console.log(descriptor.unparsed);
        return undefined;
      }
      return json;
    }
  }

  class TestSuiteDescriptorCache extends cp.CacheBase {
    get cacheStatePath_() {
      return 'testSuiteDescriptors';
    }

    async computeCacheKey_() {
      return this.options_.testSuite.replace(/\./g, '_');
    }

    get isInCache_() {
      return this.rootState_.testSuiteDescriptors[this.cacheKey_] !== undefined;
    }

    async readFromCache_() {
      // The cache entry may be a promise: see onStartRequest_().
      return await this.rootState_.testSuiteDescriptors[this.cacheKey_];
    }

    createRequest_() {
      return new DescribeRequest({
        headers: this.rootState_.authHeaders,
        testSuite: this.options_.testSuite,
      });
    }

    onStartRequest_(promise) {
      this.dispatch_(cp.ElementBase.actions.updateObject(
          'testSuiteDescriptors', {[this.cacheKey_]: promise}));
    }

    onFinishRequest_(result) {
      this.dispatch_(cp.ElementBase.actions.updateObject(
          'testSuiteDescriptors', {[this.cacheKey_]: result}));
    }
  }

  function mergeDescriptor(merged, descriptor) {
    for (const bot of descriptor.bots) merged.bots.add(bot);
    for (const measurement of descriptor.measurements) {
      merged.measurements.add(measurement);
    }
    for (const testCase of descriptor.testCases) {
      merged.testCases.add(testCase);
    }
  }

  const ReadTestSuiteDescriptors = options =>
    async function* (dispatch, getState) {
      const promises = options.testSuites.map(testSuite =>
        new TestSuiteDescriptorCache({testSuite}, dispatch, getState).read());
      const mergedDescriptor = {
        measurements: new Set(),
        bots: new Set(),
        testCases: new Set(),
        testCaseTags: new Set(),
      };
      const batches = cp.RequestBase.batchResponses(
          promises, options.getDelayPromise);
      for await (const {results} of batches) {
        for (const descriptor of results) {
          if (!descriptor) continue;
          mergeDescriptor(mergedDescriptor, descriptor);
        }
        yield mergedDescriptor;
      }
    };

  return {
    ReadTestSuiteDescriptors,
  };
});
