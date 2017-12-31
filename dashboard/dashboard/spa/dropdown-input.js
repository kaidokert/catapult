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
      this.dispatch('keydown', this.statePath, this.value);
      this.dispatchEvent(new CustomEvent('input-keydown', {
        detail: {
          key: e.key,
          value: this.value,
        },
      }));
    }

    onClear_(e) {
      this.dispatch('clear', this.statePath);
      this.dispatchEvent(new CustomEvent('clear'));
    }

    onSelect_(e) {
      this.dispatch('select', this.statePath, e.detail.selectedOptions);
    }
  }

  DropdownInput.actions = {
    select: (statePath, selectedOptions) => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObjectAtPath(
          statePath, {selectedOptions}));
    },

    clear: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObjectAtPath(
          statePath, {inputValue: '', selectedOptions: []}));
      dispatch(cp.ChromeperfApp.actions.focus(statePath, true));
    },

    keydown: (statePath, inputValue) => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObjectAtPath(
          statePath, {inputValue}));
    },
  };

  cp.ElementBase.register(DropdownInput);

  return {
    DropdownInput,
  };
});
