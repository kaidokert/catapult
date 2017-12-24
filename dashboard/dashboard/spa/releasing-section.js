/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

tr.exportTo('cp', () => {
  class ReleasingSection extends cp.Element {
    static get is() { return 'releasing-section'; }

    static get properties() {
      return cp.buildProperties('section', {
        anyAlerts: {type: Boolean},
        isEditing: {type: Boolean},
        isLoading: {type: Boolean},
        isNextMilestone: {type: Boolean},
        isOwner: {type: Boolean},
        isPreviousMilestone: {type: Boolean},
        milestone: {type: Number},
        source: {type: Object},
        tables: {type: Array},
      });
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

    ready() {
      super.ready();
      this.scrollIntoView(true);
    }

    closeSection_() {
      this.dispatch(cp.ChromeperfApp.actions.closeSection(this.sectionId));
    }

    onFocusSource_() {
      this.dispatch('focusSource', this.sectionId, true);
    }

    onBlurSource_() {
      this.dispatch('focusSource', this.sectionId, false);
    }

    onKeydownSource_(e) {
      this.dispatch('keydownSource', this.sectionId, e.detail.value);
    }

    onClearSource_() {
      this.dispatch('clearSource', this.sectionId);
    }

    onSelectSource_(e) {
      this.dispatch('selectSource', this.sectionId, e.detail.selectedOptions);
    }

    previousMilestone_() {
      this.dispatch('selectMilestone', this.sectionId, this.milestone - 1);
    }

    nextMilestone_() {
      this.dispatch('selectMilestone', this.sectionId, this.milestone + 1);
    }

    openChart_(e) {
      this.dispatch('openChart', e.model.row.testPath);
    }

    addAlertsSection_() {
      this.dispatch('addAlertsSection', this.sectionId);
    }

    toggleEditing_() {
      this.dispatch('toggleEditing', this.sectionId);
    }
  }

  ReleasingSection.NEW_STATE = {
    isEditing: false,
    isLoading: false,
    isOwner: false,
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
    isOwner: Math.random() < 0.5,
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
            category: 'Foreground',
            href: '#',
            name: 'Java Heap',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
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
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
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
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
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
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
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
            category: 'Background',
            href: '#',
            name: 'Java Heap',
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
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
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
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
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
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
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
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
            category: 'Foreground',
            href: '#',
            name: 'Java Heap',
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
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
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
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
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
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
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
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
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
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
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
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
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
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
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
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

  ReleasingSection.actions = {
    selectMilestone: (sectionId, milestone) => async (dispatch, getState) => {
      dispatch({
        type: 'releasing-section.selectMilestone',
        sectionId,
        milestone,
      });
    },

    openChart: testPath => async (dispatch, getState) => {
      dispatch({type: 'chromeperf-app.keepDefaultSection'});
      const sectionId = tr.b.GUID.allocateSimple();
      dispatch({
        type: 'chromeperf-app.newSection',
        sectionType: 'chart-section',
        sectionId,
      });
      for (let i = 0; i < testPath.length; ++i) {
        dispatch({
          type: 'test-path-component.select',
          sectionId,
          componentIndex: i,
          selectedOptions: testPath[i],
        });
      }
      dispatch(cp.ChartSection.actions.maybeLoadTimeseries(sectionId));
      dispatch({type: 'chromeperf-app.clearAllFocused'});
    },

    addAlertsSection: sectionId => async (dispatch, getState) => {
      const sectionId = tr.b.GUID.allocateSimple();
      dispatch({
        type: 'releasing-section.addAlertsSection',
        sectionId,
      });
      dispatch(cp.ChromeperfApp.actions.updateLocation());
      dispatch(cp.AlertsSection.maybeLayoutPreview(sectionId));
    },

    toggleEditing: sectionId => async (dispatch, getState) => {
      dispatch({
        type: 'releasing-section.toggleEditing',
        sectionId,
      });
    },

    focusSource: (sectionId, isFocused) => async (dispatch, getState) => {
      dispatch({
        type: 'releasing-section.focusSource',
        sectionId,
        isFocused,
      });
    },

    keydownSource: (sectionId, inputValue) => async (dispatch, getState) => {
      dispatch({
        type: 'releasing-section.keydownSource',
        sectionId,
        inputValue,
      });
    },

    clearSource: sectionId => async (dispatch, getState) => {
      dispatch({
        type: 'releasing-section.clearSource',
        sectionId,
      });
    },

    updateLocation: sectionState => async (dispatch, getState) => {
      const state = getState();
      const selectedOptions = sectionState.source.selectedOptions;
      // TODO also save Mstone
      if (state.containsDefaultSection &&
          selectedOptions.length === 1 &&
          selectedOptions[0] === 'Chromeperf Public') {
        dispatch(cp.ChromeperfApp.updateRoute('', {}));
        return;
      }
      const queryParams = {};
      for (const option of selectedOptions) {
        queryParams[option.replace(' ', '_')] = '';
      }
      dispatch(cp.ChromeperfApp.updateRoute('releasing', queryParams));
    },

    restoreFromQueryParams: (sectionId, queryParams) =>
      async (dispatch, getState) => {
        const selectedOptions = [];
        for (const param of Object.keys(queryParams)) {
          selectedOptions.push(param.replace('_', ' '));
        }
        dispatch(ReleasingSection.selectSource(sectionId, selectedOptions));
      },

    selectSource: (sectionId, selectedOptions) =>
      async (dispatch, getState) => {
        if (selectedOptions === undefined) return;
        dispatch({
          type: 'releasing-section.selectSource',
          sectionId,
          selectedOptions,
        });
        dispatch(cp.ChromeperfApp.actions.updateLocation());
      },
  };

  ReleasingSection.reducers = {
    focusSource: (state, action) => {
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
    },

    addAlertsSection: (state, action) => {
      const newSection = {
        type: 'alerts-section',
        id: action.sectionId,
        ...cp.AlertsSection.NEW_STATE,
        areAlertGroupsPlaceholders: false,
        summary: '6 alerts in 3 groups',
        isPreviewing: true,
        selectedAlertsCount: 1,
        alertGroups: [
          {
            isExpanded: false,
            alerts: [
              {
                guid: tr.b.GUID.allocateSimple(),
                isSelected: true,
                revisions: '543210 - 543221',
                bot: 'nexus5X',
                testSuite: 'system_health.common_mobile',
                measurement: 'story:power_avg',
                story: 'load:chrome:blank',
                deltaValue: 1,
                deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
                percentDeltaValue: 1,
                percentDeltaUnit:
                  tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
              },
            ],
          },
          {
            isExpanded: false,
            alerts: [
              {
                guid: tr.b.GUID.allocateSimple(),
                isSelected: false,
                revisions: '543222 - 543230',
                bot: 'nexus5X',
                testSuite: 'system_health.common_mobile',
                measurement: 'story:power_avg',
                story: 'load:chrome:blank',
                deltaValue: 1,
                deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
                percentDeltaValue: 1,
                percentDeltaUnit:
                  tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
              },
            ],
          },
          {
            isExpanded: false,
            alerts: [
              {
                guid: tr.b.GUID.allocateSimple(),
                isSelected: false,
                revisions: '543210 - 543221',
                bot: 'nexus5X',
                testSuite: 'system_health.common_mobile',
                measurement: 'story:power_avg',
                story: 'load:chrome:blank',
                deltaValue: 1,
                deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
                percentDeltaValue: 1,
                percentDeltaUnit:
                  tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
              },
              {
                guid: tr.b.GUID.allocateSimple(),
                isSelected: false,
                revisions: '543210 - 543221',
                bot: 'nexus5X',
                testSuite: 'system_health.common_mobile',
                measurement: 'story:power_avg',
                story: 'load:chrome:blank',
                deltaValue: 1,
                deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
                percentDeltaValue: 1,
                percentDeltaUnit:
                  tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
              },
              {
                guid: tr.b.GUID.allocateSimple(),
                isSelected: false,
                revisions: '543210 - 543221',
                bot: 'nexus5X',
                testSuite: 'system_health.common_mobile',
                measurement: 'story:power_avg',
                story: 'load:chrome:blank',
                deltaValue: 1,
                deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
                percentDeltaValue: 1,
                percentDeltaUnit:
                  tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
              },
              {
                guid: tr.b.GUID.allocateSimple(),
                isSelected: false,
                revisions: '543240 - 543250',
                bot: 'nexus5X',
                testSuite: 'system_health.common_mobile',
                measurement: 'story:power_avg',
                story: 'load:chrome:blank',
                deltaValue: 1,
                deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
                percentDeltaValue: 1,
                percentDeltaUnit:
                  tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
              },
            ],
          },
        ],
      };
      newSection.source = {
        ...newSection.source,
        inputValue: 'Releasing Public M64',
        isFocused: false,
        selectedOptions: ['Releasing Public M64'],
        options: [
          {...newSection.source.options[0]},
          {
            ...newSection.source.options[1],
            isExpanded: false,
          },
          {
            ...newSection.source.options[2],
            isExpanded: true,
            children: [
              {
                ...newSection.source.options[2].children[0],
              },
              {
                ...newSection.source.options[2].children[1],
                isExpanded: true,
              },
            ],
          },
        ],
      };
      const sectionsById = {...state.sectionsById};
      sectionsById[newSection.id] = newSection;

      return {
        ...state,
        containsDefaultSection: false,
        sectionsById,
        sectionIds: state.sectionIds.concat([newSection.id]),
      };
    },

    selectSource: cp.sectionReducer((section, action) => {
      return {
        ...DUMMY_RELEASING_SECTION,
        source: {
          ...section.source,
          isFocused: false,
          inputValue: action.selectedOptions.join(', '),
          selectedOptions: action.selectedOptions,
        },
      };
    }),

    clearSource: cp.sectionReducer((section, action) => {
      return {
        source: {
          ...section.source,
          inputValue: '',
          selectedOptions: [],
          isFocused: true,
        },
      };
    }),

    keydownSource: cp.sectionReducer((section, action) => {
      return {
        source: {
          ...section.source,
          inputValue: action.inputValue,
          selectedOptions: [],
          isFocused: true,
        },
      };
    }),

    toggleEditing: cp.sectionReducer((section, action) => {
      return {isEditing: !section.isEditing};
    }),
  };

  cp.Element.register(ReleasingSection);

  return {
    ReleasingSection,
  };
});
