/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  function makeProperties(configs) {
    const properties = {
      sectionId: Number,
      componentIndex: Number,
    };
    for (const [name, config] of Object.entries(configs)) {
      properties[name] = {
        ...config,
        statePath(state) {
          if (!state.sectionsById[this.sectionId]) return undefined;
          if (!state.sectionsById[this.sectionId].testPathComponents[
              this.componentIndex]) {
            return undefined;
          }
          return state.sectionsById[this.sectionId].testPathComponents[
              this.componentIndex][name];
        },
      };
    }
    return properties;
  }

  class TestPathComponent extends cp.Element {
    static get is() { return 'test-path-component'; }

    static get properties() {
      return makeProperties({
        canAggregate: {type: Boolean},
        inputValue: {type: String},
        isAggregated: {type: Boolean},
        isFocused: {type: Boolean},
        multipleSelectedOptions: {type: Boolean},
        options: {type: Array},
        placeholder: {type: String},
        selectedOptions: {type: Array},
        tagOptions: {type: Object},
      });
    }

    onFocus_(e) {
      this.dispatch('focus', this.sectionId, this.componentIndex, true);
    }

    onBlur_(e) {
      this.dispatch('focus', this.sectionId, this.componentIndex, false);
    }

    onKeydown_(e) {
      this.dispatch('keydown', this.sectionId, this.componentIndex, e.detail);
    }

    onClear_(e) {
      this.dispatch('clear', this.sectionId, this.componentIndex);
    }

    onSelect_(e) {
      cp.measureInputLatency('test-path-component', 'select', e);
      this.dispatch('select',
          this.sectionId, this.componentIndex, e.detail.selectedOptions);
    }

    onAggregateChange_(e) {
      this.dispatch('aggregate',
          this.sectionId, this.componentIndex, this.$.aggregate.checked);
    }

    onToggleTagGroupExpanded_(e) {
      e.cancelBubble = true;
      this.dispatch('toggleTagGroupExpanded',
          this.sectionId, this.componentIndex, e.detail.path);
    }

    onToggleGroupExpanded_(e) {
      this.dispatch('toggleGroupExpanded',
          this.sectionId, this.componentIndex, e.detail.path);
    }
  }

  TestPathComponent.actions = {
    toggleGroupExpanded: (sectionId, componentIndex, path) =>
      async (dispatch, getState) => {
        dispatch({
          type: 'test-path-component.toggleGroupExpanded',
          sectionId,
          componentIndex,
          path,
        });
      },

    toggleTagGroupExpanded: (sectionId, componentIndex, path) =>
      async (dispatch, getState) => {
        dispatch({
          type: 'test-path-component.toggleTagGroupExpanded',
          sectionId,
          componentIndex,
          path,
        });
      },

    focus: (sectionId, componentIndex, isFocused) =>
      async (dispatch, getState) => {
        dispatch({
          type: 'test-path-component.focus',
          sectionId,
          componentIndex,
          isFocused,
        });
      },

    keydown: (sectionId, componentIndex, detail) =>
      async (dispatch, getState) => {
        dispatch({
          type: 'test-path-component.keydown',
          sectionId,
          componentIndex,
          value: detail.value,
        });
      },

    clear: (sectionId, componentIndex) => async (dispatch, getState) => {
      dispatch({
        type: 'test-path-component.clear',
        sectionId,
        componentIndex,
      });
      dispatch(cp.ChartSection.actions.maybeLoadTimeseries(sectionId));
    },

    select: (sectionId, componentIndex, selectedOptions) =>
      async (dispatch, getState) => {
        if (selectedOptions === undefined) return;
        dispatch({
          type: 'test-path-component.select',
          sectionId,
          componentIndex,
          selectedOptions,
        });

        dispatch(cp.ChartSection.actions.maybeLoadTimeseries(sectionId));
      },

    aggregate: (sectionId, componentIndex, isAggregated) =>
      async (dispatch, getState) => {
        dispatch({
          type: 'test-path-component.aggregate',
          sectionId,
          componentIndex,
          isAggregated,
        });

        dispatch(cp.ChartSection.actions.maybeLoadTimeseries(sectionId));
      },
  };

  TestPathComponent.reducers = {
    toggleTagGroupExpanded: cp.sectionReducer((section, action) => {
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

    toggleGroupExpanded: cp.sectionReducer((section, action) => {
      return {
        testPathComponents: cp.assignInArray(
            section.testPathComponents, action.componentIndex, {
              options: cp.DropdownInput.toggleGroupExpanded(
                  section.testPathComponents[action.componentIndex].options,
                  action.path),
            }),
      };
    }),

    aggregate: cp.sectionReducer((section, action) => {
      return {
        testPathComponents: cp.assignInArray(
            section.testPathComponents, action.componentIndex,
            {isAggregated: action.isAggregated}),
      };
    }),

    clear: cp.sectionReducer((section, action) => {
      return {
        testPathComponents: cp.assignInArray(
            section.testPathComponents, action.componentIndex, {
              inputValue: '',
              selectedOptions: [],
              isFocused: true,
            }),
      };
    }),

    select: cp.sectionReducer((section, action) => {
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

    focus: cp.sectionReducer((section, action) => {
      return {
        testPathComponents: cp.assignInArray(
            section.testPathComponents, action.componentIndex,
            {isFocused: action.isFocused}),
      };
    }),

    keydown: cp.sectionReducer((section, action) => {
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
