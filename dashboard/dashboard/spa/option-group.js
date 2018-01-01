/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class OptionGroup extends cp.ElementBase {
    static get is() { return 'option-group'; }

    static get properties() {
      return {
        ...cp.ElementBase.statePathProperties('statePath', {
          options: {
            type: Array,
            value: [],
          },
        }),
        ...cp.ElementBase.statePathProperties('rootStatePath', {
          selectedOptions: {
            type: Array,
            value: [],
          },
        }),
      };
    }

    countDescendents_(options) {
      return OptionGroup.countDescendents(options);
    }

    static countDescendents(options) {
      let count = 0;
      for (const option of options) {
        if (option.options) {
          count += OptionGroup.countDescendents(option.options);
        } else {
          count += 1;
        }
      }
      return count;
    }

    isSelected_(option, selectedOptions) {
      if (!option || !selectedOptions) return false;
      return selectedOptions.includes(this.value_(option));
    }

    label_(option) {
      return option.label || this.value_(option);
    }

    value_(option) {
      return option.value || option;
    }

    isRoot_() {
      return this.statePath === this.rootStatePath;
    }

    indentRow_(option) {
      if (option.options) return false;
      return !this.isRoot_() || OptionGroup.getAnyGroups(this.options);
    }

    static getAnyGroups(options) {
      return (options || []).filter(o => o.options).length > 0;
    }

    onSelect_(e) {
      this.dispatch('select', this.rootStatePath, this.value_(e.model.option));
      this.dispatchEvent(new CustomEvent('option-select', {
        bubbles: true,
        composed: true,
      }));
    }

    toggleGroupExpanded_(e) {
      this.dispatch('toggleGroupExpanded', this.statePath, e.model.optionIndex);
    }
  }

  OptionGroup.actions = {
    select: (statePath, value) => async (dispatch, getState) => {
      dispatch({
        type: 'option-group.select',
        statePath,
        value,
      });
    },

    toggleGroupExpanded: (statePath, optionIndex) =>
      async (dispatch, getState) => {
        dispatch(cp.ElementBase.actions.toggleBooleanAtPath(
            `${statePath}.options.${optionIndex}.isExpanded`));
      },
  };

  OptionGroup.reducers = {
    select: cp.ElementBase.statePathReducer((state, action) => {
      const selectedOptions = Array.from(state.selectedOptions);
      if (selectedOptions.includes(action.value)) {
        selectedOptions.splice(selectedOptions.indexOf(action.value), 1);
      } else {
        selectedOptions.push(action.value);
      }
      return {...state, selectedOptions};
    }),
  };

  cp.ElementBase.register(OptionGroup);

  return {
    OptionGroup,
  };
});
