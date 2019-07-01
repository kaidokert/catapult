/* Copyright 2019 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import '@chopsui/chops-button';
import '@chopsui/chops-checkbox';
import '@chopsui/chops-input';
import '@chopsui/chops-textarea';
import {ElementBase, STORE} from './element-base.js';
import {TOGGLE, UPDATE} from './simple-redux.js';
import {html, css} from 'lit-element';

export class EditNote extends ElementBase {
  static get is() { return 'edit-note'; }

  static get properties() {
    return {
      statePath: String,
      isOpen: {type: Boolean, reflect: true},
      id: Number,
      suite: String,
      measurement: String,
      bot: String,
      case: String,
      text: String,
      minRevision: Number,
      maxRevision: Number,
    };
  }

  static buildState(options = {}) {
    return {
      id: options.id || 0,
      isOpen: options.isOpen || false,
      suite: options.suite || '',
      measurement: options.measurement || '',
      bot: options.bot || '',
      case: options.case || '',
      text: options.text || '',
      minRevision: options.minRevision || 0,
      maxRevision: options.maxRevision || 0,
    };
  }

  static get styles() {
    return css`
      #dialog {
        background: var(--background-color, white);
        bottom: 0;
        box-shadow: var(--elevation-2);
        display: none;
        min-width: 500px;
        padding: 8px;
        position: absolute;
        transform: translateX(-50%);
      }
      :host {
        position: relative;
      }
      :host([isOpen]) #dialog {
        display: block;
      }
      #buttons {
        display: flex;
      }
      #buttons chops-button {
        flex-grow: 1;
      }
    `;
  }

  render() {
    return html`
      <chops-button
          @click="${this.onEdit_}">
        <cp-icon icon="edit"></cp-icon>
        ${this.id ? 'Edit' : 'Create'}
      </chops-button>

      <div id="dialog">
        <chops-input
            id="suite"
            label="Suite"
            tabindex="0"
            value="${this.suite}"
            @change="${this.onSuite_}">
        </chops-input>
        (Clear to match all suites.)

        <chops-input
            id="measurement"
            label="Measurement"
            tabindex="0"
            value="${this.measurement}"
            @change="${this.onMeasurement_}">
        </chops-input>
        (Clear to match all measurements.)

        <chops-input
            id="bot"
            label="Bot"
            tabindex="0"
            value="${this.bot}"
            @change="${this.onBot_}">
        </chops-input>
        (Clear to match all bots.)

        <chops-input
            id="case"
            label="Case"
            tabindex="0"
            value="${this.case}"
            @change="${this.onCase_}">
        </chops-input>
        (Clear to match all bots.)

        <chops-input
            id="min-revision"
            label="Min Revision"
            tabindex="0"
            value="${this.minRevision}"
            @change="${this.onMinRevision_}">
        </chops-input>

        <chops-input
            id="max-revision"
            label="Max Revision"
            tabindex="0"
            value="${this.maxRevision}"
            @change="${this.onMaxRevision_}">
        </chops-input>

        <chops-textarea
            autofocus
            id="text"
            label="Text"
            tabindex="0"
            value="${this.text}"
            @keyup="${this.onText_}">
        </chops-textarea>

        <div id="buttons">
          <chops-button
              id="cancel"
              @click="${this.onCancel_}"
              tabindex="0">
            Cancel
          </chops-button>

          <chops-button
              id="submit"
              @click="${this.onSubmit_}"
              tabindex="0">
            Submit
          </chops-button>
        </div>
      </div>
    `;
  }

  async stateChanged(rootState) {
    const oldIsOpen = this.isOpen;
    super.stateChanged(rootState);

    if (this.isOpen && !oldIsOpen) {
      await this.updateComplete;
      this.shadowRoot.querySelector('#text').focus();
    }
  }

  onEdit_(event) {
    STORE.dispatch(TOGGLE(this.statePath + '.isOpen'));
  }

  onSuite_(event) {
    STORE.dispatch(UPDATE(this.statePath, {suite: event.target.value}));
  }

  onMeasurement_(event) {
    STORE.dispatch(UPDATE(this.statePath, {measurement: event.target.value}));
  }

  onBot_(event) {
    STORE.dispatch(UPDATE(this.statePath, {bot: event.target.value}));
  }

  onCase_(event) {
    STORE.dispatch(UPDATE(this.statePath, {case: event.target.value}));
  }

  onMinRevision_(event) {
    STORE.dispatch(UPDATE(this.statePath, {
      minRevision: parseInt(event.target.value),
    }));
  }

  onMaxRevision_(event) {
    STORE.dispatch(UPDATE(this.statePath, {
      maxRevision: parseInt(event.target.value),
    }));
  }

  onText_(event) {
    STORE.dispatch(UPDATE(this.statePath, {text: event.target.value}));
  }

  onCancel_(event) {
    STORE.dispatch(UPDATE(this.statePath, {isOpen: false}));
  }

  async onSubmit_(event) {
    const request = new NotesRequest({
      suite: this.suite,
      measurement: this.measurement,
      bot: this.bot,
      case: this.case,
      minRevision: this.minRevision,
      maxRevision: this.maxRevision,
      text: this.text,
      id: this.id,
    });
    const response = await request.response;
    console.log(response);
  }
}

ElementBase.register(EditNote);
