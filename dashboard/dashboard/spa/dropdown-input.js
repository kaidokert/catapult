/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class DropdownInput extends cp.ElementBase {
    static get is() { return 'dropdown-input'; }

    static get properties() {
      return cp.ElementBase.statePathProperties('statePath', {
        disabled: {type: Boolean},
        inputValue: {type: String},
        isFocused: {
          type: Boolean,
          value: false,
          observer: 'onIsFocusedChange_',
        },
        options: {type: Array},
        placeholder: {type: String},
        selectedOptions: {type: Array},
      });
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
      const option = options[path[0]];
      let delta;
      if (path.length === 1) {
        delta = {
          isExpanded: !option.isExpanded,
        };
      } else {
        delta = {
          children: DropdownInput.toggleGroupExpanded(
              option.children, path.slice(1)),
        };
      }
      options = Array.from(options);
      options.splice(path[0], 1, {
        ...option,
        ...delta,
      });
      return options;
    }
  }
  customElements.define(DropdownInput.is, DropdownInput);

  return {
    DropdownInput,
  };
});
