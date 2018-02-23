/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class OptionGroup extends cp.ElementBase {
    shouldStampSubOptions_(option) {
      return option.isExpanded || option.options.length < 20;
    }

    countDescendents_(options) {
      return OptionGroup.countDescendents(options);
    }

    isSelected_(option, selectedOptions) {
      if (!option || !selectedOptions) return false;
      for (const value of OptionGroup.values(option)) {
        if (selectedOptions.includes(value)) return true;
      }
      return false;
    }

    label_(option) {
      if (typeof(option) === 'string') return option;
      return option.label;
    }

    indentRow_(option) {
      if (option.options) return false;
      return !this.isRoot || OptionGroup.getAnyGroups(this.options);
    }

    static getAnyGroups(options) {
      return (options || []).filter(o => o.options).length > 0;
    }

    onSelect_(event) {
      this.dispatch('select', this.rootStatePath, event.target.checked,
          OptionGroup.values(event.model.option));
      this.dispatchEvent(new CustomEvent('option-select', {
        bubbles: true,
        composed: true,
      }));
    }
  }

  OptionGroup.properties = {
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
    isRoot: {
      type: Boolean,
      computed: '_eq(statePath, rootStatePath)',
    },
  };

  OptionGroup.values = option => {
    if (option === undefined) return [];
    if (typeof(option) === 'string') return [option];
    if (option.options) {
      const values = [];
      for (const child of option.options) {
        values.push(...OptionGroup.values(child));
      }
      return values;
    }
    if (option.value) return [option.value];
    return [];
  };

  OptionGroup.countDescendents = options => {
    let count = 0;
    for (const option of options) {
      if (option.options) {
        count += OptionGroup.countDescendents(option.options);
      } else {
        count += 1;
      }
    }
    return count;
  };

  OptionGroup.groupValues = names => {
    const options = [];
    for (const name of names) {
      const parts = name.split(':');
      let parent = options;
      for (let i = 0; i < parts.length; ++i) {
        const part = parts[i];

        let found = false;
        for (const option of parent) {
          if (option.label === part) {
            if (i === parts.length - 1) {
              option.options.push({
                label: part,
                value: name,
              });
            } else {
              parent = option.options;
            }
            found = true;
            break;
          }
        }

        if (!found) {
          if (i === parts.length - 1) {
            parent.push({
              label: part,
              value: name,
            });
          } else {
            const option = {
              options: [],
              isExpanded: false,
              label: part,
            };
            parent.push(option);
            parent = option.options;
          }
        }
      }
    }
    return options.map(OptionGroup.simplifyOption);
  };

  OptionGroup.simplifyOption = option => {
    if (!option.options) return option;
    if (option.options.length > 1) {
      return {
        ...option,
        options: option.options.map(OptionGroup.simplifyOption),
      };
    }
    if (option.options[0].options) {
      return OptionGroup.simplifyOption({
        isExpanded: false,
        options: option.options[0].options,
        label: option.label + ':' + option.options[0].label,
        value: option.options[0].value,
      });
    }
    if (option.options[0].label) {
      return {
        ...option.options[0],
        label: option.label + ':' + option.options[0].label,
      };
    }
    return option.options[0];
  };

  OptionGroup.actions = {
    select: (statePath, selected, values) => async (dispatch, getState) => {
      dispatch({
        type: OptionGroup.reducers.select.typeName,
        statePath,
        values,
        selected,
      });
    },
  };

  OptionGroup.reducers = {
    select: cp.ElementBase.statePathReducer((state, action) => {
      let selectedOptions = new Set(state.selectedOptions);
      if (action.selected) {
        for (const value of action.values) {
          selectedOptions.add(value);
        }
      } else {
        for (const value of action.values) {
          selectedOptions.delete(value);
        }
      }
      selectedOptions = [...selectedOptions];
      return {...state, selectedOptions};
    }),
  };

  cp.ElementBase.register(OptionGroup);

  return {
    OptionGroup,
  };
});
