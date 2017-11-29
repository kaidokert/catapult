/*
Copyright 2017 The Chromium Authors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be
found in the LICENSE file.
*/
'use strict';

tr.exportTo('cp', () => {
  class ReleasingSection extends cp.Element {
    static get is() { return 'releasing-section'; }

    static get properties() {
      return cp.sectionProperties({
        isLoading: {type: Boolean},
        report: {type: String},
        isMenuFocused: {type: Boolean},
        reportOptions: {type: Array},
        milestone: {type: Number},
        isPreviousMilestone: {type: Boolean},
        isNextMilestone: {type: Boolean},
        tables: {type: Array},
        anyAlerts: {type: Boolean},
      });
    }

    async ready() {
      super.ready();
      this.scrollIntoView(true);
      this.dispatch(cp.ChromeperfApp.updateSectionWidth(this));
    }

    closeSection_() {
      this.dispatch(cp.ChromeperfApp.closeSection(this.sectionId));
    }

    onMenuFocus_() {
      this.dispatch(ReleasingSection.focusMenu(this.sectionId, true));
    }

    onMenuBlur_() {
      this.dispatch(ReleasingSection.focusMenu(this.sectionId, false));
    }

    static focusMenu(sectionId, isMenuFocused) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'releasing-section.focusMenu',
          sectionId,
          isMenuFocused,
        });
      };
    }

    onMenuKeydown_(e) {
      this.dispatch(ReleasingSection.keydownMenu(this.sectionId, e.detail.value));
    }

    static keydownMenu(sectionId, report) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'releasing-section.keydownMenu',
          sectionId,
          report,
        });
      };
    }

    onMenuClear_() {
      this.dispatch(ReleasingSection.clearMenu(this.sectionId));
    }

    static clearMenu(sectionId) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'releasing-section.clearMenu',
          sectionId,
        });
      };
    }

    onMenuSelect_() {
      this.dispatch(ReleasingSection.selectReport(
          this.sectionId, this.$.menu.value));
    }

    static selectReport(sectionId, report) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'releasing-section.selectReport',
          sectionId,
          report,
        });
      };
    }

    previousMilestone_() {
      this.dispatch(ReleasingSection.selectMilestone(
          this.sectionId, this.milestone - 1));
    }

    nextMilestone_() {
      this.dispatch(ReleasingSection.selectMilestone(
          this.sectionId, this.milestone + 1));
    }

    static selectMilestone(sectionId, milestone) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'releasing-section.selectMilestone',
          sectionId,
          milestone,
        });
      };
    }

    addAlertsSection_() {
      this.dispatch(ReleasingSection.addAlertsSection(this.sectionId));
    }

    static addAlertsSection(sectionId) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'releasing-section.addAlertsSection',
          sectionId,
        });
      };
    }
  }
  customElements.define(ReleasingSection.is, ReleasingSection);

  const DUMMY_RELEASING_SECTION = {
    type: 'releasing',
    report: 'Chromeperf Public',
    isLoading: false,
    isMenuFocused: false,
    reportOptions: [
      'Chromeperf Public',
      'Loading',
      'Input',
      'Memory',
      'Battery',
    ],
    milestone: 64,
    isPreviousMilestone: true,
    isNextMilestone: false,
    anyAlerts: true,
    tables: [
      {
        title: 'health-plan-clankium-phone',
        currentVersion: '517411-73a',
        referenceVersion: '508578-c23',
        rows: [
          {
            isFirstInCategory: true,
            rowCount: 4,
            evenCategory: false,
            category: 'Foreground',
            href: '#',
            name: 'Java Heap',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Native Heap',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Ashmem',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Overall PSS',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: true,
            rowCount: 4,
            evenCategory: true,
            category: 'Background',
            href: '#',
            name: 'Java Heap',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Native Heap',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Ashmem',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Overall PSS',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
        ],
      },
      {
        title: 'health-plan-clankium-low-end-phone',
        currentVersion: '517411-73a',
        referenceVersion: '508578-c23',
        rows: [
          {
            isFirstInCategory: true,
            rowCount: 4,
            evenCategory: false,
            category: 'Foreground',
            href: '#',
            name: 'Java Heap',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Native Heap',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Ashmem',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Overall PSS',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: true,
            rowCount: 4,
            evenCategory: true,
            category: 'Background',
            href: '#',
            name: 'Java Heap',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Native Heap',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Ashmem',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Overall PSS',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
        ],
      },
    ],
  };

  /**
   * @param {Number} action.sectionId
   * @param {Boolean} action.isMenuFocused
   */
  cp.REDUCERS.set('releasing-section.focusMenu', (state, action) => {
    return cp.assignSection(state, action.sectionId, {
      isMenuFocused: action.isMenuFocused,
    });
  });

  /**
   * @param {Number} action.sectionId
   * @param {String} action.report
   */
  cp.REDUCERS.set('releasing-section.selectReport', (state, action) => {
    return cp.assignSection(state, action.sectionId, DUMMY_RELEASING_SECTION);
  });

  /**
   * @param {Number} action.sectionId
   */
  cp.REDUCERS.set('releasing-section.clearMenu', (state, action) => {
    return cp.assignSection(state, action.sectionId, {
      report: '',
      isMenuFocused: true,
    });
  });

  /**
   * @param {Number} action.sectionId
   * @param {String} action.report
   */
  cp.REDUCERS.set('releasing-section.keydownMenu', (state, action) => {
    return cp.assignSection(state, action.sectionId, {
      report: action.report,
      isMenuFocused: true,
    });
  });

  return {
    ReleasingSection,
  };
});
