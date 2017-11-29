/*
Copyright 2017 The Chromium Authors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be
found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class DropdownInput extends Polymer.Element {
    static get is() { return 'dropdown-input'; }

    static get properties() {
      return {
        placeholder: {
          type: String,
          value: '',
        },

        disabled: {
          type: Boolean,
          value: false,
        },

        inputValue: {
          type: String,
          value: '',
        },

        options: {
          type: Array,
          value: [],
        },

        selectedOptions: {
          type: Array,
          value: [],
        },

        isFocused: {
          type: Boolean,
          value: false,
          observer: 'onIsFocusedChange_',
        }
      };
    }

    onIsFocusedChange_() {
      if (this.isFocused) {
        this.$.input.focus();
      } else {
        this.$.input.blur();
      }
    }

    connectedCallback() {
      super.connectedCallback();
      if (this.isFocused) {
        this.$.input.focus();
      } else {
        this.$.input.blur();
      }
    }

    onInputFocus_(e) {
      this.dispatchEvent(new CustomEvent('input-focus'));
    }

    onInputBlur_(e) {
      if (e.relatedTarget === null) {
        // TODO or if e.relatedTarget is an element outside of dropdown_scroll
        this.dispatchEvent(new CustomEvent('input-blur'));
      }
    }

    onInputKeydown_(e) {
      this.dispatchEvent(new CustomEvent('input-keydown', {
        detail: {
          key: e.key,
          value: this.value,
        },
      }));
    }

    onInputClear_(e) {
      this.dispatchEvent(new CustomEvent('clear'));
    }

    onDropdownSelect_(e) {
      this.dispatchEvent(new CustomEvent('option-select', {
        detail: {selectedOptions: e.target.selectedValues},
      }));
    }
  }
  customElements.define(DropdownInput.is, DropdownInput);

  return {
  };
});
