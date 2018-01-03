/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class ExpandButton extends Polymer.GestureEventListeners(cp.ElementBase) {
    static get is() { return 'expand-button'; }

    static get properties() {
      return {
        isExpanded: {
          type: Boolean,
          value: false,
        },
        horizontal: {
          type: Boolean,
          value: false,
        },
        after: {
          type: Boolean,
          value: false,
        },
      };
    }

    toggle_(event) {
      this.dispatchEvent(new CustomEvent('toggle', {
        bubbles: true,
        composed: true,
        detail: {isExpanded: !this.isExpanded},
      }));
    }

    getIcon_(isExpanded) {
      if (this.after) isExpanded = !isExpanded;
      if (this.horizontal) {
        return (isExpanded ? 'chevron-left' : 'chevron-right');
      }
      return (isExpanded ? 'expand-less' : 'expand-more');
    }
  }

  cp.ElementBase.register(ExpandButton);

  return {
    ExpandButton,
  };
});
