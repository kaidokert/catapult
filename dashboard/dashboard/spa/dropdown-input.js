/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  function elementIsChildOf(el, potentialParent) {
    if (el === potentialParent) return false;

    let cur = el;
    while (Polymer.dom(cur).parentNode) {
      if (cur === potentialParent) return true;
      cur = Polymer.dom(cur).parentNode;
    }
    return false;
  }

  class DropdownInput extends cp.ElementBase {
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

    onFocus_(event) {
      this.dispatch('focus', this.statePath);
    }

    onBlur_(event) {
      if (event.relatedTarget === this.$.dropdown ||
          elementIsChildOf(event.relatedTarget, this) ||
          elementIsChildOf(event.relatedTarget, this.$.dropdown)) {
        this.$.input.focus();
        return;
      }
      this.dispatch('blur', this.statePath);
    }

    onKeydown_(event) {
      if (event.key === 'Escape') {
        this.$.input.blur();
        return;
      }
      this.dispatch('keydown', this.statePath, this.value);
      this.dispatchEvent(new CustomEvent('input-keydown', {
        detail: {
          key: event.key,
          value: this.value,
        },
      }));
    }

    onClear_(event) {
      this.dispatch('clear', this.statePath);
      this.dispatchEvent(new CustomEvent('clear'));
      this.dispatchEvent(new CustomEvent('option-select', {
        bubbles: true,
        composed: true,
      }));
    }
  }

  DropdownInput.properties = {
    ...cp.ElementBase.statePathProperties('statePath', {
      disabled: {type: Boolean},
      inputValue: {type: String},
      focusTimestamp: {type: Number},
      options: {type: Array},
      label: {type: String},
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
