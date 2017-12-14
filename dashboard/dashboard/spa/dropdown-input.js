/* Copyright 2017 The Chromium Authors. All rights reserved.
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

    onFocus_(e) {
      this.dispatchEvent(new CustomEvent('input-focus'));
    }

    onBlur_(e) {
      if (e.relatedTarget === this.$.dropdown ||
          tr.ui.b.elementIsChildOf(e.relatedTarget, this) ||
          tr.ui.b.elementIsChildOf(e.relatedTarget, this.$.dropdown)) {
        this.$.input.focus();
        return;
      }
      this.dispatchEvent(new CustomEvent('input-blur'));
    }

    onKeydown_(e) {
      if (e.key === 'Escape') {
        this.$.input.blur();
        return;
      }
      this.dispatchEvent(new CustomEvent('input-keydown', {
        detail: {
          key: e.key,
          value: this.value,
        },
      }));
    }

    onClear_(e) {
      this.dispatchEvent(new CustomEvent('clear'));
    }

    static toggleGroupExpanded(options, path) {
      if (path.length === 1) {
        return cp.assignInArray(options, path[0], {
          isExpanded: !options[path[0]].isExpanded,
        });
      }
      return cp.assignInArray(options, path[0], {
        children: DropdownInput.toggleGroupExpanded(
            options[path[0]].children, path.slice(1)),
      });
    }
  }
  customElements.define(DropdownInput.is, DropdownInput);

  return {
    DropdownInput,
  };
});
