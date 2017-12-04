/* Copyright 2017 The Chromium Authors. All rights reserved.
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
        source: {type: Object},
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

    onFocusSource_() {
      this.dispatch(ReleasingSection.focusSource(this.sectionId, true));
    }

    onBlurSource_() {
      this.dispatch(ReleasingSection.focusSource(this.sectionId, false));
    }

    static focusSource(sectionId, isFocused) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'releasing-section.focusSource',
          sectionId,
          isFocused,
        });
      };
    }

    onKeydownSource_(e) {
      this.dispatch(ReleasingSection.keydownSource(
          this.sectionId, e.detail.value));
    }

    static keydownSource(sectionId, inputValue) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'releasing-section.keydownSource',
          sectionId,
          inputValue,
        });
      };
    }

    onClearSource_() {
      this.dispatch(ReleasingSection.clearSource(this.sectionId));
    }

    static clearSource(sectionId) {
      return async (dispatch, getState) => {
        dispatch({
          type: 'releasing-section.clearSource',
          sectionId,
        });
      };
    }

    onSelectSource_() {
      this.dispatch(ReleasingSection.selectSource(
          this.sectionId, this.$.source.selectedOptions));
    }

    static selectSource(sectionId, selectedOptions) {
      return async (dispatch, getState) => {
        if (selectedOptions === undefined) return;
        dispatch({
          type: 'releasing-section.selectSource',
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

    static clearAllFocused(sectionState) {
      return {
        ...sectionState,
        source: {
          ...sectionState.source,
          isFocused: false,
        },
      };
    }
  }
  customElements.define(ReleasingSection.is, ReleasingSection);

  ReleasingSection.NEW_STATE = {
    isLoading: false,
    source: {
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
    isLoading: false,
    source: {
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
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
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
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
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
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
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
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
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
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
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
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
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
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
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
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
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
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
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
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
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
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
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
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
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
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
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
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
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
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
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
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
        ],
      },
    ],
  };

  cp.REDUCERS.set('releasing-section.focusSource', (state, action) => {
    const sectionsById = cp.ChromeperfApp.clearAllFocused(state.sectionsById);
    const section = sectionsById[action.sectionId];
    sectionsById[action.sectionId] = {
      ...section,
      source: {
        ...section.source,
        isFocused: action.isFocused,
      },
    };
    return {...state, sectionsById};
  });

  cp.sectionReducer('releasing-section.selectSource',
      (state, action, section) => DUMMY_RELEASING_SECTION);

  cp.sectionReducer('releasing-section.clearSource',
      (state, action, section) => {
        return {
          source: {
            ...section.source,
            inputValue: '',
            selectedOptions: [],
            isFocused: true,
          },
        };
      });

  cp.sectionReducer('releasing-section.keydownSource',
      (state, action, section) => {
        return {
          source: {
            ...section.source,
            inputValue,
            selectedOptions: [],
            isFocused: true,
          },
        };
      });

  return {
    ReleasingSection,
  };
});
