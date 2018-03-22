/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class RequestBase {
    constructor(options) {
      this.promise_ = undefined;

      this.method_ = 'GET';
      this.headers_ = new Headers(options.headers);
      this.body_ = undefined;

      this.abortController_ = options.abortController;
      if (!this.abortController_ && window.AbortController) {
        this.abortController_ = new window.AbortController();
      }
      this.signal_ = undefined;
      if (this.abortController_) {
        this.signal_ = this.abortController_.signal;
      }
    }

    get response() {
      // Don't call fetch_ before the subclass constructor finishes.
      if (!this.promise_) this.promise_ = this.fetch_();
      return this.promise_;
    }

    async fetch_() {
      if (location.hostname === 'localhost') {
        await cp.ElementBase.timeout(1000);
        return this.postProcess_(await this.localhostResponse_());
      }

      const mark = tr.b.Timing.mark('fetch', this.constructor.name);
      const response = await fetch(this.url_, {
        body: this.body_,
        headers: this.headers_,
        method: this.method_,
        signal: this.signal_,
      });
      mark.end();
      return this.postProcess_(await response.json());
    }

    abort() {
      if (!this.abortController_) return;
      this.abortController_.abort();
    }

    get url_() {
      throw new Error('not implemented');
    }

    async localhostResponse_() {
      return {};
    }

    postProcess_(json) {
      return json;
    }
  }

  function selfAwarePromise(narcissus) {
    const socrates = (async() => {
      try {
        return await narcissus;
      } finally {
        socrates.isResolved = true;
      }
    })();
    socrates.isResolved = false;
    return socrates;
  }

  /* Processing results can be costly. Help callers batch process
   * results by waiting a bit to see if more promises resolve.
   * This is similar to Polymer.Debouncer, but as an async generator.
   * Usage:
   * async function fetchThings(things) {
   *   const responses = things.map(thing => new ThingRequest(thing).response);
   *   const mergedResult = {};
   *   for await (const {results, errors} of
   *              cp.RequestBase.batchResponses(responses)) {
   *     dispatch({
   *       type: ...mergeAndDisplayThings.typeName,
   *       results, errors,
   *     });
   *   }
   *   dispatch({
   *     type: ...doneReceivingThings.typeName,
   *   });
   * }
   *
   * |promises| can be any promise, need not be RequestBase.response.
   */
  RequestBase.batchResponses = async function* (promises, opt_getDelayPromise) {
    const getDelayPromise = opt_getDelayPromise || (() =>
      cp.ElementBase.timeout(500));
    promises = promises.map(selfAwarePromise);
    let results = [];
    let errors = [];
    while (promises.length) {
      let result;
      try {
        result = await Promise.race(promises);
      } catch (err) {
        errors.push(err);
      }

      // Remove the delay even if it hasn't fired yet.
      promises = promises.filter(p => !p.isResolved && !p.isBatchDelay);

      if (result === RequestBase.batchResponses.DELAY_NONCE) {
        // The delay resolved.
        yield {results, errors};
        results = [];
        errors = [];
      } else {
        results.push(result);
        if (promises.length > 0) {
          const delay = (async() => {
            await getDelayPromise();
            return RequestBase.batchResponses.DELAY_NONCE;
          })();
          // It doesn't matter if the delay is self aware because timeouts and
          // resolved promises are treated the same in the filter above.
          delay.isBatchDelay = true;
          promises.push(delay);
        }
      }
    }
    yield {results, errors};
  };

  RequestBase.batchResponses.DELAY_NONCE = Object.freeze({});

  class NewBugRequest extends RequestBase {
    constructor(options) {
      super(options);
      this.method_ = 'POST';
      this.body_ = new FormData();
      for (const key of options.alertKeys) this.body_.append('key', key);
      for (const label of options.labels) this.body_.append('label', label);
      for (const component of options.components) {
        this.body_.append('component', component);
      }
      this.body_.set('summary', options.summary);
      this.body_.set('description', options.description);
      this.body_.set('owner', options.owner);
      this.body_.set('cc', options.cc);
    }

    get url_() {
      return '/api/alerts/new_bug';
    }

    async localhostResponse_() {
      return {bug_id: 123450000 + tr.b.GUID.allocateSimple()};
    }

    postProcess_(json) {
      return json.bug_id;
    }
  }

  class ExistingBugRequest extends RequestBase {
    constructor(options) {
      super(options);
      this.method_ = 'POST';
      this.body_ = new FormData();
      for (const key of options.alertKeys) this.body_.append('key', key);
      this.body_.set('bug_id', options.bugId);
    }

    get url_() {
      return '/api/alerts/existing_bug';
    }
  }

  class AlertsRequest extends RequestBase {
    constructor(options) {
      super(options);
      this.headers_.set('Content-type', 'application/x-www-form-urlencoded');
      this.method_ = 'POST';
      this.body_ = new URLSearchParams();
      for (const [key, value] of Object.entries(options.body)) {
        if (value === undefined) continue;
        this.body_.set(key, value);
      }
      this.improvements = options.body.improvements;
      this.triaged = options.body.triaged;
    }

    get url_() {
      // TODO /api/alerts
      return '/alerts';
    }

    async localhostResponse_() {
      const improvements = Boolean(this.improvements);
      const triaged = Boolean(this.triaged);
      const alerts = [];
      for (let i = 0; i < 10; ++i) {
        const revs = new tr.b.math.Range();
        revs.addValue(parseInt(1e6 * Math.random()));
        revs.addValue(parseInt(1e6 * Math.random()));
        let bugId = undefined;
        if (triaged && (Math.random() > 0.5)) {
          if (Math.random() > 0.5) {
            bugId = -1;
          } else {
            bugId = 123456;
          }
        }
        alerts.push({
          bot: 'android-nexus5',
          bug_id: bugId,
          bug_labels: [],
          bug_components: [],
          end_revision: revs.max,
          improvement: improvements && (Math.random() > 0.5),
          key: tr.b.GUID.allocateSimple(),
          master: 'ChromiumPerf',
          median_after_anomaly: 100 * Math.random(),
          median_before_anomaly: 100 * Math.random(),
          start_revision: revs.min,
          test: 'fake' + i + '/case' + parseInt(Math.random() * 10),
          testsuite: 'system_health.common_desktop',
          units: 'ms',
        });
      }
      alerts.sort((x, y) => x.start_revision - y.start_revision);
      const bugs = [
        {
          id: '12345',
          status: 'WontFix',
          owner: {name: 'owner'},
          summary: '0% regression in nothing at 1:9999999',
        },
      ];
      for (let i = 0; i < 50; ++i) {
        bugs.push({
          id: 'TODO',
          status: 'TODO',
          owner: {name: 'TODO'},
          summary: 'TODO '.repeat(30),
        });
      }
      return {
        anomaly_list: alerts,
        recent_bugs: bugs,
      };
    }

    postProcess_(json) {
      if (json.error) {
        // eslint-disable-next-line no-console
        console.error('Error fetching alerts', err);
        return {
          anomaly_list: [],
          recent_bugs: [],
        };
      }
      return json;
    }
  }

  class TestSuitesRequest extends RequestBase {
    get url_() {
      // The TestSuitesHandler doesn't use this query parameter, but it helps
      // caches (such as the browser cache) understand that it returns different
      // data depending on whether the user is authorized to access internal
      // data.
      const internal = this.headers_.has('Authorization');
      return '/api/test_suites' + (internal ? '?internal' : '');
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

  class DescribeRequest extends RequestBase {
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
  }

  class TimeseriesRequest extends RequestBase {
    constructor(options) {
      super(options);
      this.measurement_ = options.measurement;
      this.queryParams_ = new URLSearchParams();
      this.queryParams_.set('testSuite', options.testSuite);
      this.queryParams_.set('measurement', options.measurement);
      this.queryParams_.set('bot', options.bot);
      if (options.testCase) {
        this.queryParams_.set('testCase', options.testCase);
      }
      this.queryParams_.set('statistic', options.statistic);
      if (options.buildType) {
        this.queryParams_.set('buildType', options.buildType);
      }
      this.queryParams_.set('columns', options.columns.join(','));
      if (options.minRevision) {
        this.queryParams_.set('minRevision', options.minRevision);
      }
      if (options.maxRevision) {
        this.queryParams_.set('maxRevision', options.maxRevision);
      }
      if (options.minTimestamp) {
        this.queryParams_.set('minTimestamp', options.minTimestamp);
      }
      if (options.maxTimestamp) {
        this.queryParams_.set('maxTimestamp', options.maxTimestamp);
      }
    }

    get url_() {
      return `/api/timeseries2?${this.queryParams_}`;
    }

    async localhostResponse_() {
      let units = 'unitlessNumber';
      if (this.measurement_.startsWith('memory:')) {
        units = 'sizeInBytes_smallerIsBetter';
      }
      if (this.measurement_.startsWith('cpu:') ||
          this.measurement_.startsWith('loading') ||
          this.measurement_.startsWith('startup')) {
        units = 'ms_smallerIsBetter';
      }
      if (this.measurement_.startsWith('power')) {
        units = 'W_smallerIsBetter';
      }
      const timeseries = [];
      const sequenceLength = 100;
      const nowMs = new Date() - 0;
      for (let i = 0; i < sequenceLength; i += 1) {
        // r_commit_pos, timestamp, value
        timeseries.push([
          i,
          nowMs - ((sequenceLength - i - 1) * (2592105834 / 50)),
          parseInt(100 * Math.random()),
        ]);
      }
      return {timeseries, units};
    }
  }

  async function sha256(s) {
    s = new TextEncoder('utf-8').encode(s);
    const hash = await crypto.subtle.digest('SHA-256', s);
    const view = new DataView(hash);
    let hex = '';
    for (let i = 0; i < view.byteLength; i += 4) {
      hex += ('00000000' + view.getUint32(i).toString(16)).slice(-8);
    }
    return hex;
  }

  class SessionIdRequest extends RequestBase {
    constructor(options) {
      super(options);
      this.method_ = 'POST';
      this.headers_.set('Content-type', 'application/x-www-form-urlencoded');
      this.sessionStateJson_ = JSON.stringify(options.sessionState);
      this.body_ = 'page_state=' + encodeURIComponent(this.sessionStateJson_);
    }

    get sessionStateJson() {
      return this.sessionStateJson_;
    }

    async expectedResponse() {
      return await sha256(this.sessionStateJson_);
    }

    async localhostResponse_() {
      return {sid: await this.expectedResponse()};
    }

    get url_() {
      return '/short_uri';
    }

    postProcess_(json) {
      return json.sid;
    }
  }

  class SessionStateRequest extends RequestBase {
    constructor(options) {
      super(options);
      this.sessionId_ = options.sessionId;
    }

    get url_() {
      return `/short_uri?sid=${this.sessionId_}`;
    }
  }

  class ReportNamesRequest extends RequestBase {
    get url_() {
      // The ReportHandler doesn't use this query parameter, but it helps caches
      // (such as the browser cache) understand that it returns different data
      // depending on whether the user is authorized to access internal data.
      const internal = this.headers_.has('Authorization');
      return '/api/report_names' + (internal ? '?internal' : '');
    }

    async localhostResponse_() {
      return [
        {name: cp.ReportSection.DEFAULT_NAME, id: 0, modified: 0},
      ];
    }
  }

  class ReportRequest extends RequestBase {
    constructor(options) {
      super(options);
      this.id_ = options.id;
      this.name_ = options.name;
      this.modified_ = options.modified;
      this.revisions_ = options.revisions;
      this.queryParams_ = new URLSearchParams();
      this.queryParams_.set('id', this.id_);
      this.queryParams_.set('modified', this.modified_);
      this.queryParams_.set('revisions', this.revisions_);
    }

    get url_() {
      return `/api/report?${this.queryParams_}`;
    }

    async localhostResponse_() {
      const dummyStatistics = () => {
        const statistics = {};
        for (const revision of this.revisions_) {
          statistics[revision] = {
            avg: Math.random() * 1000,
            std: Math.random() * 1000,
          };
        }
        return statistics;
      };
      return {
        name: this.name_,
        owners: ['benjhayden@chromium.org', 'benjhayden@google.com'],
        url: 'https://v2spa-dot-chromeperf.appspot.com/',
        statistics: ['avg', 'std'],
        rows: [
          {
            label: 'Pixel:Memory',
            units: 'sizeInBytes_smallerIsBetter',
            testSuites: ['system_health.common_mobile'],
            measurement: 'memory:a_size',
            bots: ['master:bot0'],
            testCases: [],
            ...dummyStatistics(),
          },
          {
            label: 'Pixel:Loading',
            units: 'ms_smallerIsBetter',
            testSuites: ['system_health.common_mobile'],
            measurement: 'loading',
            bots: ['master:bot0'],
            testCases: [],
            ...dummyStatistics(),
          },
          {
            label: 'Pixel:Startup',
            units: 'ms_smallerIsBetter',
            testSuites: ['system_health.common_mobile'],
            measurement: 'startup',
            bots: ['master:bot0'],
            testCases: [],
            ...dummyStatistics(),
          },
          {
            label: 'Pixel:CPU',
            units: 'ms_smallerIsBetter',
            testSuites: ['system_health.common_mobile'],
            measurement: 'cpu:a',
            bots: ['master:bot0'],
            testCases: [],
            ...dummyStatistics(),
          },
          {
            label: 'Pixel:Power',
            units: 'W_smallerIsBetter',
            testSuites: ['system_health.common_mobile'],
            measurement: 'power',
            bots: ['master:bot0'],
            testCases: [],
            ...dummyStatistics(),
          },
          {
            label: 'Android Go:Memory',
            units: 'sizeInBytes_smallerIsBetter',
            testSuites: ['system_health.common_mobile'],
            measurement: 'memory:a_size',
            bots: ['master:bot0'],
            testCases: [],
            ...dummyStatistics(),
          },
          {
            label: 'Android Go:Loading',
            units: 'ms_smallerIsBetter',
            testSuites: ['system_health.common_mobile'],
            measurement: 'loading',
            bots: ['master:bot0'],
            testCases: [],
            ...dummyStatistics(),
          },
          {
            label: 'Android Go:Startup',
            units: 'ms_smallerIsBetter',
            testSuites: ['system_health.common_mobile'],
            measurement: 'startup',
            bots: ['master:bot0'],
            testCases: [],
            ...dummyStatistics(),
          },
          {
            label: 'Android Go:CPU',
            units: 'ms_smallerIsBetter',
            testSuites: ['system_health.common_mobile'],
            measurement: 'cpu:a',
            bots: ['master:bot0'],
            testCases: [],
            ...dummyStatistics(),
          },
          {
            label: 'Android Go:Power',
            units: 'W_smallerIsBetter',
            testSuites: ['system_health.common_mobile'],
            measurement: 'power',
            bots: ['master:bot0'],
            testCases: [],
            ...dummyStatistics(),
          },
        ],
      };
    }
  }

  class ReportTemplateRequest extends RequestBase {
    constructor(options) {
      super(options);
      this.method_ = 'POST';
      this.headers_.set('Content-type', 'application/json');
      this.body_ = JSON.stringify({
        id: options.id,
        name: options.name,
        owners: options.owners,
        url: options.url,
        template: {
          statistics: options.statistics,
          rows: options.rows,
        },
      });
    }

    get url_() {
      return `/api/report`;
    }

    async localhostResponse_() {
      return {};
    }
  }

  return {
    AlertsRequest,
    DescribeRequest,
    ExistingBugRequest,
    NewBugRequest,
    ReportNamesRequest,
    ReportRequest,
    ReportTemplateRequest,
    RequestBase,
    SessionIdRequest,
    SessionStateRequest,
    TestSuitesRequest,
    TimeseriesRequest,
  };
});
