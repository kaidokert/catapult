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
          selectedOptions: {
            type: Array,
            value: [],
          },
        }),
        isRoot: {
          type: Boolean,
          value: false,
        },
      };
    }

    countDescendents_(children) {
      return OptionGroup.countDescendents(children);
    }

    static countDescendents(children) {
      let count = 0;
      for (const option of children) {
        if (option.children) {
          count += OptionGroup.countDescendents(option.children);
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

    indentRow_(option) {
      if (option.children) return false;
      return !this.isRoot || this.getAnyGroups_(this.options);
    }

    getAnyGroups_(options) {
      if (!options) return false;
      for (const option of options) {
        if (option.children) return true;
      }
      return false;
    }

    onSelect_(e) {
      const selectedOptions = Array.from(this.selectedOptions);
      if (e.target.checked) {
        selectedOptions.push(this.value_(e.model.option));
      } else {
        selectedOptions.splice(
            selectedOptions.indexOf(this.value_(e.model.option)), 1);
      }
      this.dispatchEvent(new CustomEvent('option-select', {
        bubbles: true,
        composed: true,
        detail: {selectedOptions},
      }));
    }

    toggleGroupExpanded_(e) {
      this.dispatch('toggleGroupExpanded', this.statePath, e.model.optionIndex);
    }
  }

  OptionGroup.actions = {
    toggleGroupExpanded: (statePath, optionIndex) =>
      async (dispatch, getState) => {
        const option = cp.ElementBase.getStateAtPath(
            getState(), statePath).options[optionIndex];
        dispatch({
          type: 'element-base.setStateAtPath',
          statePath: statePath.concat(['options', optionIndex, 'isExpanded']),
          value: !option.isExpanded,
        });
      },
  };

  cp.ElementBase.register(OptionGroup);

  return {
    OptionGroup,
  };
});
