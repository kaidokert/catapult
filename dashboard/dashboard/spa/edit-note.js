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
import {renderMarkdown, isElementChildOf} from './utils.js';
import {unsafeHTML} from 'lit-html/directives/unsafe-html.js';
import {NotesRequest} from './notes-request.js';

export class EditNote extends ElementBase {
  static get is() { return 'edit-note'; }

  static get properties() {
    return {
      userEmail: String,
      statePath: String,
      isOpen: {type: Boolean, reflect: true},
      author: String,
      modified: Date,
      key: Number,
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
      key: options.key || 0,
      author: options.author || '',
      modified: options.modified || '',
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
      :host {
        position: relative;
      }
      #dialog {
        background: var(--background-color, white);
        bottom: 0;
        box-shadow: var(--elevation-2);
        display: none;
        min-width: 700px;
        padding: 8px;
        position: absolute;
        transform: translateX(-50%);
      }
      :host([isOpen]) #dialog {
        display: block;
      }
      #cancel {
        background: var(--background-color, white);
        box-shadow: none;
      }
      #buttons, #revisions, #descriptor {
        display: flex;
      }
      #descriptor *:not(:first-child),
      #revisions *:not(:first-child) {
        margin-left: 8px;
      }
      #revisions chops-input,
      #buttons chops-button {
        flex-grow: 1;
      }
      #conduct {
        align-items: center;
        display: flex;
        flex-direction: column;
        justify-content: center;
      }
      #editor {
        display: flex;
      }
      #editor * {
        flex-grow: 1;
      }
      .markdown-container {
        margin: 1em 4px 4px 4px;
        border: 1px solid var(--neutral-color-dark, grey);
        padding: 4px;
      }
      p {
        margin: 0 0 10px;
      }
      .label {
        background-color: var(--background-color, white);
        color: var(--neutral-color-dark, grey);
        font-size: smaller;
        padding: 4px;
        position: absolute;
        transform: translate(0px, -1.5em);
        white-space: nowrap;
      }
    `;
  }

  static isNumber(x) {
    if (typeof(x) === 'number' && !isNaN(x)) return true;
    if (typeof(x) === 'string' && x.match(/^\d+$/)) return true;
    return false;
  }

  render() {
    return html`
      ${!this.key ? '' : html`
        <div class="markdown-container">
          <div class="label">
            ${this.author} at ${tr.b.formatDate(this.modified)}
          </div>
          ${unsafeHTML(renderMarkdown(this.text))}
        </div>
      `}

      ${!this.userEmail ? '' : html`
        <chops-button
            @click="${this.onEdit_}">
          <cp-icon icon="edit"></cp-icon>
          ${this.key ? 'Edit' : 'Create'}
        </chops-button>
      `}

      <div id="dialog">
        <div id="descriptor">
          <chops-input
              id="suite"
              label="Suite"
              tabindex="0"
              value="${this.suite}"
              @change="${this.onSuite_}">
          </chops-input>

          <chops-input
              id="measurement"
              label="Measurement"
              tabindex="0"
              value="${this.measurement}"
              @change="${this.onMeasurement_}">
          </chops-input>

          <chops-input
              id="bot"
              label="Bot"
              tabindex="0"
              value="${this.bot}"
              @change="${this.onBot_}">
          </chops-input>

          <chops-input
              id="case"
              label="Case"
              tabindex="0"
              value="${this.case}"
              @change="${this.onCase_}">
          </chops-input>
        </div>

        <div id="revisions">
          <chops-input
              id="min-revision"
              label="Min Revision"
              tabindex="0"
              value="${this.minRevision}"
              ?error="${!EditNote.isNumber(this.minRevision)}"
              @change="${this.onMinRevision_}">
          </chops-input>

          <chops-input
              id="max-revision"
              label="Max Revision"
              tabindex="0"
              value="${this.maxRevision}"
              ?error="${!EditNote.isNumber(this.maxRevision)}"
              @change="${this.onMaxRevision_}">
          </chops-input>

          <div id="conduct">
            <a href="https://chromium.googlesource.com/catapult.git/+/HEAD/dashboard/docs/user-guide.md#notes" target="_blank">How notes work</a>
            <a href="https://chromium.googlesource.com/chromium/src/+/master/CODE_OF_CONDUCT.md" target="_blank">Code of Conduct</a>
          </div>
        </div>

        <div id="editor">
          <chops-textarea
              autofocus
              id="text"
              label="Text"
              tabindex="0"
              value="${this.text}"
              @keyup="${this.onText_}">
          </chops-textarea>

          <div class="markdown-container">
            <div class="label">Preview</div>
            ${unsafeHTML(renderMarkdown(this.text))}
          </div>
        </div>

        <div id="buttons">
          <chops-button
              id="cancel"
              @click="${this.onCancel_}"
              tabindex="0">
            Cancel
          </chops-button>

          <chops-button
              id="submit"
              ?disabled="${
  !EditNote.isNumber(this.minRevision) || !EditNote.isNumber(this.maxRevision)}"
              @click="${this.onSubmit_}"
              tabindex="0">
            Submit
          </chops-button>
        </div>
      </div>
    `;
  }

  firstUpdated() {
    this.addEventListener('blur', this.onBlur_.bind(this));
  }

  constructor() {
    super();
    this.text = '';
  }

  async stateChanged(rootState) {
    const oldIsOpen = this.isOpen;

    this.userEmail = rootState.userEmail;
    super.stateChanged(rootState);

    if (this.isOpen && !oldIsOpen) {
      await this.updateComplete;
      this.shadowRoot.querySelector('#text').focus();
    }
  }

  onBlur_(event) {
    if (event.relatedTarget === this ||
        isElementChildOf(event.relatedTarget, this)) {
      return;
    }
    STORE.dispatch(UPDATE(this.statePath, {isOpen: false}));
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
    STORE.dispatch(UPDATE(this.statePath, {isOpen: false}));
    const request = new NotesRequest({
      suite: this.suite,
      measurement: this.measurement,
      bot: this.bot,
      case: this.case,
      minRevision: this.minRevision,
      maxRevision: this.maxRevision,
      text: this.text,
      key: this.key,
    });
    const notes = await request.response;
    if (!notes || !notes.length) return;
    const note = notes[0];
    this.dispatchEvent(new CustomEvent('submit', {
      bubbles: true,
      composed: true,
      detail: {note},
    }));
  }
}

ElementBase.register(EditNote);
