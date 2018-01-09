/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class TestPathComponent extends cp.ElementBase {
    static get is() { return 'test-path-component'; }

    static get properties() {
      return cp.ElementBase.statePathProperties('statePath', {
        canAggregate: {type: Boolean},
        isAggregated: {type: Boolean},
        tags: {type: Object},
        selectedOptions: {type: Array},
      });
    }

    isMultiple_(ary) {
      return ary.length > 1;
    }

    onKeydown_(e) {
      this.dispatch('keydown', this.statePath, e.detail.value);
    }

    onClear_(e) {
      this.dispatch('clear', this.statePath);
    }

    onSelect_(e) {
      // Allow this event to bubble up.
      cp.ElementBase.measureInputLatency('test-path-component', 'select', e);
      this.dispatch('updateInputValue', this.statePath);
    }

    onAggregateChange_(e) {
      this.dispatch('toggleAggregate', this.statePath);
      this.dispatchEvent(new CustomEvent('aggregate'));
    }
  }

  TestPathComponent.actions = {
    keydown: (statePath, inputValue) => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(
          statePath, {inputValue}));
    },

    clear: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(statePath, {
        inputValue: '',
        selectedOptions: [],
      }));
      dispatch(cp.DropdownInput.actions.focus(statePath));
    },

    toggleAggregate: (statePath, isAggregated) =>
      async (dispatch, getState) => {
        dispatch(cp.ElementBase.actions.toggleBoolean(
            `${statePath}.isAggregated`));
      },

    select: (statePath, selectedOptions) =>
      async (dispatch, getState) => {
        dispatch(cp.ElementBase.actions.updateObject(statePath, {
          selectedOptions
        }));
        dispatch(TestPathComponent.actions.updateInputValue(statePath));
      },

    updateInputValue: statePath => async (dispatch, getState) => {
      dispatch({
        type: TestPathComponent.reducers.updateInputValue.typeName,
        statePath,
      });
    },
  };

  TestPathComponent.reducers = {
    updateInputValue: cp.ElementBase.statePathReducer((state, action) => {
      let inputValue = state.inputValue;
      if (state.selectedOptions.length === 0) {
        inputValue = '';
      } else if (state.selectedOptions.length === 1) {
        inputValue = state.selectedOptions[0];
      } else if (state.selectedOptions.length > 1) {
        inputValue = `[${state.selectedOptions.length} selected]`;
      }
      return {...state, inputValue};
    }),
  };

  cp.ElementBase.register(TestPathComponent);

  return {
    TestPathComponent,
  };
});
