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
        multipleSelectedOptions: {type: Boolean},
        hasTags: {type: Boolean},
        selectedOptions: {type: Array},
      });
    }

    onFocus_(e) {
      this.dispatch('focus', this.statePath, true);
    }

    onBlur_(e) {
      this.dispatch('focus', this.statePath, false);
    }

    onKeydown_(e) {
      this.dispatch('keydown', this.statePath, e.detail.value);
    }

    onClear_(e) {
      this.dispatch('clear', this.statePath);
    }

    onSelect_(e) {
      cp.ElementBase.measureInputLatency('test-path-component', 'select', e);
      this.dispatch('select', this.statePath, this.selectedOptions);
    }

    onAggregateChange_(e) {
      this.dispatch('aggregate', this.statePath, this.$.aggregate.checked);
    }

    onToggleTagGroupExpanded_(e) {
      e.cancelBubble = true;
      this.dispatch('toggleTagGroupExpanded', this.statePath, e.detail.path);
    }

    onToggleGroupExpanded_(e) {
      this.dispatch('toggleGroupExpanded',
          this.statePath, e.detail.path);
    }
  }

  TestPathComponent.actions = {
    focus: (statePath, isFocused) => async (dispatch, getState) => {
      // TODO dispatchEvent instead, let chromeperf-app handle this.
      dispatch(cp.ChromeperfApp.actions.focus(statePath, isFocused));
    },

    keydown: (statePath, inputValue) => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObjectAtPath(
          statePath, {inputValue}));
    },

    clear: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObjectAtPath(statePath, {
        inputValue: '',
        selectedOptions: [],
      }));
      dispatch(TestPathComponent.actions.focus(statePath, false));
    },

    aggregate: (statePath, isAggregated) => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObjectAtPath(statePath, {
        isAggregated,
      }));
    },

    select: (statePath, selectedOptions) =>
      async (dispatch, getState) => {
        if (selectedOptions === undefined) return;
        dispatch({
          type: 'test-path-component.select',
          statePath,
          selectedOptions,
        });
      },
  };

  TestPathComponent.reducers = {
    select: cp.ElementBase.statePathReducer((state, action) => {
      let inputValue = state.inputValue;
      if (action.selectedOptions.length === 0) {
        inputValue = '';
      } else if (action.selectedOptions.length === 1) {
        inputValue = action.selectedOptions[0];
      } else if (action.selectedOptions.length > 1) {
        inputValue = `[${action.selectedOptions.length} selected]`;
      }
      const isAggregated = (action.selectedOptions.length > 1) &&
        state.isAggregated;
      return {
        ...state,
        inputValue,
        isAggregated,
        isFocused: false,
      };
    }),
  };

  cp.ElementBase.register(TestPathComponent);

  return {
    TestPathComponent,
  };
});
