/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class DropdownInput extends cp.ElementBase {
    static get is() { return 'dropdown-input'; }

    static get properties() {
      return {
        ...cp.ElementBase.statePathProperties('statePath', {
          disabled: {type: Boolean},
          inputValue: {type: String},
          focusTimestamp: {type: Number},
          options: {type: Array},
          placeholder: {type: String},
          selectedOptions: {type: Array},
        }),
        rootFocusTimestamp: {
          type: Number,
          statePath: 'focusTimestamp',
        },
        isFocused: {
          type: Boolean,
          computed: '_eq(focusTimestamp, rootFocusTimestamp)',
          observer: 'onIsFocusedChange_',
        },
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
      this.onIsFocusedChange_();
    }

    onFocus_(e) {
      this.dispatch('focus', this.statePath);
    }

    onBlur_(e) {
      if (e.relatedTarget === this.$.dropdown ||
          tr.ui.b.elementIsChildOf(e.relatedTarget, this) ||
          tr.ui.b.elementIsChildOf(e.relatedTarget, this.$.dropdown)) {
        this.$.input.focus();
        return;
      }
      this.dispatch('blur', this.statePath);
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
  }

  DropdownInput.actions = {
    focus: statePath => async (dispatch, getState) => {
      dispatch({
        type: DropdownInput.reducers.focus.typeName,
        statePath,
      });
    },

    blurAll: () => async (dispatch, getState) => {
      dispatch({
        type: DropdownInput.reducers.blur.typeName,
        statePath: '',
      });
    },

    blur: statePath => async (dispatch, getState) => {
      dispatch({
        type: DropdownInput.reducers.blur.typeName,
        statePath,
      });
    },

    clear: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(
          statePath, {inputValue: '', selectedOptions: []}));
      dispatch(cp.DropdownInput.actions.focus(statePath, true));
    },

    keydown: (statePath, inputValue) => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(
          statePath, {inputValue}));
    },
  };

  DropdownInput.reducers = {
    focus: (state, action) => {
      const focusTimestamp = window.performance.now();
      state = {...state, focusTimestamp};
      if (!action.statePath) return state;
      return Polymer.Path.setImmutable(state, action.statePath, inputState => {
        return {...inputState, focusTimestamp};
      });
    },

    blur: cp.ElementBase.statePathReducer((state, action) => {
      return {...state, focusTimestamp: window.performance.now()};
    }),
  };

  cp.ElementBase.register(DropdownInput);

  return {
    DropdownInput,
  };
});
