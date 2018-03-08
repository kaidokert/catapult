/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  const CLANK_MILESTONES = {
    54: (1473196450, 1475824394),
    55: (1475841673, 1479536199),
    56: (1479546161, 1485025126),
    57: (1486119399, 1488528859),
    58: (1488538235, 1491977185),
    59: (1492542658, 1495792284),
    60: (1495802833, 1500610872),
    61: (1500628339, 1504160258),
    62: (1504294629, 1507887190),
    63: (1507887190, 0),
  };
  const CHROMIUM_MILESTONES = {
    54: (416640, 423768),
    55: (433391, 433400),
    56: (433400, 445288),
    57: (447949, 454466),
    58: (454523, 463842),
    59: (465221, 474839),
    60: (474952, 488392),
    61: (488576, 498621),
    62: (499187, 508578),
    63: (508578, 0),
  };
  const CURRENT_MILESTONE = tr.b.math.Statistics.max(
      Object.keys(CHROMIUM_MILESTONES));

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

    onToggleEditing_(event) {
      this.dispatch('toggleEditing', this.statePath, event.model.tableIndex);
    }

    isLastRow_(rows) {
      return rows.length === 1;
    }

    onTemplateNameKeyUp_(event) {
      this.dispatch('templateName', this.statePath, event.model.tableIndex,
          event.target.value);
    }

    onTemplateOwnersKeyUp_(event) {
      this.dispatch('templateOwners', this.statePath, event.model.tableIndex,
          event.target.value);
    }

    onTemplateRowLabelKeyUp_(event) {
      this.dispatch('templateRowLabel', this.statePath,
          event.model.tableIndex, event.model.rowIndex, event.target.value);
    }

    onTemplateRemoveRow_(event) {
      this.dispatch('templateRemoveRow', this.statePath,
          event.model.tableIndex, event.model.rowIndex);
    }

    onTemplateAddRow_(event) {
      this.dispatch('templateAddRow', this.statePath, event.model.tableIndex);
    }

    onAuthChanged_() {
      this.dispatch('authChange', this.statePath);
    }
  }

  ReportSection.properties = {
    ...cp.ElementBase.statePathProperties('statePath', {
      anyAlerts: {type: Boolean},
      areTablesPlaceholders: {type: Boolean},
      isLoading: {type: Boolean},
      isNextMilestone: {type: Boolean},
      isPreviousMilestone: {type: Boolean},
      milestone: {type: Number},
      sectionId: {type: String},
      source: {type: Object},
      tables: {type: Array},
    }),
    authHeaders: {
      type: Object,
      statePath: 'authHeaders',
      observer: 'onAuthChanged_',
    },
  };

  const DASHES = '-'.repeat(5);
  const PLACEHOLDER_TABLE = {
    title: '[placeholder report]',
    currentVersion: DASHES,
    referenceVersion: DASHES,
    rows: [],
  };
  // Keep this the same shape as the default report so that the buttons don't
  // jump around the page when the default report loads.
  for (let i = 0; i < 8; ++i) {
    PLACEHOLDER_TABLE.rows.push({
      isFirstInCategory: i === 0,
      rowCount: (i === 0) ? 8 : 0,
      category: '',
      href: '',
      name: DASHES,
      currentValue: 0,
      referenceValue: 0,
      deltaValue: 0,
      percentDeltaValue: 0,
      unit: tr.b.Unit.byName.unitlessNumber,
      deltaUnit: tr.b.Unit.byName.unitlessNumberDelta,
      percentDeltaUnit: tr.b.Unit.byName.normalizedPercentageDelta,
    });
  }

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

    authChange: statePath => async (dispatch, getState) => {
      dispatch(ReportSection.actions.loadSources(statePath));
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

    toggleEditing: (statePath, tableIndex) => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.toggleBoolean(
          `${statePath}.tables.${tableIndex}.isEditing`));
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

    templateName: (statePath, tableIndex, name) =>
      async (dispatch, getState) => {
        dispatch(cp.ElementBase.actions.updateObject(
            `${statePath}.tables.${tableIndex}.template`,
            {name}));
      },

    templateOwners: (statePath, tableIndex, owners) =>
      async (dispatch, getState) => {
        dispatch(cp.ElementBase.actions.updateObject(
            `${statePath}.tables.${tableIndex}.template`,
            {owners}));
      },

    templateRowLabel: (statePath, tableIndex, rowIndex, label) =>
      async (dispatch, getState) => {
        dispatch(cp.ElementBase.actions.updateObject(
            `${statePath}.tables.${tableIndex}.template.rows.${rowIndex}`,
            {label}));
      },

    templateRemoveRow: (statePath, tableIndex, rowIndex) =>
      async (dispatch, getState) => {
        dispatch({
          type: ReportSection.reducers.templateRemoveRow.typeName,
          statePath,
          tableIndex,
          rowIndex,
        });
      },

    templateAddRow: (statePath, tableIndex) => async (dispatch, getState) => {
      dispatch({
        type: ReportSection.reducers.templateAddRow.typeName,
        statePath,
        tableIndex,
      });
    },
  };

  ReportSection.reducers = {
    restoreState: cp.ElementBase.statePathReducer((state, action) => {
      if (!action.options) return state;
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
      return {
        ...state,
        ...action.response,
        isLoading: false,
        areTablesPlaceholders: false,
      };
    }),

    templateRemoveRow: cp.ElementBase.statePathReducer((state, action) => {
      const tables = [...state.tables];
      const table = tables[action.tableIndex];
      const rows = [...table.template.rows];
      rows.splice(action.rowIndex, 1);
      tables[action.tableIndex] = {
        ...table,
        template: {
          ...table.template,
          rows,
        },
      };
      return {...state, tables};
    }),

    templateAddRow: cp.ElementBase.statePathReducer((state, action) => {
      const tables = [...state.tables];
      const table = tables[action.tableIndex];
      tables[action.tableIndex] = {
        ...table,
        template: {
          ...table.template,
          rows: [
            ...table.template.rows,
            ReportSection.newTemplateRow(),
          ],
        },
      };
      return {...state, tables};
    }),
  };

  ReportSection.newTemplateRow = () => {
    return {
      label: '',
      testSuite: {
        label: 'Test suites',
        query: '',
        options: [],
        selectedOptions: [],
      },
      measurement: {
        label: 'Measurement',
        query: '',
        options: [],
        selectedOptions: [],
      },
      bot: {
        label: 'Bots',
        query: '',
        options: [],
        selectedOptions: [],
      },
      testCase: {
        label: 'Test cases',
        query: '',
        options: [],
        selectedOptions: [],
      },
      statistic: {
        label: 'Statistics',
        query: '',
        options: [],
        selectedOptions: [],
      },
    };
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
      isLoading: false,
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
      tables: [PLACEHOLDER_TABLE],
      areTablesPlaceholders: true,
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
