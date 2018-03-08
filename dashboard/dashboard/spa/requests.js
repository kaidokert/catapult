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
        return this.postProcess_(this.localhostResponse_);
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

    get localhostResponse_() {
      return {};
    }

    postProcess_(json) {
      return json;
    }
  }

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

    get localhostResponse_() {
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

    get localhostResponse_() {
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
      return '/api/test_suites';
    }

    get localhostResponse_() {
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

    get localhostResponse_() {
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

    get localhostResponse_() {
      let units = 'unitlessNumber';
      if (this.measurement_.startsWith('memory:')) {
        units = 'sizeInBytes';
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

  class SessionIdRequest extends RequestBase {
    constructor(options) {
      super(options);
      this.method_ = 'POST';
      this.headers_.set('Content-type', 'application/x-www-form-urlencoded');
      this.sessionState_ = JSON.stringify(options.sessionState);
      this.body_ = 'page_state=' + encodeURIComponent(this.sessionState_);
    }

    get localhostResponse_() {
      return {sid: tr.b.ColorScheme.getStringHash(this.sessionState_)};
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
      return '/api/report_names';
    }

    get localhostResponse_() {
      return [
        'ChromiumPerfPublicReport',
        'MonochromePublic.apk Milestone resource_sizes Report',
        'MonochromePublic.apk_resource_sizes',
      ];
    }
  }

  class ReportRequest extends RequestBase {
    constructor(options) {
      super(options);
      this.source_ = options.source;
      this.milestone_ = options.milestone;
    }

    get url_() {
      return `/api/report/${this.source_}/${this.milestone_}`;
    }

    get localhostResponse_() {
      return {
        milestone: 64,
        isPreviousMilestone: true,
        isNextMilestone: false,
        anyAlerts: true,
        tables: [
          {
            name: 'ChromiumPerfPublicReport',
            isOwner: true,
            isEditing: false,
            currentVersion: '517411-73a',
            referenceVersion: '508578-c23',
            rows: [
              {
                isFirstInCategory: true,
                rowCount: 4,
                category: 'Foreground',
                href: '#',
                name: 'Java Heap',
                currentValue: 2,
                unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
                referenceValue: 1,
                percentDeltaValue: 1,
                percentDeltaUnit:
                  tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
                deltaValue: 1,
                deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
              },
              {
                isFirstInCategory: false,
                href: '#',
                name: 'Native Heap',
                currentValue: 2,
                unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
                referenceValue: 1,
                percentDeltaValue: 1,
                percentDeltaUnit:
                  tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
                deltaValue: 1,
                deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
              },
              {
                isFirstInCategory: false,
                href: '#',
                name: 'Ashmem',
                currentValue: 2,
                unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
                referenceValue: 1,
                percentDeltaValue: 1,
                percentDeltaUnit:
                  tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
                deltaValue: 1,
                deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
              },
              {
                isFirstInCategory: false,
                href: '#',
                name: 'Overall PSS',
                currentValue: 2,
                unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
                referenceValue: 1,
                percentDeltaValue: 1,
                percentDeltaUnit:
                  tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
                deltaValue: 1,
                deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
              },
              {
                isFirstInCategory: true,
                rowCount: 4,
                category: 'Background',
                href: '#',
                name: 'Java Heap',
                currentValue: 2,
                unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
                referenceValue: 1,
                percentDeltaValue: 1,
                percentDeltaUnit:
                  tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
                deltaValue: 1,
                deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
              },
              {
                isFirstInCategory: false,
                href: '#',
                name: 'Native Heap',
                currentValue: 2,
                unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
                referenceValue: 1,
                percentDeltaValue: 1,
                percentDeltaUnit:
                  tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
                deltaValue: 1,
                deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
              },
              {
                isFirstInCategory: false,
                href: '#',
                name: 'Ashmem',
                currentValue: 2,
                unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
                referenceValue: 1,
                percentDeltaValue: 1,
                percentDeltaUnit:
                  tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
                deltaValue: 1,
                deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
              },
              {
                isFirstInCategory: false,
                href: '#',
                name: 'Overall PSS',
                currentValue: 2,
                unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
                referenceValue: 1,
                percentDeltaValue: 1,
                percentDeltaUnit:
                  tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
                deltaValue: 1,
                deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
              },
            ],
          },
        ],
      };
    }
  }

  return {
    AlertsRequest,
    DescribeRequest,
    ExistingBugRequest,
    NewBugRequest,
    ReportNamesRequest,
    ReportRequest,
    RequestBase,
    SessionIdRequest,
    SessionStateRequest,
    TestSuitesRequest,
    TimeseriesRequest,
  };
});
