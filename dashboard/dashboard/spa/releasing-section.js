/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

tr.exportTo('cp', () => {
  class ReleasingSection extends cp.ElementBase {
    static get is() { return 'releasing-section'; }

    static get properties() {
      return cp.ElementBase.statePathProperties('statePath', {
        anyAlerts: {type: Boolean},
        isEditing: {type: Boolean},
        isLoading: {type: Boolean},
        isNextMilestone: {type: Boolean},
        isOwner: {type: Boolean},
        isPreviousMilestone: {type: Boolean},
        milestone: {type: Number},
        sectionId: {type: String},
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
      this.dispatch('focusSource', this.statePath, true);
    }

    onBlurSource_() {
      this.dispatch('focusSource', this.statePath, false);
    }

    onKeydownSource_(e) {
      this.dispatch('keydownSource', this.statePath, e.detail.value);
    }

    onClearSource_() {
      this.dispatch('clearSource', this.statePath);
    }

    onSelectSource_(e) {
      this.dispatch('selectSource', this.statePath, e.detail.selectedOptions);
    }

    previousMilestone_() {
      this.dispatch('selectMilestone', this.statePath, this.milestone - 1);
    }

    nextMilestone_() {
      this.dispatch('selectMilestone', this.statePath, this.milestone + 1);
    }

    openChart_(e) {
      this.dispatch('openChart', e.model.row.testPath);
    }

    addAlertsSection_() {
      this.dispatch('addAlertsSection', this.statePath);
    }

    toggleEditing_() {
      this.dispatch('toggleEditing', this.statePath);
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

  ReleasingSection.actions = {
    selectMilestone: (statePath, milestone) => async (dispatch, getState) => {
      dispatch({
        type: 'releasing-section.selectMilestone',
        statePath,
        milestone,
      });
    },

    openChart: testPath => async (dispatch, getState) => {
      dispatch(cp.ChromeperfApp.actions.keepDefaultSection());
      const sectionId = tr.b.GUID.allocateSimple();
      dispatch({
        type: 'chromeperf-app.newSection',
        sectionType: 'chart-section',
        sectionId,
      });
      for (let i = 0; i < testPath.length; ++i) {
        dispatch(cp.TestPathComponent.actions.select(
            ['sectionsById', sectionId, 'testPathComponents', i],
            testPath[i]));
      }
      dispatch(cp.ChartSection.actions.maybeLoadTimeseries(sectionId));
      dispatch(cp.ChromeperfApp.actions.focus([], false));
    },

    addAlertsSection: statePath => async (dispatch, getState) => {
      const sectionId = tr.b.GUID.allocateSimple();
      dispatch({
        type: 'releasing-section.addAlertsSection',
        sectionId,
      });
      dispatch(cp.ChromeperfApp.actions.updateLocation());
      dispatch(cp.AlertsSection.actions.maybeLayoutPreview(sectionId));
    },

    toggleEditing: statePath => async (dispatch, getState) => {
      dispatch({
        type: 'releasing-section.toggleEditing',
        statePath,
      });
    },

    focusSource: (statePath, isFocused) => async (dispatch, getState) => {
      dispatch(cp.ChromeperfApp.actions.focus(
          statePath.concat(['source']), isFocused));
    },

    keydownSource: (statePath, inputValue) => async (dispatch, getState) => {
      // TODO filter options?
    },

    clearSource: statePath => async (dispatch, getState) => {
      // TODO unfilter options?
    },

    updateLocation: sectionState => async (dispatch, getState) => {
      const state = getState();
      const selectedOptions = sectionState.source.selectedOptions;
      // TODO also save Mstone
      if (state.containsDefaultSection &&
          selectedOptions.length === 1 &&
          selectedOptions[0] === 'Chromeperf Public') {
        dispatch(cp.ChromeperfApp.actions.updateRoute('', {}));
        return;
      }
      const queryParams = {};
      for (const option of selectedOptions) {
        queryParams[option.replace(' ', '_')] = '';
      }
      dispatch(cp.ChromeperfApp.actions.updateRoute('releasing', queryParams));
    },

    restoreFromQueryParams: (statePath, queryParams) =>
      async (dispatch, getState) => {
        const selectedOptions = [];
        for (const param of Object.keys(queryParams)) {
          selectedOptions.push(param.replace('_', ' '));
        }
        dispatch(ReleasingSection.actions.selectSource(
            statePath, selectedOptions));
      },

    selectSource: (statePath, selectedOptions) =>
      async (dispatch, getState) => {
        if (selectedOptions === undefined) return;
        dispatch({
          type: 'releasing-section.selectSource',
          statePath,
          selectedOptions,
        });
        await tr.b.timeout(0);
        dispatch(cp.ChromeperfApp.actions.updateLocation());
      },
  };

  ReleasingSection.reducers = {
    addAlertsSection: (state, action) => {
      const newSection = {
        type: 'alerts-section',
        sectionId: action.sectionId,
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
      sectionsById[newSection.sectionId] = newSection;

      return {
        ...state,
        containsDefaultSection: false,
        sectionsById,
        sectionIds: state.sectionIds.concat([newSection.sectionId]),
      };
    },

    selectSource: cp.ElementBase.updatingReducer((section, action) => {
      return {
        isLoading: false,
        ...cp.dummyReleasingSection(),
        source: {
          ...section.source,
          isFocused: false,
          inputValue: action.selectedOptions.join(', '),
          selectedOptions: action.selectedOptions,
        },
      };
    }),

    toggleEditing: cp.ElementBase.updatingReducer((section, action) => {
      return {isEditing: !section.isEditing};
    }),
  };

  cp.ElementBase.register(ReleasingSection);

  return {
    ReleasingSection,
  };
});
