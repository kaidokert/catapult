/*
Copyright 2017 The Chromium Authors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be
found in the LICENSE file.
*/
'use strict';

tr.exportTo('cp', () => {
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
