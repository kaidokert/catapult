/* Copyright 2019 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import './cp-loading.js';
import './error-set.js';
import '@polymer/polymer/lib/elements/dom-if.js';
import ElementBase from './element-base.js';
import ExistingBugRequest from './existing-bug-request.js';
import NewBugRequest from './new-bug-request.js';
import TriageExisting from './triage-existing.js';
import TriageNew from './triage-new.js';
import {TOGGLE, UPDATE} from './simple-redux.js';
import {get} from '@polymer/polymer/lib/utils/path.js';
import {html} from '@polymer/polymer/polymer-element.js';

import {
  buildProperties,
  buildState,
  crbug,
} from './utils.js';

export default class AlertDetail extends ElementBase {
  static get is() { return 'alert-detail'; }

  static get template() {
    return html`
      <style>
        table {
          margin-left: auto;
        }
        #triage {
          display: flex;
        }
        cp-input {
          margin-top: 12px;
          width: 100px;
        }
        #start-revision {
          margin-right: 8px;
        }
      </style>

      <table>
        <tr>
          <td>&#916;[[statistic]]</td>
          <td>
            <scalar-span
                value="[[deltaValue]]"
                unit="[[deltaUnit]]">
            </scalar-span>
          </td>
        </tr>
        <tr>
          <td>%&#916;[[statistic]]</td>
          <td>
            <scalar-span
                value="[[percentDeltaValue]]"
                unit="[[percentDeltaUnit]]"
                maximum-fraction-digits="1">
            </scalar-span>
          </td>
        </tr>
      </table>

      <error-set errors="[[errors]]"></error-set>
      <cp-loading loading$="[[isLoading]]"></cp-loading>

      <template is="dom-if" if="[[bugId]]">
        <template is="dom-if" if="[[isValidBugId_(bugId)]]">
          <a href="[[crbug_(bugId)]]" target="_blank">[[bugId]]</a>
        </template>

        <template is="dom-if" if="[[isInvalidBugId_(bugId)]]">
          Ignored
        </template>

        <raised-button on-click="onUnassign_">
          Unassign
        </raised-button>
      </template>

      <template is="dom-if" if="[[!bugId]]">
        <div id="triage">
          <span style="position: relative;">
            <raised-button id="new" on-click="onTriageNew_">
              New Bug
            </raised-button>
            <triage-new
                tabindex="0"
                state-path="[[statePath]].newBug"
                on-submit="onTriageNewSubmit_">
            </triage-new>
          </span>

          <span style="position: relative;">
            <raised-button id="existing" on-click="onTriageExisting_">
              Existing Bug
            </raised-button>

            <triage-existing
                tabindex="0"
                state-path="[[statePath]].existingBug"
                on-submit="onTriageExistingSubmit_">
            </triage-existing>
          </span>

          <raised-button id="ignore" on-click="onIgnore_">
            Ignore
          </raised-button>
        </div>
      </template>

      <div>
        Revision range: [[startRevision]]-[[endRevision]]
      </div>

      <template is="dom-if" if="[[!isEmpty_(pinpointJobs)]]">
        Pinpoint jobs:
      </tempalte>
      <template is="dom-repeat" items="[[pinpointJobs]]" as="jobId">
        <a target="_blank" href="[[pinpoint_(jobId)]]">[[jobId]]</a>
      </template>

      <!-- TODO bugComponents, bugLabels -->
    `;
  }

  pinpoint_(jobId) {
    return 'https://pinpoint-dot-chromeperf.appspot.com/job/' + jobId;
  }

  isValidBugId_(bugId) {
    return bugId > 0;
  }

  isInvalidBugId_(bugId) {
    return bugId < 0;
  }

  crbug_(bugId) {
    return crbug(bugId);
  }

  async onTriageNew_() {
    this.dispatch({
      type: AlertDetail.reducers.triageNew.name,
      statePath: this.statePath,
    });
  }

  async onTriageExisting_() {
    this.dispatch({
      type: AlertDetail.reducers.triageExisting.name,
      statePath: this.statePath,
    });
  }

  async onTriageNewSubmit_() {
    await this.dispatch('submitNewBug', this.statePath);
  }

  async onUnassign_() {
    await this.dispatch('changeBugId', this.statePath, 0);
  }

  async onTriageExistingSubmit_() {
    this.dispatch(UPDATE(this.statePath + '.existingBug', {isOpen: false}));
    await this.dispatch('changeBugId', this.statePath, this.existingBug.bugId);
  }

  async onIgnore_() {
    await this.dispatch('changeBugId', this.statePath, -2);
  }
}

AlertDetail.State = {
  bugId: options => 0,
  deltaUnit: options => undefined,
  deltaValue: options => 0,
  endRevision: options => 0,
  key: options => '',
  percentDeltaUnit: options => undefined,
  percentDeltaValue: options => 0,
  startRevision: options => 0,
  statistic: options => '',
  pinpointJobs: options => [],

  isLoading: options => false,
  errors: options => [],
  newBug: options => TriageNew.buildState({}),
  existingBug: options => TriageExisting.buildState({}),
};
AlertDetail.properties = buildProperties('state', AlertDetail.State);
AlertDetail.buildState = options => buildState(AlertDetail.State, options);

AlertDetail.actions = {
  changeBugId: (statePath, bugId) => async(dispatch, getState) => {
    // Assume success.
    dispatch(UPDATE(statePath, {bugId, isLoading: true}));
    const alertKeys = [get(getState(), statePath).key];
    try {
      const request = new ExistingBugRequest({alertKeys, bugId});
      await request.response;
    } catch (err) {
      dispatch(UPDATE(statePath, {errors: [err.message]}));
    }
    dispatch(UPDATE(statePath, {isLoading: false}));
  },

  submitNewBug: statePath => async(dispatch, getState) => {
    dispatch(UPDATE(statePath, {
      bugId: '[creating]',
      newBug: TriageNew.buildState({}),
    }));

    const state = get(getState(), statePath);
    try {
      const request = new NewBugRequest({
        alertKeys: [state.key],
        ...state.newBug,
        labels: state.newBug.labels.filter(
            x => x.isEnabled).map(x => x.name),
        components: state.newBug.components.filter(
            x => x.isEnabled).map(x => x.name),
      });
      const bugId = await request.response;
      dispatch(UPDATE(statePath, {bugId}));
      // TODO storeRecentlyModifiedBugs
    } catch (err) {
      dispatch(UPDATE(statePath, {errors: [err.message]}));
    }
    dispatch(UPDATE(statePath, {isLoading: false}));
  },
};

AlertDetail.reducers = {
  triageNew: (state, action, rootState) => {
    const newBug = TriageNew.buildState({
      isOpen: true,
      alerts: [state],
      cc: rootState.userEmail,
    });
    return {...state, newBug};
  },

  triageExisting: (state, action, rootState) => {
    const existingBug = TriageExisting.buildState({
      isOpen: true,
      alerts: [state],
    });
    return {...state, existingBug};
  },
};

ElementBase.register(AlertDetail);
