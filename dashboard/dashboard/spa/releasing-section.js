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

    ready() {
      super.ready();
      this.scrollIntoView(true);
    }

    connectedCallback() {
      super.connectedCallback();
      this.dispatch('connected', this.statePath);
    }

    closeSection_() {
      this.dispatchEvent(new CustomEvent('close-section', {
        bubbles: true,
        composed: true,
        detail: {sectionId: this.sectionId},
      }));
    }

    onKeydownSource_(e) {
      this.dispatch('keydownSource', this.statePath, e.detail.value);
    }

    onClearSource_() {
      this.dispatch('clearSource', this.statePath);
    }

    onSelectSource_(e) {
      e.cancelBubble = true;
      this.dispatch(
          'selectSource', this.statePath, this.source.selectedOptions);
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
      // TODO dispatchEvent instead, let chromeperf-app do this.
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
      placeholder: 'Report',
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
    connected: statePath => async (dispatch, getState) => {
      const sourcePath = statePath + '.source';
      const source = Polymer.Path.get(getState(), sourcePath);
      if (source.selectedOptions.length === 0) {
        dispatch(cp.DropdownInput.actions.focus(sourcePath));
      }
    },

    selectMilestone: (statePath, milestone) => async (dispatch, getState) => {
      dispatch({
        type: ReleasingSection.reducers.selectMilestone.typeName,
        statePath,
        milestone,
      });
    },

    openChart: testPath => async (dispatch, getState) => {
      dispatch(cp.ChromeperfApp.actions.keepDefaultSection());
      const sectionId = tr.b.GUID.allocateSimple();
      dispatch({
        type: ChromeperfApp.reducers.newSection.typeName,
        sectionType: ChartSection.is,
        sectionId,
      });
      for (let i = 0; i < testPath.length; ++i) {
        dispatch(cp.TestPathComponent.actions.select(
            `sectionsById.${sectionId}.testPathComponents.${i}`,
            testPath[i]));
      }
      dispatch(cp.ChartSection.actions.maybeLoadTimeseries(
          `sectionsById.${sectionId}`));
      dispatch(cp.DropdownInput.actions.blurAll());
    },

    addAlertsSection: statePath => async (dispatch, getState) => {
      const sectionId = tr.b.GUID.allocateSimple();
      dispatch({
        type: ReleasingSection.reducers.addAlertsSection.typeName,
        sectionId,
      });
      dispatch(cp.ChromeperfApp.actions.updateLocation());
      dispatch(cp.AlertsSection.actions.maybeLayoutPreview(
          `sectionsById.${sectionId}`));
    },

    toggleEditing: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.toggleBoolean(
          `${statePath}.isEditing`));
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
          type: ReleasingSection.reducers.selectSource.typeName,
          statePath,
          selectedOptions,
        });
        // ChromeperfApp.ready calls this as soon as it is registered in
        // customElements. Wait a tick for tr.exportTo() to finish exporting
        // cp.ChromeperfApp.
        await tr.b.timeout(0);
        dispatch(cp.ChromeperfApp.actions.updateLocation());
      },
  };

  ReleasingSection.reducers = {
    addAlertsSection: (state, action) => {
      const newSection = {
        type: cp.AlertsSection.is,
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
            options: [
              {
                ...newSection.source.options[2].options[0],
              },
              {
                ...newSection.source.options[2].options[1],
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

    selectSource: cp.ElementBase.statePathReducer((state, action) => {
      return {
        ...state,
        isLoading: false,
        ...cp.dummyReleasingSection(),
        source: {
          ...state.source,
          inputValue: action.selectedOptions.join(', '),
          selectedOptions: action.selectedOptions,
        },
      };
    }),
  };

  cp.ElementBase.register(ReleasingSection);

  return {
    ReleasingSection,
  };
});
