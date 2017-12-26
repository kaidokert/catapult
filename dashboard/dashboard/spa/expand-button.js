/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class ExpandButton extends Polymer.GestureEventListeners(Polymer.Element) {
    static get is() { return 'expand-button'; }

    static get properties() {
      return {
        opened: {
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
        detail: {opened: !this.opened},
      }));
    }

    getIcon_(opened) {
      if (this.after) opened = !opened;
      if (horizontal) return (opened ? 'chevron-left' : 'chevron-right');
      return (opened ? 'expand-less' : 'expand-more');
    }
  }
  customElements.define(ExpandButton.is, ExpandButton);

  return {
    ExpandButton,
  };
});
