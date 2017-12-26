/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class TestPathComponent extends cp.Element {
    static get is() { return 'test-path-component'; }

    static get properties() {
      return cp.ElementBase.statePathProperties('statePath', {
        canAggregate: {type: Boolean},
        isAggregated: {type: Boolean},
        multipleSelectedOptions: {type: Boolean},
        tagOptions: {type: Object},
      });
    }

    onFocus_(e) {
      this.dispatch('focus', this.statePath, true);
    }

    onBlur_(e) {
      this.dispatch('focus', this.statePath, false);
    }

    onKeydown_(e) {
      this.dispatch('keydown', this.statePath, e.detail);
    }

    onClear_(e) {
      this.dispatch('clear', this.statePath);
    }

    onSelect_(e) {
      cp.measureInputLatency('test-path-component', 'select', e);
      this.dispatch('select', this.statePath, e.detail.selectedOptions);
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
    toggleGroupExpanded: (statePath, groupPath) =>
      async (dispatch, getState) => {
        dispatch({
          type: 'test-path-component.toggleGroupExpanded',
          statePath,
          groupPath,
        });
      },

    toggleTagGroupExpanded: (statePath, groupPath) =>
      async (dispatch, getState) => {
        dispatch({
          type: 'test-path-component.toggleTagGroupExpanded',
          statePath,
          groupPath,
        });
      },

    focus: (statePath, isFocused) =>
      async (dispatch, getState) => {
        dispatch({
          type: 'test-path-component.focus',
          statePath,
          isFocused,
        });
      },

    keydown: (statePath, detail) =>
      async (dispatch, getState) => {
        dispatch({
          type: 'test-path-component.keydown',
          statePath,
          value: detail.value,
        });
      },

    clear: statePath => async (dispatch, getState) => {
      dispatch({
        type: 'test-path-component.clear',
        statePath,
      });
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

    aggregate: (statePath, isAggregated) =>
      async (dispatch, getState) => {
        dispatch({
          type: 'test-path-component.aggregate',
          statePath,
          isAggregated,
        });
      },
  };

  TestPathComponent.reducers = {
    toggleTagGroupExpanded: cp.ElementBase.statePathReducer(
        (section, action) => {
          const components = section.testPathComponents;
          return {
            testPathComponents: cp.assignInArray(
                components, action.componentIndex, {
                  tagOptions: cp.DropdownInput.toggleGroupExpanded(
                      components[action.componentIndex].tagOptions,
                      action.path),
                }),
          };
        }),

    toggleGroupExpanded: cp.ElementBase.statePathReducer((section, action) => {
      return {
        testPathComponents: cp.assignInArray(
            section.testPathComponents, action.componentIndex, {
              options: cp.DropdownInput.toggleGroupExpanded(
                  section.testPathComponents[action.componentIndex].options,
                  action.path),
            }),
      };
    }),

    aggregate: cp.ElementBase.statePathReducer((section, action) => {
      return {
        testPathComponents: cp.assignInArray(
            section.testPathComponents, action.componentIndex,
            {isAggregated: action.isAggregated}),
      };
    }),

    clear: cp.ElementBase.statePathReducer((section, action) => {
      return {
        testPathComponents: cp.assignInArray(
            section.testPathComponents, action.componentIndex, {
              inputValue: '',
              selectedOptions: [],
              isFocused: true,
            }),
      };
    }),

    select: cp.ElementBase.statePathReducer((section, action) => {
      const oldComponents = section.testPathComponents;
      const oldComponent = oldComponents[action.componentIndex];
      let inputValue = oldComponent.inputValue;
      if (action.selectedOptions.length === 0) {
        inputValue = '';
      } else if (action.selectedOptions.length === 1) {
        inputValue = action.selectedOptions[0];
      } else if (action.selectedOptions.length > 1) {
        inputValue = `[${action.selectedOptions.length} selected]`;
      }
      let newComponents = cp.assignInArray(
          oldComponents, action.componentIndex, {
            selectedOptions: action.selectedOptions,
            multipleSelectedOptions: action.selectedOptions.length > 1,
            isAggregated:
              (action.selectedOptions.length > 1) && oldComponent.isAggregated,
            inputValue,
            isFocused: false,
          });
      if ((1 + action.componentIndex) < 3) {
        newComponents = cp.assignInArray(
            newComponents, 1 + action.componentIndex, {isFocused: true});
      }

      return {
        testPathComponents: newComponents,
      };
    }),

    focus: cp.ElementBase.statePathReducer((section, action) => {
      return {
        testPathComponents: cp.assignInArray(
            section.testPathComponents, action.componentIndex,
            {isFocused: action.isFocused}),
      };
    }),

    keydown: cp.ElementBase.statePathReducer((section, action) => {
      return {
        testPathComponents: cp.assignInArray(
            section.testPathComponents, action.componentIndex,
            {inputValue: action.value}),
      };
    }),
  };

  cp.Element.register(TestPathComponent);

  return {
    TestPathComponent,
  };
});
