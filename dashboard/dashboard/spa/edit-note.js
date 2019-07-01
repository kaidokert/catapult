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
import {html, css} from 'lit-element';

export class EditNote extends ElementBase {
  static get is() { return 'edit-note'; }

  static get properties() {
    return {
      statePath: String,
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
    `;
  }

  render() {
    return html`
      <chops-button
          @click="${this.onEdit_}">
        <cp-icon icon="edit"></cp-icon>
        Edit
      </chops-button>

      <div id="dialog">
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

        <chops-button
            id="submit"
            @click="${this.onSubmit_}"
            tabindex="0">
          Submit
        </chops-button>
      </div>
    `;
  }

  onMinRevision_(event) {
    console.log(event);
  }

  onMaxRevision_(event) {
    console.log(event);
  }

  onText_(event) {
    console.log(event);
  }

  onSubmit_(event) {
    console.log(event);
  }
}

ElementBase.register(EditNote);
