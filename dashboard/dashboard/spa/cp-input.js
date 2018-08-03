/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class CpInput extends cp.ElementBase {
    async connectedCallback() {
      super.connectedCallback();
      if (this.autofocus) {
        while (cp.ElementBase.getActiveElement() !== this.nativeInput) {
          this.$.input.focus();
          await cp.ElementBase.timeout(50);
        }
      }
    }

    get nativeInput() {
      return this.$.input;
    }

    focus() {
      this.nativeInput.focus();
    }

    async onKeyup_(event) {
      this.value = event.target.value;
    }
  }

  CpInput.properties = {
    autofocus: {type: Boolean},
    disabled: {
      type: Boolean,
      reflectToAttribute: true,
    },
    placeholder: {type: String},
    value: {type: String},
  };

  cp.ElementBase.register(CpInput);

  return {
    CpInput,
  };
});
