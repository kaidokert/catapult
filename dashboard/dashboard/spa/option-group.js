/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class OptionGroup extends cp.ElementBase {
    shouldStampSubOptions_(option, query) {
      if (!option) return false;
      if (!option.options) return false;
      if (option.options.length < 20) return true;
      return this.isExpanded_(option, query);
    }

    isExpanded_(option, query) {
      // Expand all groups after the user has entered a query, but don't expand
      // everything as soon as the user starts typing.
      return (query && (query.length > 1)) || (option && option.isExpanded);
    }

    matches_(option, query) {
      if (!query) return true;
      return OptionGroup.matches(option, query.toLocaleLowerCase().split(' '));
    }

    countDescendents_(options) {
      return OptionGroup.countDescendents(options);
    }

    isSelected_(option, selectedOptions) {
      if (!option || !selectedOptions) return false;
      for (const value of OptionGroup.getValuesFromOption(option)) {
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
      return !this.isRoot_() || OptionGroup.getAnyGroups(this.options);
    }

    isRoot_() {
      return this.statePath === this.rootStatePath;
    }

    async onSelect_(event) {
      await this.dispatch('select', this.rootStatePath, event.model.option);
      this.dispatchEvent(new CustomEvent('option-select', {
        bubbles: true,
        composed: true,
      }));
    }
  }

  OptionGroup.getAnyGroups = options =>
    (options || []).filter(o => o.options).length > 0;

  OptionGroup.matches = (option, queryParts) => {
    if (option.options) {
      for (const suboption of option.options) {
        if (OptionGroup.matches(suboption, queryParts)) return true;
      }
      return false;
    }
    if (option.valueLowerCase) {
      option = option.valueLowerCase;
    } else if (option.value) {
      option = option.value;
    } else {
      option = option.toLocaleLowerCase();
    }
    for (const part of queryParts) {
      if (!option.includes(part)) return false;
    }
    return true;
  };

  OptionGroup.State = {
    options: options => options.options || [],
  };

  OptionGroup.RootState = {
    selectedOptions: options => options.selectedOptions || [],
  };

  OptionGroup.buildState = options => {
    return {
      ...cp.buildState(State, options),
      ...cp.buildState(RootState, options),
    };
  };

  OptionGroup.properties = {
    ...cp.buildProperties('state', State),
    ...cp.buildProperties('rootState', RootState),
  };

  OptionGroup.getValuesFromOption = option => {
    if (option === undefined) return [];
    if (typeof(option) === 'string') return [option];
    if (option.options) {
      const values = [];
      if (option.value) {
        values.push(option.value);
      }
      for (const child of option.options) {
        values.push(...OptionGroup.getValuesFromOption(child));
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
        if (option.value) {
          count += 1;
        }
      } else {
        count += 1;
      }
    }
    return count;
  };

  OptionGroup.groupValues = (names, isExpanded) => {
    isExpanded = isExpanded || false;
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
                isExpanded,
                label: part,
                options: [],
                value: name,
                valueLowerCase: name.toLocaleLowerCase(),
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
              isExpanded,
              label: part,
              options: [],
              value: name,
              valueLowerCase: name.toLocaleLowerCase(),
            });
          } else {
            const option = {
              isExpanded,
              label: part,
              options: [],
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
    if (!option.options) {
      return option;
    }
    if (option.options.length === 0) {
      return {
        label: option.label,
        value: option.value,
        valueLowerCase: option.valueLowerCase,
      };
    }
    if (option.options.length > 1 ||
        option.value) {
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
        valueLowerCase: option.options[0].valueLowerCase,
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
    select: (statePath, option) => async(dispatch, getState) => {
      dispatch({
        type: OptionGroup.reducers.select.typeName,
        statePath,
        option,
      });
    },
  };

  OptionGroup.reducers = {
    select: (state, action, rootState) => {
      const selectedOptions = new Set(state.selectedOptions);

      // action.option is either
      // a string to toggle
      // OR an object without an array of sub options but with a value to toggle
      // OR an object without a value but with an array of sub options to toggle
      // collectively
      // OR an object with both a value and an array of sub options; use
      // tristate logic to toggle either the value or the sub options.

      let value;
      if (typeof(action.option) === 'string') {
        value = action.option;
      } else if (action.option.value &&
          (!action.option.options ||
           !selectedOptions.has(action.option.value))) {
        value = action.option.value;
      } else {
        const values = OptionGroup.getValuesFromOption(action.option);
        const selectedValues = values.filter(value =>
          value !== action.option.value && selectedOptions.has(value));
        if (selectedValues.length > 0) {
          for (const value of values) selectedOptions.delete(value);
        } else {
          for (const value of values) selectedOptions.add(value);
        }
      }

      if (value) {
        if (selectedOptions.has(value)) {
          selectedOptions.delete(value);
        } else {
          selectedOptions.add(value);
        }
      }
      return {...state, selectedOptions: [...selectedOptions]};
    },
  };

  cp.ElementBase.register(OptionGroup);

  return {
    OptionGroup,
  };
});
