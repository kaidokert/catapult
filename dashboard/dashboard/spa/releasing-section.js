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

    onKeydownSource_(event) {
      this.dispatch('keydownSource', this.statePath, event.detail.value);
    }

    onClearSource_() {
      this.dispatch('clearSource', this.statePath);
    }

    onSelectSource_(event) {
      event.cancelBubble = true;
      this.dispatch('selectSource', this.statePath,
          this.source.selectedOptions);
    }

    previousMilestone_() {
      this.dispatch('selectMilestone', this.statePath, this.milestone - 1);
    }

    nextMilestone_() {
      this.dispatch('selectMilestone', this.statePath, this.milestone + 1);
    }

    openChart_(event) {
      this.dispatchEvent(new CustomEvent('new-section', {
        bubbles: true,
        composed: true,
        detail: {
          keepDefaultSection: true,
          type: cp.ChartSection.is,
          options: {
            parameters: event.model.row.chartParameters,
          },
        },
      }));
    }

    addAlertsSection_() {
      this.dispatchEvent(new CustomEvent('new-section', {
        bubbles: true,
        composed: true,
        detail: {
          keepDefaultSection: true,
          type: cp.AlertsSection.is,
          options: {
            sources: this.source.selectedOptions.map(s =>
              `Releasing:M${this.milestone}:${s}`),
          },
        },
      }));
    }

    toggleEditing_() {
      this.dispatch('toggleEditing', this.statePath);
    }
  }

  ReleasingSection.actions = {
    connected: statePath => async (dispatch, getState) => {
      const sourcePath = statePath + '.source';
      const source = Polymer.Path.get(getState(), sourcePath);
      if (source.selectedOptions.length === 0) {
        dispatch(cp.DropdownInput.actions.focus(sourcePath));
      } else {
        dispatch(cp.ElementBase.actions.updateObject(sourcePath, {
          inputValue: source.selectedOptions.join(', '),
        }));

        cp.todo('fetch releasing report');
        dispatch(cp.ElementBase.actions.updateObject(statePath, {
          ...cp.dummyReleasingSection(),
        }));
      }
    },

    selectMilestone: (statePath, milestone) => async (dispatch, getState) => {
      dispatch({
        type: ReleasingSection.reducers.selectMilestone.typeName,
        statePath,
        milestone,
      });
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
          selectedOptions[0] === 'Public') {
        dispatch(cp.ChromeperfApp.actions.updateRoute('', {}));
        return;
      }
      const queryParams = {};
      for (const option of selectedOptions) {
        queryParams[option.replace(' ', '_')] = '';
      }
      dispatch(cp.ChromeperfApp.actions.updateRoute('releasing', queryParams));
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

  ReleasingSection.newStateOptionsFromQueryParams = queryParams => {
    const options = {sources: []};
    for (const [name, value] of Object.entries(queryParams)) {
      options.sources.push(name.replace(/_/g, ' '));
    }
    return options;
  };

  ReleasingSection.newState = options => {
    const sources = options.sources ? options.sources : [];
    return {
      isEditing: false,
      isLoading: false,
      isOwner: false,
      source: {
        placeholder: 'Report',
        inputValue: '',
        selectedOptions: sources,
        options: cp.dummyReleasingSources(),
      },
      milestone: 64,
      isPreviousMilestone: false,
      isNextMilestone: false,
      anyAlerts: false,
    };
  };


  cp.ElementBase.register(ReleasingSection);

  return {
    ReleasingSection,
  };
});
