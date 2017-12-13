/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class PivotSection extends cp.Element {
    static get is() { return 'pivot-section'; }

    static get properties() {
      return cp.sectionProperties({
        benchmark: {type: Object},
        bot: {type: Object},
        revisions: {type: Object},
        histograms: {type: Object},
      });
    }

    closeSection_() {
      this.dispatch(cp.ChromeperfApp.closeSection(this.sectionId));
    }

    static clearAllFocused(sectionState) {
      return {
        ...sectionState,
        benchmark: {
          ...sectionState.benchmark,
          isFocused: false,
        },
        bot: {
          ...sectionState.bot,
          isFocused: false,
        },
        revisions: {
          ...sectionState.revisions,
          isFocused: false,
        },
      };
    }
  }
  customElements.define(PivotSection.is, PivotSection);

  return {
    PivotSection,
  };
});
