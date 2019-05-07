/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import './cp-input.js';
import './cp-radio-group.js';
import './cp-radio.js';
import './raised-button.js';
import '@polymer/polymer/lib/elements/dom-if.js';
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
          position: relative;
        }

        #dialog {
          background: var(--background-color, white);
          box-shadow: var(--elevation-2);
          flex-direction: column;
          outline: none;
          padding: 16px;
          position: absolute;
          bottom: 0;
          z-index: var(--layer-menu, 100);
        }
        cp-input {
          margin: 12px 4px 4px 4px;
          width: 100px;
        }
        cp-radio-group {
          margin-left: 8px;
          flex-direction: row;
        }
        .row raised-button {
          flex-grow: 1;
        }
        .row {
          display: flex;
          align-items: center;
        }
        #cancel {
          background: var(--background-color, white);
          box-shadow: none;
        }
      </style>

      <raised-button
          disabled$="[[!able]]"
          title$="[[tooltip]]"
          on-click="onOpen_">
        Bisect
      </raised-button>

      <div id="dialog" hidden$="[[!isOpen]]">
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
          <template is="dom-if" if="[[case]]">
            <tr>
              <td>Case</td>
              <td>[[case]]</td>
            </tr>
          </template>
          <template is="dom-if" if="[[statistic]]">
            <tr>
              <td>Statistic</td>
              <td>[[statistic]]</td>
            </tr>
          </template>
        </table>

        <div class="row">
          <cp-input
              label="Start Revision"
              tabindex="0"
              value="[[startRevision]]"
              on-change="onStartRevision_">
          </cp-input>

          <cp-input
              label="End Revision"
              tabindex="0"
              value="[[endRevision]]"
              on-change="onEndRevision_">
          </cp-input>
        </div>

        <div class="row">
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
        </div>

        <div class="row">
          Mode:
          <cp-radio-group
              selected="[[mode]]"
              on-selected-changed="onModeChange_">
            <cp-radio name="performance">
              Performance
            </cp-radio>
            <cp-radio name="functional">
              Functional
            </cp-radio>
          </cp-radio-group>
        </div>

        <div class="row">
          <raised-button
              id="cancel"
              on-click="onCancel_"
              tabindex="0">
            Cancel
          </raised-button>
          <raised-button
              id="start"
              on-click="onSubmit_"
              tabindex="0">
            Start
          </raised-button>
        </div>
      </div>
    `;
  }

  ready() {
    super.ready();
    this.addEventListener('blur', this.onBlur_.bind(this));
    this.addEventListener('keyup', this.onKeyup_.bind(this));
  }

  observeIsOpen_() {
    if (this.isOpen) {
      this.$.start.focus();
    }
  }

  async onKeyup_(event) {
    if (event.key === 'Escape') {
      await this.dispatch(UPDATE(this.statePath, {isOpen: false}));
    }
  }

  async onBlur_(event) {
    if (event.relatedTarget === this ||
        isElementChildOf(event.relatedTarget, this)) {
      return;
    }
    await this.dispatch(UPDATE(this.statePath, {isOpen: false}));
  }

  async onCancel_(event) {
    await this.dispatch(UPDATE(this.statePath, {isOpen: false}));
  }

  async onStartRevision_(event) {
    await this.dispatch(UPDATE(this.statePath, {
      startRevision: event.detail.value,
    }));
  }

  async onEndRevision_(event) {
    await this.dispatch(UPDATE(this.statePath, {
      endRevision: event.detail.value,
    }));
  }

  async onBugId_() {
    await this.dispatch(UPDATE(this.statePath, {bugId: event.detail.value}));
  }

  async onModeChange_(event) {
    await this.dispatch(UPDATE(this.statePath, {mode: event.detail.value}));
  }

  async onPatch_(event) {
    await this.dispatch(UPDATE(this.statePath, {patch: event.detail.value}));
  }

  async onOpen_(event) {
    await this.dispatch(UPDATE(this.statePath, {isOpen: true}));
  }

  async onSubmit_(event) {
    this.dispatch(UPDATE(this.statePath, {isOpen: false, isLoading: true}));
    const request = new NewPinpointRequest({
      alerts: JSON.stringify(this.alertKeys),
      suite: this.suite,
      bot: this.bot,
      measurement: this.measurement,
      case: this.case,
      statistic: this.statistic,
      mode: this.mode,
      bug: this.bugId,
      patch: this.patch,
      start_revision: this.startRevision,
      end_revision: this.endRevision,
    });
    try {
      const response = await request.response;
      this.dispatch(UPDATE(this.statePath, {isLoading: false, jobId}));
    } catch (err) {
      this.dispatch(UPDATE(this.statePath, {errors: [err.message]}));
    }
  }
}

BisectDialog.MODE = {
  PERFORMANCE: 'performance',
  FUNCTIONAL: 'functional',
};

BisectDialog.State = {
  alertKeys: options => options.alertKeys || [],
  able: options => options.able || true,
  tooltip: options => options.tooltip || '',
  errors: options => [],
  isOpen: options => false,
  bugId: options => options.bugId || '',
  patch: options => options.patch || '',
  suite: options => options.suite || '',
  measurement: options => options.measurement || '',
  bot: options => options.bot || '',
  case: options => options.case || '',
  statistic: options => options.statistic || '',
  mode: options => options.mode || BisectDialog.MODE.PERFORMANCE,
  startRevision: options => options.startRevision || 0,
  endRevision: options => options.endRevision || 0,
};

BisectDialog.properties = buildProperties(
    'state', BisectDialog.State);
BisectDialog.buildState = options => buildState(
    BisectDialog.State, options);

BisectDialog.observers = [
  'observeIsOpen_(isOpen)',
];

ElementBase.register(BisectDialog);
