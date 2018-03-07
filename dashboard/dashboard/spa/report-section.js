/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

tr.exportTo('cp', () => {
  class ReportSection extends cp.ElementBase {
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

    onSelectSource_(event) {
      event.cancelBubble = true;
      this.dispatch('loadReports', this.statePath);
    }

    previousMilestone_() {
      this.dispatch('selectMilestone', this.statePath, this.milestone - 1);
    }

    nextMilestone_() {
      this.dispatch('selectMilestone', this.statePath, this.milestone + 1);
    }

    openChart_(event) {
      this.dispatchEvent(new CustomEvent('new-chart', {
        bubbles: true,
        composed: true,
        detail: {
          options: {
            parameters: event.model.row.chartParameters,
          },
        },
      }));
    }

    addAlertsSection_() {
      this.dispatchEvent(new CustomEvent('alerts', {
        bubbles: true,
        composed: true,
        detail: {
          options: {
            sources: this.source.selectedOptions.map(s =>
              `Report:M${this.milestone}:${s}`),
          },
        },
      }));
    }

    toggleEditing_() {
      this.dispatch('toggleEditing', this.statePath);
    }
  }

  ReportSection.properties = cp.ElementBase.statePathProperties(
      'statePath', {
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

  ReportSection.DEFAULT_SOURCE = 'ChromiumPerfPublicReport';

  ReportSection.actions = {
    connected: statePath => async (dispatch, getState) => {
      dispatch(ReportSection.actions.loadSources(statePath));
      const rootState = getState();
      const state = Polymer.Path.get(rootState, statePath);
      if (state.source.selectedOptions.length > 0) {
        dispatch(ReportSection.actions.loadReports(statePath));
      } else {
        dispatch(cp.DropdownInput.actions.focus(statePath + '.source'));
      }
    },

    selectMilestone: (statePath, milestone) => async (dispatch, getState) => {
      dispatch({
        type: ReportSection.reducers.selectMilestone.typeName,
        statePath,
        milestone,
      });
    },

    restoreState: (statePath, options) => async (dispatch, getState) => {
      dispatch({
        type: ReportSection.reducers.restoreState.typeName,
        statePath,
        options,
      });
    },

    toggleEditing: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.toggleBoolean(
          `${statePath}.isEditing`));
    },

    loadSources: statePath => async (dispatch, getState) => {
      const rootState = getState();
      const request = new cp.ReportNamesRequest({
        headers: rootState.authHeaders,
      });
      const sources = await request.response;
      dispatch({
        type: ReportSection.reducers.receiveSources.typeName,
        statePath,
        sources,
      });
    },

    loadReports: statePath => async (dispatch, getState) => {
      dispatch({
        type: ReportSection.reducers.requestReports.typeName,
        statePath,
      });
      const rootState = getState();
      let state = Polymer.Path.get(rootState, statePath);
      await Promise.all(state.source.selectedOptions.map(async source => {
        const request = new cp.ReportRequest({
          headers: rootState.authHeaders,
          source,
          milestone: state.milestone,
        });
        // TODO const response = await request.response;
        const response = request.localhostResponse_;
        state = Polymer.Path.get(getState(), statePath);
        if (!state.source.selectedOptions.includes(source)) return;
        dispatch({
          type: ReportSection.reducers.receiveReport.typeName,
          statePath,
          response,
        });
      }));
    },
  };

  ReportSection.reducers = {
    restoreState: cp.ElementBase.statePathReducer((state, action) => {
      const source = {...state.source, selectedOptions: action.options.sources};
      return {...state, source, milestone: action.options.milestone};
    }),

    receiveSources: cp.ElementBase.statePathReducer((state, action) => {
      const source = {...state.source};
      source.options = cp.OptionGroup.groupValues(action.sources);
      source.label = `Reports (${action.sources.length})`;
      return {...state, source};
    }),

    requestReports: cp.ElementBase.statePathReducer((state, action) => {
      return {...state, isLoading: true};
    }),

    receiveReport: cp.ElementBase.statePathReducer((state, action) => {
      return {...state, isLoading: false, ...action.response};
    }),
  };

  ReportSection.newStateOptionsFromQueryParams = queryParams => {
    return {
      sources: queryParams.getAll('report'),
      milestone: queryParams.get('m'),
    };
  };

  ReportSection.newState = options => {
    const sources = options.sources ? options.sources : [
      ReportSection.DEFAULT_SOURCE,
    ];
    return {
      isEditing: false,
      isLoading: false,
      isOwner: false,
      source: {
        label: 'Reports (loading)',
        options: [ReportSection.DEFAULT_SOURCE],
        query: '',
        selectedOptions: sources,
      },
      milestone: options.milestone || 64,
      isPreviousMilestone: false,
      isNextMilestone: false,
      anyAlerts: false,
    };
  };

  ReportSection.getSessionState = state => {
    return {
      sources: state.source.selectedOptions,
      milestone: state.milestone,
    };
  };

  ReportSection.getRouteParams = state => {
    const routeParams = new URLSearchParams();
    const selectedOptions = state.source.selectedOptions;
    if (state.containsDefaultSection &&
        selectedOptions.length === 1 &&
        selectedOptions[0] === ReportSection.DEFAULT_SOURCE) {
      return routeParams;
    }
    routeParams.set('m', state.milestone);
    for (const option of selectedOptions) {
      routeParams.append('report', option);
    }
    return routeParams;
  };

  cp.ElementBase.register(ReportSection);

  return {
    ReportSection,
  };
});
