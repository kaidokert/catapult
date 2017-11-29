/*
Copyright 2017 The Chromium Authors. All rights reserved.
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
      properties[name] = Object.assign(config, {
        statePath(state) {
          if (!state.sections[this.sectionId]) return undefined;
          if (!state.sections[this.sectionId].testPathComponents[
              this.componentIndex]) {
            return undefined;
          }
          return state.sections[this.sectionId].testPathComponents[
              this.componentIndex][name];
        }
      });
    }
    return properties;
  }

  class TestPathComponent extends cp.Element {
    static get is() { return 'test-path-component'; }

    static get properties() {
      return makeProperties({
        placeholder: {type: String},
        value: {type: String},
        options: {type: Array},
        isFocused: {type: Boolean},
        canAggregate: {type: Boolean},
        isAggregated: {type: Boolean},
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
        if (detail.key === 'Escape') {
          dispatch(TestPathComponent.focus(sectionId, componentIndex, false));
          return;
        }
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
      };
    }

    onSelect_(e) {
      this.dispatch(TestPathComponent.select(
        this.sectionId, this.componentIndex, e.detail.value));
    }

    static select(sectionId, componentIndex, value) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'test-path-component.select',
          sectionId,
          componentIndex,
          value,
        });

        // If the first 3 components are filled, then load the timeseries.
        const components = getState().sections[sectionId].testPathComponents;
        if (components[0].value && components[1].value && components[2].value) {
          dispatch(cp.ChartSection.loadTimeseries(sectionId));
        }
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
          sectionId: this.sectionId,
          componentIndex: this.componentIndex,
          value: this.$.aggregate.checked,
        });
      };
    }
  }
  customElements.define(TestPathComponent.is, TestPathComponent);

  cp.REDUCERS.set('test-path-component.clear', (state, action) => {
    const oldComponents = state.sections[action.sectionId].testPathComponents;
    return cp.assignSection(state, action.sectionId, {
      testPathComponents: cp.assignInArray(oldComponents, action.componentIndex, {
        value: '',
        isFocused: true,
      }),
    });
  });

  /**
   * @param {Number} action.sectionId
   * @param {Number} action.componentIndex
   * @param {String} action.value
   */
  cp.REDUCERS.set('test-path-component.select', (state, action) => {
    const oldComponents = state.sections[action.sectionId].testPathComponents;
    const oldComponent = oldComponents[action.componentIndex];
    let newComponents = cp.assignInArray(oldComponents, action.componentIndex, {
      value: action.value,
      isFocused: false,
    });
    if ((1 + action.componentIndex) < (newComponents.length - 1)) {
      newComponents = cp.assignInArray(newComponents, 1 + action.componentIndex, {
        isFocused: true,
      });
    }

    return cp.assignSection(state, action.sectionId, {
      testPathComponents: newComponents,
    });
  });

  /**
   * @param {Number} action.sectionId
   * @param {Number} action.componentIndex
   * @param {Boolean} action.isFocused
   */
  cp.REDUCERS.set('test-path-component.focus', (state, action) => {
    const oldComponents = state.sections[action.sectionId].testPathComponents;
    return cp.assignSection(state, action.sectionId, {
      testPathComponents: cp.assignInArray(oldComponents, action.componentIndex, {
        isFocused: action.isFocused,
      }),
    });
  });

  /**
   * @param {Number} action.sectionId
   * @param {Number} action.componentIndex
   * @param {String} action.value
   */
  cp.REDUCERS.set('test-path-component.keydown', (state, action) => {
    const oldComponents = state.sections[action.sectionId].testPathComponents;
    return cp.assignSection(state, action.sectionId, {
      testPathComponents: cp.assignInArray(oldComponents, action.componentIndex, {
        value: action.value,
      }),
    });
  });

  return {
  };
});
