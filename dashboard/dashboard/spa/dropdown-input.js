/*
Copyright 2017 The Chromium Authors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be
found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class DropdownInput extends Polymer.Element {
    static get is() { return 'dropdown-input'; }

    static get properties() {
      return {
        placeholder: {
          type: String,
          value: '',
        },

        disabled: {
          type: Boolean,
          value: false,
        },

        inputValue: {
          type: String,
          value: '',
        },

        options: {
          type: Array,
          value: [],
        },

        selectedOptions: {
          type: Array,
          value: [],
        },

        isFocused: {
          type: Boolean,
          value: false,
          observer: 'onIsFocusedChange_',
        }
      };
    }

    onIsFocusedChange_() {
      if (this.isFocused) {
        this.$.input.focus();
      } else {
        this.$.input.blur();
      }
    }

    connectedCallback() {
      super.connectedCallback();
      if (this.isFocused) {
        this.$.input.focus();
      } else {
        this.$.input.blur();
      }
    }

    visibleOptions_(options) {
      return DropdownInput.getVisibleOptions(this.options);
    }

    static getVisibleOptionsInternal_(options, depth, path) {
      const visibleOptions = [];
      for (let optionIndex = 0; optionIndex < options.length; ++optionIndex) {
        const option = options[optionIndex];
        if (!option.children) {
          if (typeof option === 'string') {
            visibleOptions.push({
              label: option,
              value: option,
              depth,
              path: path.concat([optionIndex]),
            });
          } else {
            visibleOptions.push({
              ...option,
              depth,
              path: path.concat([optionIndex]),
            });
          }
          continue;
        }
        visibleOptions.push({
          ...option,
          isGroupHeader: true,
          count: option.children.length,
          depth,
          path: path.concat([optionIndex]),
        });
        if (option.isExpanded) {
          visibleOptions.push.apply(visibleOptions,
            DropdownInput.getVisibleOptionsInternal_(
              option.children,
              depth + 1,
              path.concat([optionIndex])));
        }
      }
      return visibleOptions;
    }

    static getVisibleOptions(options) {
      return DropdownInput.getVisibleOptionsInternal_(options, 0, []);
    }

    onInputFocus_(e) {
      this.dispatchEvent(new CustomEvent('input-focus'));
    }

    onInputBlur_(e) {
      if (e.relatedTarget === null) {
        // TODO or if e.relatedTarget is an element outside of dropdown_scroll
        this.dispatchEvent(new CustomEvent('input-blur'));
      }
    }

    onInputKeydown_(e) {
      this.dispatchEvent(new CustomEvent('input-keydown', {
        detail: {
          key: e.key,
          value: this.value,
        },
      }));
    }

    onInputClear_(e) {
      this.dispatchEvent(new CustomEvent('clear'));
    }

    onDropdownSelect_(e) {
      this.dispatchEvent(new CustomEvent('option-select', {
        detail: {selectedOptions: e.target.selectedValues},
      }));
    }

    toggleGroupExpanded_(e) {
      console.log(e.model.option.path);
      this.dispatchEvent(new CustomEvent('toggle-group-expanded', {
        detail: {path: e.model.option.path},
      }));
    }

    static toggleGroupExpanded(options, path) {
      if (path.length === 1) {
        return cp.assignInArray(options, path[0], {
          isExpanded: !options[path[0]].isExpanded,
        });
      }
      return cp.assignInArray(options, path[0], {
        children: DropdownInput.toggleGroupExpanded(
          options[path[0]].children, path.slice(1)),
      });
    }
  }
  customElements.define(DropdownInput.is, DropdownInput);

  return {
    DropdownInput,
  };
});
