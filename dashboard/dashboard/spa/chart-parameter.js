/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class ChartParameter extends cp.ElementBase {
    isMultiple_(ary) {
      return ary.length > 1;
    }

    onKeydown_(event) {
      this.dispatch('keydown', this.statePath, event.detail.value);
    }

    onClear_(event) {
      this.dispatch('clear', this.statePath);
    }

    onSelect_(event) {
      // Allow this event to bubble up.
      this.dispatch('updateInputValue', this.statePath);
    }

    onAggregateChange_(event) {
      this.dispatch('toggleAggregate', this.statePath);
      this.dispatchEvent(new CustomEvent('aggregate'));
    }
  }

  ChartParameter.properties = cp.ElementBase.statePathProperties('statePath', {
    canAggregate: {type: Boolean},
    isAggregated: {type: Boolean},
    tags: {type: Object},
    selectedOptions: {type: Array},
  });

  ChartParameter.actions = {
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
        dispatch(ChartParameter.actions.updateInputValue(statePath));
      },

    updateInputValue: statePath => async (dispatch, getState) => {
      dispatch({
        reducer: ChartParameter.reducers.updateInputValue,
        statePath,
      });
    },
  };

  ChartParameter.reducers = {
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

  cp.ElementBase.register(ChartParameter);

  return {
    ChartParameter,
  };
});
