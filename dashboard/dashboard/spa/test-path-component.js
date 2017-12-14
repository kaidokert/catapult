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
        tagMap: {type: Object},
      });
    }

    onFocus_(e) {
      this.dispatch(TestPathComponent.focus(
          this.sectionId, this.componentIndex, true));
    }

    static focus(sectionId, componentIndex, isFocused) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'test-path-component.focus',
          sectionId,
          componentIndex,
          isFocused,
        });
      };
    }

    onBlur_(e) {
      this.dispatch(TestPathComponent.focus(
          this.sectionId, this.componentIndex, false));
    }

    onKeydown_(e) {
      this.dispatch(TestPathComponent.keydown(
          this.sectionId, this.componentIndex, e.detail));
    }

    static keydown(sectionId, componentIndex, detail) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'test-path-component.keydown',
          sectionId,
          componentIndex,
          value: detail.value,
        });
      };
    }

    onClear_(e) {
      this.dispatch(TestPathComponent.clear(
          this.sectionId, this.componentIndex));
    }

    static clear(sectionId, componentIndex) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'test-path-component.clear',
          sectionId,
          componentIndex,
        });
        dispatch(cp.ChartSection.maybeLoadTimeseries(sectionId));
      };
    }

    onSelect_(e) {
      cp.measureInputLatency('test-path-component', 'select', e);
      this.dispatch(TestPathComponent.select(
          this.sectionId, this.componentIndex, e.detail.selectedOptions));
    }

    static select(sectionId, componentIndex, selectedOptions) {
      return async (dispatch, getState) => {
        if (selectedOptions === undefined) return;
        dispatch({
          type: 'test-path-component.select',
          sectionId,
          componentIndex,
          selectedOptions,
        });

        dispatch(cp.ChartSection.maybeLoadTimeseries(sectionId));
      };
    }

    onAggregateChange_(e) {
      this.dispatch(TestPathComponent.aggregate(
          this.sectionId, this.componentIndex, this.$.aggregate.checked));
    }

    static aggregate(sectionId, componentIndex, isAggregated) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'test-path-component.aggregate',
          sectionId,
          componentIndex,
          isAggregated,
        });

        dispatch(cp.ChartSection.maybeLoadTimeseries(sectionId));
      };
    }

    onToggleGroupExpanded_(e) {
      this.dispatch(TestPathComponent.toggleGroupExpanded(
          this.sectionId, this.componentIndex, e.detail.path));
    }

    static toggleGroupExpanded(sectionId, componentIndex, path) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'test-path-component.toggleGroupExpanded',
          sectionId,
          componentIndex,
          path,
        });
      };
    }
  }
  customElements.define(TestPathComponent.is, TestPathComponent);

  cp.sectionReducer('test-path-component.toggleGroupExpanded',
      (state, action, section) => {
        return {
          testPathComponents: cp.assignInArray(
              section.testPathComponents, action.componentIndex, {
                options: cp.DropdownInput.toggleGroupExpanded(
                    section.testPathComponents[action.componentIndex].options,
                    action.path),
              }),
        };
      });

  cp.sectionReducer('test-path-component.aggregate',
      (state, action, section) => {
        return {
          testPathComponents: cp.assignInArray(
              section.testPathComponents, action.componentIndex,
              {isAggregated: action.isAggregated}),
        };
      });

  cp.sectionReducer('test-path-component.clear', (state, action, section) => {
    return {
      testPathComponents: cp.assignInArray(
          section.testPathComponents, action.componentIndex, {
            inputValue: '',
            selectedOptions: [],
            isFocused: true,
          }),
    };
  });

  cp.sectionReducer('test-path-component.select', (state, action, section) => {
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
    let newComponents = cp.assignInArray(oldComponents, action.componentIndex, {
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
  });

  cp.sectionReducer('test-path-component.focus', (state, action, section) => {
    return {
      testPathComponents: cp.assignInArray(
          section.testPathComponents, action.componentIndex,
          {isFocused: action.isFocused}),
    };
  });

  cp.sectionReducer('test-path-component.keydown',
      (state, action, section) => {
        return {
          testPathComponents: cp.assignInArray(
              section.testPathComponents, action.componentIndex,
              {inputValue: action.value}),
        };
      });

  return {
    TestPathComponent,
  };
});
