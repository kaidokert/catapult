/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class CreateElement extends cp.ElementBase {
    static get is() { return 'create-element'; }

    static get properties() {
      return {
        tagName: {
          type: String,
          value: 'div',
          observer: 'update_',
        },
        properties: {
          type: Object,
          value: {},
          observer: 'update_',
        },
      };
    }

    get content() {
      return this.content_;
    }

    update_() {
      if (this.content_) {
        this.shadowRoot.removeChild(this.content_);
      }
      this.content_ = document.createElement(this.tagName);
      Object.assign(this.content_, this.properties);
      Object.assign(this.content_, this.dataset);
      this.shadowRoot.appendChild(this.content_);
    }
  }

  CreateElement.reducers = {};

  cp.ElementBase.register(CreateElement);

  return {
    CreateElement,
  };
});
