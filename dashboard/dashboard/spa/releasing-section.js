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
        menu: {type: Object},
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

    static focusMenu(sectionId, isFocused) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'releasing-section.focusMenu',
          sectionId,
          isFocused,
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
          this.sectionId, this.$.menu.selectedOptions));
    }

    static selectReport(sectionId, selectedOptions) {
      return async (dispatch, getState) => {
        if (selectedOptions === undefined) return;
        dispatch({
          type: 'releasing-section.selectReport',
          sectionId,
          selectedOptions,
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

  ReleasingSection.NEW_STATE = {
    isLoading: false,
    menu: {
      isFocused: true,
      inputValue: '',
      selectedOptions: [],
      options: [
        'Chromeperf Public',
        'Loading',
        'Input',
        'Memory',
        'Battery',
      ],
    },
    milestone: 64,
    isPreviousMilestone: false,
    isNextMilestone: false,
    anyAlerts: false,
  };

  const DUMMY_RELEASING_SECTION = {
    type: 'releasing',
    isLoading: false,
    menu: {
      isFocused: false,
      inputValue: 'Chromeperf Public',
      selectedOptions: ['Chromeperf Public'],
      options: [
        'Chromeperf Public',
        'Loading',
        'Input',
        'Memory',
        'Battery',
      ],
    },
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

  cp.sectionReducer('releasing-section.focusMenu', (state, action, section) => {
    return {
      menu: cp.assign(section.menu, {
        isFocused: action.isFocused,
      }),
    };
  });

  cp.sectionReducer('releasing-section.selectReport', (state, action, section) => {
    return DUMMY_RELEASING_SECTION;
  });

  cp.sectionReducer('releasing-section.clearMenu', (state, action, section) => {
    return {
      report: '',
      isMenuFocused: true,
    };
  });

  cp.sectionReducer('releasing-section.keydownMenu', (state, action, section) => {
    return {
      report: action.report,
      isMenuFocused: true,
    };
  });

  return {
    ReleasingSection,
  };
});
