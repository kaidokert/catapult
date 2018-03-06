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
    connectedCallback() {
      super.connectedCallback();
      this.onIsFocusedChange_();
    }

    onIsFocusedChange_() {
      if (this.isFocused) {
        this.$.input.focus();
      } else {
        this.$.input.blur();
      }
    }

    isDisabled_(options) {
      return options.length === 0;
    }

    inputValue_(isFocused, query, selectedOptions) {
      return DropdownInput.inputValue(isFocused, query, selectedOptions);
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

    onKeyup_(event) {
      if (event.key === 'Escape') {
        this.$.input.blur();
        return;
      }
      this.dispatch('keydown', this.statePath, event.target.value);
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

  DropdownInput.inputValue = (isFocused, query, selectedOptions) => {
    if (isFocused) return query;
    if (selectedOptions.length === 0) return '';
    if (selectedOptions.length === 1) return selectedOptions[0];
    return `[${selectedOptions.length} selected]`;
  };

  DropdownInput.properties = {
    ...cp.ElementBase.statePathProperties('statePath', {
      query: {type: String},
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
      dispatch(cp.ElementBase.actions.updateObject(statePath, {
        query: '',
        selectedOptions: [],
      }));
      dispatch(cp.DropdownInput.actions.focus(statePath, true));
    },

    keydown: (statePath, query) => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(statePath, {
        query,
      }));
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
      return {
        ...state,
        focusTimestamp: window.performance.now(),
        query: '',
      };
    }),
  };

  cp.ElementBase.register(DropdownInput);

  return {
    DropdownInput,
  };
});
