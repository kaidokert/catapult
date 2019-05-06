/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import './cp-input.js';
import './cp-radio-group.js';
import './cp-radio.js';
import './raised-button.js';
import ElementBase from './element-base.js';
import NewPinpointRequest from './new-pinpoint-request.js';
import {UPDATE} from './simple-redux.js';
import {html} from '@polymer/polymer/polymer-element.js';

import {
  buildProperties,
  buildState,
  isElementChildOf,
  setImmutable,
} from './utils.js';

export default class BisectDialog extends ElementBase {
  static get is() { return 'bisect-dialog'; }

  static get template() {
    return html`
      <style>
        :host {
          background: var(--background-color);
          box-shadow: var(--elevation-2);
          display: none;
          flex-direction: column;
          min-width: 500px;
          outline: none;
          padding: 16px;
          position: absolute;
          right: 0;
          z-index: var(--layer-menu);
        }
        :host([is-open]) {
          display: flex;
        }
        *:not(:nth-child(2)) {
          margin-top: 12px;
        }
      </style>

      <table>
        <tr>
          <td>Suite</td>
          <td>[[suite]]</td>
        </tr>
        <tr>
          <td>Bot</td>
          <td>[[bot]]</td>
        </tr>
        <tr>
          <td>Measurement</td>
          <td>[[measurement]]</td>
        </tr>
        <tr>
          <td>Case</td>
          <td>[[testCase]]</td>
        </tr>
        <tr>
          <td>Statistic</td>
          <td>[[statistic]]</td>
        </tr>
      </table>

      <cp-input
          label="Bug ID"
          tabindex="0"
          value="[[bugId]]"
          on-change="onBugId_">
      </cp-input>

      <cp-input
          label="Patch"
          tabindex="0"
          value="[[patch]]"
          on-change="onPatch_">
      </cp-input>

      <cp-radio-group
          selected="[[mode]]"
          on-selected-changed="onModeChange_">
        <cp-radio name="PERFORMANCE">
          Performance
        </cp-radio>
        <cp-radio name="FUNCTIONAL">
          Functional
        </cp-radio>
      </cp-radio-group>

      <raised-button on-click="onSubmit_" tabindex="0">
        Bisect
      </raised-button>
    `;
  }

  async onBugId_() {
    this.dispatch(UPDATE(this.statePath, {bugId: event.detail.value}));
  }

  async onModeChange_(event) {
    this.dispatch(UPDATE(this.statePath, {mode: event.detail.value}));
  }

  async onPatch_(event) {
    this.dispatch(UPDATE(this.statePath, {patch: event.detail.value}));
  }

  async onSubmit_(event) {
    this.dispatch(UPDATE(this.statePath, {isOpen: false}));
    const request = new NewPinpointRequest({
      suite: this.suite,
      bot: this.bot,
      measurement: this.measurement,
      test_case: this.testCase,
      statistic: this.statistic,
      mode: this.mode,
      bug: this.bugId,
      patch: this.patch,
      start_revision: this.startRevision,
      end_revision: this.endRevision,
    });
    try {
      const response = await request.response;
    } catch (err) {
      // TODO
    }
  }
}

BisectDialog.MODE = {
  PERFORMANCE: 'PERFORMANCE',
  FUNCTIONAL: 'FUNCTIONAL',
};

BisectDialog.State = {
  isOpen: {
    value: options => false,
    reflectToAttribute: true,
  },
  bugId: options => options.bugId || '',
  patch: options => options.patch || '',
  suite: options => options.suite || '',
  measurement: options => options.measurement || '',
  bot: options => options.bot || '',
  testCase: options => options.testCase || '',
  statistic: options => options.statistic || '',
  mode: options => options.mode || BisectDialog.MODE.PERFORMANCE,
  startRevision: options => options.startRevision || 0,
  endRevision: options => options.endRevision || 0,
};

BisectDialog.properties = buildProperties(
    'state', BisectDialog.State);
BisectDialog.buildState = options => buildState(
    BisectDialog.State, options);

ElementBase.register(BisectDialog);
