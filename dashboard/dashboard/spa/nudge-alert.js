/* Copyright 2019 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import './cp-loading.js';
import './error-set.js';
import '@polymer/polymer/lib/elements/dom-repeat.js';
import ElementBase from './element-base.js';
import {LEVEL_OF_DETAIL, TimeseriesRequest} from './timeseries-request.js';
import {UPDATE} from './simple-redux.js';
import {get} from '@polymer/polymer/lib/utils/path.js';
import {html} from '@polymer/polymer/polymer-element.js';
import {isElementChildOf, afterRender} from './utils.js';
import NudgeAlertRequest from './nudge-alert-request.js';

export default class NudgeAlert extends ElementBase {
  static get is() { return 'nudge-alert'; }

  static get properties() {
    return {
      statePath: String,
      isOpen: {type: Boolean, reflectToAttribute: true},
      errors: Array,
      isLoading: Boolean,
      options: Array,
      endRevision: Number,
    };
  }

  static buildState(options = {}) {
    return {
      isOpen: options.isOpen || false,
      isLoading: false,
      errors: [],

      // The alert to be nudged:
      key: options.key || '',

      // The fetchDescriptor for the alert's timeseries:
      suite: options.suite || '',
      measurement: options.measurement || '',
      bot: (options.master || '') + ':' + (options.bot || ''),
      case: options.case || '',
      statistic: options.statistic || 'avg',

      // The alert's current endRevision:
      endRevision: options.endRevision || 0,

      // The revision range of the main chart:
      minRevision: options.minRevision || 0,
      maxRevision: options.maxRevision || 0,
    };
  }

  static get template() {
    return html`
      <style>
        :host {
          background: var(--background-color, white);
          bottom: 0;
          box-shadow: var(--elevation-2);
          display: none;
          flex-direction: column;
          padding: 16px;
          position: absolute;
          right: 0;
          white-space: nowrap;
          z-index: var(--layer-menu, 100);
        }
        :host([is-open]) {
          display: flex;
        }
        #scroller {
          max-height: 200px;
          overflow: auto;
        }
        table {
          border-collapse: collapse;
        }
        tr[selected] {
          background-color: var(--neutral-color-dark, grey);
        }
        tr:not([selected]) {
          cursor: pointer;
        }
        tr:not([selected]):hover {
          background-color: var(--neutral-color-light, lightgrey);
        }
        td {
          padding: 4px;
        }
      </style>

      <error-set errors="[[errors]]"></error-set>
      <cp-loading loading$="[[isLoading]]"></cp-loading>

      <div id="scroller">
        <table>
          <template is="dom-repeat" items="[[options]]" as="option">
            <tr selected$="[[isEqual_(option.endRevision, endRevision)]]"
                on-click="onNudge_">
              <td>[[option.revision]]</td>
              <td>[[option.scalar]]</td>
            </tr>
          </template>
        </table>
      </div>
    `;
  }

  ready() {
    super.ready();
    this.addEventListener('blur', this.onBlur_.bind(this));
    this.addEventListener('keyup', this.onKeyup_.bind(this));
  }

  stateChanged(rootState) {
    const oldDescriptor = [
      this.suite,
      this.measurement,
      this.bot,
      this.case,
      this.statistic,
      this.minRevision,
      this.maxRevision,
    ].join('/');
    const oldIsOpen = this.isOpen;
    const oldIsLoading = this.isLoading;

    super.stateChanged(rootState);

    const newDescriptor = [
      this.suite,
      this.measurement,
      this.bot,
      this.case,
      this.statistic,
      this.minRevision,
      this.maxRevision,
    ].join('/');
    if (newDescriptor !== oldDescriptor) {
      this.dispatch('load', this.statePath);
    }

    if (this.isOpen && (!oldIsOpen || (this.isLoading && !oldIsLoading))) {
      // Either this was just opened or this just finished loading while open.
      const row = this.$.scroller.querySelector('tr[selected]');
      if (row) row.scrollIntoView({block: 'center', inline: 'center'});
      this.focus();
    }
  }

  async onKeyup_(event) {
    if (event.key === 'Escape') {
      await this.dispatch('close', this.statePath);
    }
  }

  async onBlur_(event) {
    if (event.relatedTarget === this ||
        isElementChildOf(event.relatedTarget, this)) {
      return;
    }
    await this.dispatch('close', this.statePath);
  }

  async onNudge_(event) {
    await this.dispatch('nudge', this.statePath, event.model.TODO);
    // TODO dispatchEvent up to chart-compound to nudge the icon
  }
}

NudgeAlert.actions = {
  close: statePath => async(dispatch, getState) => {
    dispatch(UPDATE(statePath, {isOpen: false}));
  },

  load: statePath => async(dispatch, getState) => {
    let state = get(getState(), statePath);
    if (!state) return;

    const started = performance.now();
    dispatch({
      type: NudgeAlert.reducers.startLoading.name,
      statePath,
      started,
    });

    try {
      const request = new TimeseriesRequest({
        levelOfDetail: LEVEL_OF_DETAIL.XY,
        suite: state.suite,
        measurement: state.measurement,
        bot: state.bot,
        case: state.case,
        statistic: state.statistic,
        build_type: 'test',
        minRevision: state.minRevision,
        maxRevision: state.maxRevision,
      });
      for await (const timeseries of request.reader()) {
        state = get(getState(), statePath);
        if (!state || state.started !== started) return;

        dispatch({
          type: NudgeAlert.reducers.receiveData.name,
          statePath,
          timeseries,
        });
      }
    } catch (err) {
      dispatch(UPDATE(statePath, {errors: [err.message]}));
    }

    dispatch({type: NudgeAlert.reducers.doneLoading.name, statePath});
  },

  nudge: (statePath, {startRevision, endRevision}) =>
    async(dispatch, getState) => {
      const state = get(getState(), statePath);
      if (!state) return;

      try {
        const request = new NudgeAlertRequest({
          key: state.key, startRevision, endRevision,
        });
        await request.response;
        dispatch(UPDATE(statePath, {endRevision}));
      } catch (err) {
        dispatch(UPDATE(statePath, {errors: [err.message]}));
      }
    },
};

NudgeAlert.reducers = {
  startLoading: (state, {started}, rootState) => {
    return {...state, isLoading: true, started};
  },

  receiveData: (state, {timeseries}, rootState) => {
    const options = [];
    let startRevision = timeseries.shift().revision + 1;
    for (const datum of timeseries) {
      let scalar = datum[state.statistic];
      if (typeof(scalar) === 'number' && !isNaN(scalar)) {
        scalar = datum.unit.format(scalar);
      }
      const revisions = (datum.revision === startRevision) ? datum.revision :
        `${startRevision} - ${datum.revision}`;
      options.push({
        startRevision, endRevision: datum.revision,
        revisions, scalar,
      });
      startRevision = datum.revision + 1;
    }
    return {...state, options};
  },

  doneLoading: (state, action, rootState) => {
    return {...state, isLoading: false};
  },
};

ElementBase.register(NudgeAlert);
