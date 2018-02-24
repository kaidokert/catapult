/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class RequestBase {
    constructor(options) {
      this.method = 'GET';
      this.headers = new Headers(options.headers);
      this.body = undefined;

      this.abortController = options.abortController;
      if (!this.abortController && window.AbortController) {
        this.abortController = new window.AbortController();
      }
      this.signal = undefined;
      if (this.abortController) {
        this.signal = this.abortController.signal;
      }
    }

    abort() {
      if (!this.abortController) return;
      this.abortController.abort();
    }

    get url() {
      throw new Error('not implemented');
    }

    get localhostResponse() {
      return {};
    }

    async fetch() {
      if (location.hostname === 'localhost') {
        return this.postProcess(this.localhostResponse);
      }

      const response = await fetch(this.url, {
        method: this.method,
        headers: this.headers,
        signal: this.signal,
        body: this.body,
      });
      return this.postProcess(await response.json());
    }

    postProcess(json) {
      return json;
    }
  }

  class NewBugRequest extends RequestBase {
    constructor(options) {
      super(options.abortController);
      this.method = 'POST';
      this.headers = new Headers(options.headers);
      this.body = new FormData();
      for (const key of options.alertKeys) this.body.append('key', key);
      for (const label of options.labels) this.body.append('label', label);
      for (const component of options.components) {
        this.body.append('component', component);
      }
      this.body.set('summary', options.summary);
      this.body.set('description', options.description);
      this.body.set('owner', options.owner);
      this.body.set('cc', options.cc);
    }

    get url() {
      return '/api/alerts/new_bug';
    }

    get localhostResponse() {
      return {bug_id: 123456789};
    }

    postProcess(json) {
      return json.bug_id;
    }
  }

  class ExistingBugRequest extends RequestBase {
    constructor(options) {
      super(options.abortController);
      this.headers = new Headers(options.headers);
      this.method = 'POST';
      this.body = new FormData();
      for (const key of options.alertKeys) this.body.append('key', key);
      this.body.set('bug_id', options.bugId);
    }

    get url() {
      return '/api/alerts/existing_bug';
    }
  }

  class AlertsRequest extends RequestBase {
    constructor(options) {
      super(options.abortController);
      this.headers = new Headers(options.headers);
      this.headers.set('Content-type', 'application/x-www-form-urlencoded');
      this.method = 'POST';
      this.body = new URLSearchParams();
      // TODO this.body
    }

    get url() {
      // TODO /api/alerts
      return '/alerts';
    }

    get localhostResponse() {
      // TODO options
      return {
        anomaly_list: cp.dummyAlerts(
            Boolean(options.improvements), Boolean(options.triaged)),
        recent_bugs: cp.dummyRecentBugs(),
      };
    }

    postProcess(json) {
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

  return {
    AlertsRequest,
    ExistingBugRequest,
    NewBugRequest,
    RequestBase,
  };
});
