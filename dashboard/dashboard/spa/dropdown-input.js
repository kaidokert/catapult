/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  function elementIsChildOf(el, potentialParent) {
    if (el === potentialParent) return false;

    let cur = el;
    while (Polymer.dom(cur).parentNode) {
      if (cur === potentialParent) return true;
      cur = Polymer.dom(cur).parentNode;
    }
    return false;
  }

  class DropdownInput extends cp.ElementBase {
    connectedCallback() {
      super.connectedCallback();
      this.onIsFocusedChange_();
    }

    onIsFocusedChange_() {
      if (this.isFocused) {
        this.$.input.focus();
      } else {
        this.$.input.blur();
      }
    }

    isDisabled_(options) {
      return options && options.length === 0;
    }

    isValid_(selectedOptions) {
      if (!this.required) return true;
      if (!this.requireSingle && !this._empty(selectedOptions)) return true;
      if (this.requireSingle && (selectedOptions.length === 1)) return true;
      return false;
    }

    getInputValue_(isFocused, query, selectedOptions) {
      return DropdownInput.inputValue(isFocused, query, selectedOptions);
    }

    onFocus_(event) {
      this.dispatch('focus', this.statePath);
    }

    onBlur_(event) {
      if (event.relatedTarget === this.$.dropdown ||
          elementIsChildOf(event.relatedTarget, this) ||
          elementIsChildOf(event.relatedTarget, this.$.dropdown)) {
        this.$.input.focus();
        return;
      }
      this.dispatch('blur', this.statePath);
    }

    onKeyup_(event) {
      if (this.required) this.$.input.validate();
      if (event.key === 'Escape') {
        this.$.input.blur();
        return;
      }
      this.dispatch('keydown', this.statePath, event.target.value);
      this.dispatchEvent(new CustomEvent('input-keydown', {
        detail: {
          key: event.key,
          value: this.value,
        },
      }));
    }

    onClear_(event) {
      this.dispatch('clear', this.statePath);
      this.dispatchEvent(new CustomEvent('clear'));
      this.dispatchEvent(new CustomEvent('option-select', {
        bubbles: true,
        composed: true,
      }));
    }

    onOptionSelect_(event) {
      this.dispatch('populateMagicOptions', this.statePath);
    }

    isComponentSelected_(option, columnIndex, selectedOptions) {
      return DropdownInput.isComponentSelected(
          option, columnIndex, selectedOptions);
    }

    onComponentSelect_(event) {
      this.dispatch('onComponentSelect', this.statePath,
          event.model.columnIndex, event.model.option);
      this.dispatch('populateMagicOptions', this.statePath);
      this.dispatchEvent(new CustomEvent('option-select', {
        bubbles: true,
        composed: true,
      }));
    }
  }

  DropdownInput.valueHasComponent = (value, columnIndex, component) => {
    const components = value instanceof Array ? value : value.split(':');
    while (components.length < 7) {
      components.splice(components.length - 1, 0, '-');
    }
    return components[columnIndex] === component;
  };

  DropdownInput.isComponentSelected =
    (option, columnIndex, selectedOptions) => {
      if (option === undefined) return false;
      if (selectedOptions === undefined) return false;
      for (const value of selectedOptions) {
        if (DropdownInput.valueHasComponent(value, columnIndex, option)) {
          return true;
        }
      }
      return false;
    };

  DropdownInput.inputValue = (isFocused, query, selectedOptions) => {
    if (isFocused) return query;
    if (selectedOptions === undefined) return '';
    if (selectedOptions.length === 0) return '';
    if (selectedOptions.length === 1) return selectedOptions[0];
    return `[${selectedOptions.length} selected]`;
  };

  DropdownInput.properties = {
    ...cp.ElementBase.statePathProperties('statePath', {
      columns: {type: Array},
      focusTimestamp: {type: Number},
      label: {type: String},
      options: {type: Array},
      query: {type: String},
      required: {type: Boolean},
      requireSingle: {type: Boolean},
      errorMessage: {type: String},
      selectedOptions: {type: Array},
    }),
    rootFocusTimestamp: {
      type: Number,
      statePath: 'focusTimestamp',
    },
    isFocused: {
      type: Boolean,
      computed: '_eq(focusTimestamp, rootFocusTimestamp)',
      observer: 'onIsFocusedChange_',
    },
  };

  DropdownInput.actions = {
    populateMagicOptions: statePath => async(dispatch, getState) => {
      dispatch({
        type: DropdownInput.reducers.populateMagicOptions.typeName,
        statePath,
      });
    },

    focus: inputStatePath => async(dispatch, getState) => {
      dispatch({
        type: DropdownInput.reducers.focus.typeName,
        // NOT "statePath"! ElementBase.statePathReducer would mess that up.
        inputStatePath,
      });
    },

    blurAll: () => async(dispatch, getState) => {
      dispatch({
        type: DropdownInput.reducers.blur.typeName,
        statePath: '',
      });
    },

    blur: statePath => async(dispatch, getState) => {
      dispatch({
        type: DropdownInput.reducers.blur.typeName,
        statePath,
      });
    },

    clear: statePath => async(dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(statePath, {
        query: '',
        selectedOptions: [],
      }));
      dispatch(cp.DropdownInput.actions.focus(statePath));
    },

    keydown: (statePath, query) => async(dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(statePath, {
        query,
      }));
    },

    onComponentSelect: (statePath, columnIndex, option) =>
      async(dispatch, getState) => {
        dispatch({
          type: DropdownInput.reducers.onComponentSelect.typeName,
          statePath,
          columnIndex,
          option,
        });
      },
  };

  DropdownInput.reducers = {
    onComponentSelect: (state, action, rootState) => {
      const selectedOptions = state.selectedOptions.filter(v =>
        !DropdownInput.valueHasComponent(v, action.columnIndex, action.option));
      if (state.selectedOptions.length > selectedOptions.length) {
        return {...state, selectedOptions};
      }
      // Otherwise, add all option values that match the components.
      const selectedColumns = state.columns.map(({options}, colI) =>
        options.filter(option => DropdownInput.isComponentSelected(
            option, colI, selectedOptions)));
      for (const option of state.options) {
        for (const value of cp.OptionGroup.getValuesFromOption(option)) {
          if (selectedOptions.includes(value)) continue;
          let valueMatches = true;
          const components = value.split(':');
          while (components.length < 7) {
            components.splice(components.length - 1, 0, '-');
          }
          for (let colI = 0; colI < state.columns.length; ++colI) {
            let columnMatches = false;
            if (colI === action.columnIndex) {
              columnMatches = DropdownInput.valueHasComponent(
                  components, colI, action.option);
            } else {
              for (const component of selectedColumns[colI]) {
                if (DropdownInput.valueHasComponent(
                    components, colI, component)) {
                  columnMatches = true;
                  break;
                }
              }
            }
            if (!columnMatches) {
              valueMatches = false;
              break;
            }
          }
          if (valueMatches) {
            selectedOptions.push(value);
          }
        }
      }
      return {...state, selectedOptions};
    },

    focus: (rootState, action, rootStateAgain) => {
      const focusTimestamp = window.performance.now();
      rootState = {...rootState, focusTimestamp};
      if (!action.inputStatePath) return rootState; // Blur all dropdown-inputs

      return Polymer.Path.setImmutable(
          rootState, action.inputStatePath, inputState => {
            return {...inputState, focusTimestamp};
          });
    },

    blur: (state, action, rootState) => {
      return {
        ...state,
        focusTimestamp: window.performance.now(),
        query: '',
      };
    },

    populateMagicOptions: (state, action, rootState) => {
      const allOptionValues = [];
      for (const option of state.options) {
        allOptionValues.push(...cp.OptionGroup.getValuesFromOption(option));
      }

      const isExpanded = true;
      const magic = {options: []};
      if (state.selectedOptions.length < (allOptionValues.length / 2) &&
          allOptionValues.length > 10) {
        // Magically display all selected options at the top if there are more
        // unselected options than selected options.
        magic.options.push(...cp.OptionGroup.groupValues(
            state.selectedOptions, isExpanded));
      }

      const getLastComponent = s => s.split(':').slice(-1)[0];
      const lastComponents = new Set(
          state.selectedOptions.map(getLastComponent));
      const isSimilarToSelected = value =>
        !state.selectedOptions.includes(value) &&
        lastComponents.has(getLastComponent(value));

      const similarOptions = cp.OptionGroup.groupValues(
          allOptionValues.filter(isSimilarToSelected), isExpanded);
      if (similarOptions.length > 0) {
        magic.options.push({
          label: '[Similar]',
          options: similarOptions,
          isExpanded: similarOptions.length === 1,
        });
      }

      let anyMemory = false;
      for (const value of state.selectedOptions) {
        if (value.startsWith('memory:')) {
          anyMemory = true;
          break;
        }
      }
      const columns = [];
      if (anyMemory) {
        for (let i = 0; i < 7; ++i) {
          columns.push({options: new Set()});
        }
        for (const value of allOptionValues) {
          if (!value.startsWith('memory:')) continue;
          const components = value.split(':');
          while (components.length < 7) {
            components.splice(components.length - 1, 0, '-');
          }
          for (let i = 0; i < 7; ++i) {
            columns[i].options.add(components[i]);
          }
        }
        for (let i = 0; i < 7; ++i) {
          columns[i].options = [...columns[i].options];
          columns[i].options.sort((a, b) => a.localeCompare(b));
        }
      }

      return {...state, magic, columns};
    },
  };

  cp.ElementBase.register(DropdownInput);

  return {
    DropdownInput,
  };
});
