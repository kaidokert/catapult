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

    static get actions() { return window.ACTION_CREATORS; }

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

    multipleValues_(/* TODO values */) {
      return false;
      // return values && values.length > 1;
    }

    onFocus_(e) {
      this.dispatch({
        type: 'testPathFocus',
        sectionId: this.sectionId,
        componentIndex: this.componentIndex,
        isFocused: true,
      });
    }

    onBlur_(e) {
      this.dispatch({
        type: 'testPathFocus',
        sectionId: this.sectionId,
        componentIndex: this.componentIndex,
        isFocused: false,
      });
    }

    onKeydown_(e) {
      this.dispatch({
        type: 'testPathKeydown',
        sectionId: this.sectionId,
        componentIndex: this.componentIndex,
        value: e.detail.value,
      });
    }

    onSelect_(e) {
      if (e.detail.value !== this.value) {
        this.dispatch({
          type: 'selectTestPathComponent',
          sectionId: this.sectionId,
          componentIndex: this.componentIndex,
          value: e.detail.value,
        });
      }
    }

    onAggregateChange_(e) {
      this.dispatch({
        type: 'testPathAggregate',
        sectionId: this.sectionId,
        componentIndex: this.componentIndex,
        value: this.$.aggregate.checked,
      });
    }
  }
  customElements.define(TestPathComponent.is, TestPathComponent);

  /**
   * @param {Number} action.sectionId
   * @param {Number} action.componentIndex
   * @param {String} action.value
   */
  cp.REDUCERS.set('selectTestPathComponent', (state, action) => {
    const oldComponents = state.sections[action.sectionId].testPathComponents;
    const oldComponent = oldComponents[action.componentIndex];
    let newComponents = cp.assignInArray(oldComponents, action.componentIndex, {
      value: action.value,
      isFocused: false,
    });
    if ((1 + action.componentIndex) < newComponents.length) {
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
  cp.REDUCERS.set('testPathFocus', (state, action) => {
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
  cp.REDUCERS.set('testPathKeydown', (state, action) => {
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
