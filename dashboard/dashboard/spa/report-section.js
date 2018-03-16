/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  const CHROMIUM_MILESTONES = {
    54: [416640, 423768],
    55: [433391, 433400],
    56: [433400, 445288],
    57: [447949, 454466],
    58: [454523, 463842],
    59: [465221, 474839],
    60: [474952, 488392],
    61: [488576, 498621],
    62: [502840, 508578],
    63: [508578, 520719],
    64: [528754, 530282],
    65: [530424, 540245],
    66: [540302, 543346],
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

    async onSelectSource_(event) {
      event.cancelBubble = true;
      await this.dispatch('loadReports', this.statePath);
      if (this.source.selectedOptions.includes(ReportSection.CREATE)) {
        this.shadowRoot.querySelector(
            'paper-input[label="Report Name"]').focus();
      }
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
      if (this.tables[event.model.tableIndex].isEditing) {
        this.shadowRoot.querySelector('paper-input').focus();
      }
    }

    isValid_(table) {
      return ReportSection.isValid(table);
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

    onTemplateUrlKeyUp_(event) {
      this.dispatch('templateUrl', this.statePath, event.model.tableIndex,
          event.target.value);
    }

    onTemplateRowLabelKeyUp_(event) {
      this.dispatch('templateRowLabel', this.statePath,
          event.model.tableIndex, event.model.rowIndex, event.target.value);
    }

    onTestSuiteSelect_(event) {
      event.cancelBubble = true;
      this.dispatch('templateTestSuite', this.statePath,
          event.model.tableIndex, event.model.rowIndex);
    }

    onTemplateRemoveRow_(event) {
      this.dispatch('templateRemoveRow', this.statePath,
          event.model.tableIndex, event.model.rowIndex);
    }

    onTemplateAddRow_(event) {
      this.dispatch('templateAddRow', this.statePath, event.model.tableIndex);
    }

    onTemplateSave_(event) {
      this.dispatch('templateSave', this.statePath, event.model.tableIndex);
    }

    onAuthChanged_() {
      this.dispatch('authChange', this.statePath);
    }

    numChangeColumns_(statistics) {
      return 2 * this._len(statistics);
    }

    showDocumentation_(table) {
      return table.url && !table.owners;
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
      minRevision: {type: Number},
      maxRevision: {type: Number},
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
    name: '(loading)',
    rows: [],
    statistics: ['avg'],
  };
  // Keep this the same shape as the default report so that the buttons don't
  // jump around the page when the default report loads.
  for (let i = 0; i < 5; ++i) {
    PLACEHOLDER_TABLE.rows.push({
      labelParts: [
        {
          href: '',
          label: DASHES,
          isFirst: true,
          rowCount: 1,
        },
      ],
      scalars: [
        {value: 0, unit: tr.b.Unit.byName.count},
        {value: 0, unit: tr.b.Unit.byName.count},
        {value: 0, unit: tr.b.Unit.byName.count},
        {value: 0, unit: tr.b.Unit.byName.count},
      ],
    });
  }

  ReportSection.LOADING_SOURCE = '(loading)';
  ReportSection.DEFAULT_NAME = 'Chromium Performance Overview';
  ReportSection.CREATE = '[Create new report]';

  ReportSection.actions = {
    connected: statePath => async(dispatch, getState) => {
      await dispatch(ReportSection.actions.loadSources(statePath));
      const rootState = getState();
      const state = Polymer.Path.get(rootState, statePath);
      if (state.minRevision === undefined ||
          state.maxRevision === undefined) {
        dispatch(ReportSection.actions.selectMilestone(
            statePath, state.milestone));
      }
      if (state.source.selectedOptions.length > 0) {
        dispatch(ReportSection.actions.loadReports(statePath));
      } else {
        dispatch(cp.DropdownInput.actions.focus(statePath + '.source'));
      }
    },

    authChange: statePath => async(dispatch, getState) => {
      dispatch(ReportSection.actions.loadSources(statePath));
    },

    selectMilestone: (statePath, milestone) => async(dispatch, getState) => {
      dispatch({
        type: ReportSection.reducers.selectMilestone.typeName,
        statePath,
        milestone,
      });
    },

    restoreState: (statePath, options) => async(dispatch, getState) => {
      dispatch({
        type: ReportSection.reducers.restoreState.typeName,
        statePath,
        options,
      });
    },

    toggleEditing: (statePath, tableIndex) => async(dispatch, getState) => {
      dispatch(cp.ElementBase.actions.toggleBoolean(
          `${statePath}.tables.${tableIndex}.isEditing`));
    },

    loadSources: statePath => async(dispatch, getState) => {
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

    loadReports: statePath => async(dispatch, getState) => {
      const rootState = getState();
      let state = Polymer.Path.get(rootState, statePath);
      const testSuites = await dispatch(
          cp.TimeseriesCache.actions.testSuites());
      const names = state.source.selectedOptions.filter(name =>
        name !== ReportSection.CREATE);

      const requestedReports = new Set(state.source.selectedOptions);
      const revisions = [state.minRevision, state.maxRevision];

      const promises = names.map(name =>
        new cp.ReportRequest({
          headers: rootState.authHeaders,
          ...state.templateIds.get(name),
          revisions,
        }).response);

      dispatch({
        type: ReportSection.reducers.requestReports.typeName,
        statePath,
      });

      if (state.source.selectedOptions.includes(ReportSection.CREATE)) {
        dispatch({
          type: ReportSection.reducers.create.typeName,
          statePath,
          testSuites,
        });
      }

      const batches = cp.RequestBase.batchResponses(promises);
      for await (const {results} of batches) {
        state = Polymer.Path.get(getState(), statePath);
        if (!tr.b.setsEqual(requestedReports, new Set(
            state.source.selectedOptions)) ||
            (state.minRevision !== revisions[0]) ||
            (state.maxRevision !== revisions[1])) {
          return;
        }
        dispatch({
          type: ReportSection.reducers.receiveReports.typeName,
          statePath,
          reports: results,
          testSuites,
        });
        state = Polymer.Path.get(getState(), statePath);
        for (let tableIndex = 0; tableIndex < state.tables.length;
          ++tableIndex) {
          for (let rowIndex = 0;
            rowIndex < state.tables[tableIndex].rows.length; ++rowIndex) {
            dispatch(cp.ChartSection.actions.describeTestSuites(
                `${statePath}.tables.${tableIndex}.rows.${rowIndex}`));
          }
        }
      }
    },

    templateName: (statePath, tableIndex, name) =>
      async(dispatch, getState) => {
        dispatch(cp.ElementBase.actions.updateObject(
            `${statePath}.tables.${tableIndex}`, {name}));
      },

    templateOwners: (statePath, tableIndex, owners) =>
      async(dispatch, getState) => {
        dispatch(cp.ElementBase.actions.updateObject(
            `${statePath}.tables.${tableIndex}`, {owners}));
      },

    templateUrl: (statePath, tableIndex, url) =>
      async(dispatch, getState) => {
        dispatch(cp.ElementBase.actions.updateObject(
            `${statePath}.tables.${tableIndex}`, {url}));
      },

    templateRowLabel: (statePath, tableIndex, rowIndex, label) =>
      async(dispatch, getState) => {
        dispatch(cp.ElementBase.actions.updateObject(
            `${statePath}.tables.${tableIndex}.rows.${rowIndex}`,
            {label}));
      },

    templateTestSuite: (statePath, tableIndex, rowIndex) =>
      async(dispatch, getState) => {
        dispatch(cp.ChartSection.actions.describeTestSuites(
            `${statePath}.tables.${tableIndex}.rows.${rowIndex}`));
      },

    templateRemoveRow: (statePath, tableIndex, rowIndex) =>
      async(dispatch, getState) => {
        dispatch({
          type: ReportSection.reducers.templateRemoveRow.typeName,
          statePath,
          tableIndex,
          rowIndex,
        });
      },

    templateAddRow: (statePath, tableIndex) => async(dispatch, getState) => {
      dispatch({
        type: ReportSection.reducers.templateAddRow.typeName,
        statePath,
        tableIndex,
        testSuites: await dispatch(cp.TimeseriesCache.actions.testSuites()),
      });
    },

    templateSave: (statePath, tableIndex) => async(dispatch, getState) => {
      const rootState = getState();
      const state = Polymer.Path.get(rootState, statePath);
      const table = state.tables[tableIndex];
      const request = new cp.ReportTemplateRequest({
        headers: rootState.authHeaders,
        id: table.id,
        name: table.name,
        owners: table.owners.split(',').map(o => o.replace(/ /g, '')),
        url: table.url,
        statistics: table.statistic.selectedOptions,
        rows: table.rows.map(row => {
          return {
            label: row.label,
            testSuites: row.testSuite.selectedOptions,
            measurement: row.measurement.selectedOptions[0],
            bots: row.bot.selectedOptions,
            testCases: row.testCase.selectedOptions,
          };
        }),
      });
      dispatch(cp.ElementBase.actions.updateObject(statePath, {
        isLoading: true,
      }));
      await request.response;
      dispatch(cp.ElementBase.actions.updateObject(statePath, {
        isLoading: false,
      }));
      dispatch(ReportSection.actions.loadReports(statePath));
    },
  };

  ReportSection.reducers = {
    selectMilestone: cp.ElementBase.statePathReducer((state, action) => {
      const [minRevision, maxRevision] = CHROMIUM_MILESTONES[action.milestone];
      return {...state, minRevision, maxRevision, milestone: action.milestone};
    }),

    create: cp.ElementBase.statePathReducer((state, action, rootState) => {
      const newReport = {
        isEditing: true,
        name: '',
        owners: rootState.userEmail,
        url: '',
        statistics: [],
        rows: [ReportSection.newTemplateRow(action.testSuites)],
        statistic: {
          label: 'Statistics',
          query: '',
          options: [
            'avg',
            'std',
            'count',
            'min',
            'max',
            'median',
            'iqr',
            '90%',
            '95%',
            '99%',
          ],
          selectedOptions: ['avg'],
          required: true,
        },
      };
      return {...state, tables: [...state.tables, newReport]};
    }),

    restoreState: cp.ElementBase.statePathReducer((state, action) => {
      if (!action.options) return state;
      const source = {...state.source, selectedOptions: action.options.sources};
      return {...state, source, milestone: parseInt(action.options.milestone)};
    }),

    receiveSources: cp.ElementBase.statePathReducer(
        (state, action, rootState) => {
          const templateIds = new Map(action.sources.map(entity =>
            [entity.name, entity]));
          const source = {...state.source};
          source.options = cp.OptionGroup.groupValues(templateIds.keys());
          if (location.hostname === 'localhost' || rootState.authHeaders) {
            source.options.push(ReportSection.CREATE);
          }
          source.label = `Reports (${action.sources.length})`;
          return {...state, source, templateIds};
        }),

    requestReports: cp.ElementBase.statePathReducer((state, action) => {
      return {...state, isLoading: true};
    }),

    receiveReports: cp.ElementBase.statePathReducer((state, action) => {
      const origin = location.origin + '#';
      const tables = state.areTablesPlaceholders ? [] : [...state.tables];
      for (const report of action.reports) {
        let maxLabelParts = 0;
        const rows = report.rows.map(row => {
          const labelParts = row.label.split(':').map(label => {
            return {
              href: origin + new URLSearchParams('TODO'),
              isFirst: true,
              label,
              rowCount: 1,
            };
          });
          maxLabelParts = Math.max(maxLabelParts, labelParts.length);

          let rowUnit = tr.b.Unit.byJSONName[row.units];
          let conversionFactor = 1;
          if (!rowUnit) {
            const info = tr.v.LEGACY_UNIT_INFO.get(row.units);
            if (info) {
              conversionFactor = info.conversionFactor;
              rowUnit = tr.b.Unit.byName[info.name];
            } else {
              rowUnit = tr.b.Unit.byName.unitlessNumber;
            }
          }

          const scalars = [];
          for (const revision of [state.maxRevision, state.minRevision]) {
            for (const statistic of report.statistics) {
              const unit = (statistic === 'count') ? tr.b.Unit.byName.count :
                rowUnit;
              let unitPrefix;
              if (rowUnit.baseUnit === tr.b.Unit.byName.sizeInBytes) {
                unitPrefix = tr.b.UnitPrefixScale.BINARY.KIBI;
              }
              scalars.push({
                unit,
                unitPrefix,
                value: row[revision][statistic],
              });
            }
          }
          for (const statistic of report.statistics) {
            const unit = ((statistic === 'count') ? tr.b.Unit.byName.count :
              rowUnit).correspondingDeltaUnit;
            const deltaValue = (
              row[state.maxRevision][statistic] -
              row[state.minRevision][statistic]);
            const suffix = tr.b.Unit.nameSuffixForImprovementDirection(
                unit.improvementDirection);
            scalars.push({
              unit: tr.b.Unit.byName[`normalizedPercentageDelta${suffix}`],
              value: deltaValue / row[state.minRevision][statistic],
            });
            scalars.push({
              unit,
              value: deltaValue,
            });
          }
          return {
            labelParts,
            scalars,
            label: row.label,
            testSuite: {
              errorMessage: 'required',
              label: `Test suites (${action.testSuites.count})`,
              options: action.testSuites.options,
              query: '',
              required: true,
              selectedOptions: row.testSuites,
            },
            measurement: {
              errorMessage: 'require exactly one',
              label: 'Measurement',
              options: [],
              query: '',
              requireSingle: true,
              required: true,
              selectedOptions: [row.measurement],
            },
            bot: {
              errorMessage: 'required',
              label: 'Bots',
              options: [],
              query: '',
              required: true,
              selectedOptions: row.bots,
            },
            testCase: {
              label: 'Test cases',
              options: [],
              query: '',
              selectedOptions: row.testCases,
            },
          };
        });

        // Right-align labelParts.
        for (const {labelParts} of rows) {
          while (labelParts.length < maxLabelParts) {
            labelParts.unshift({
              href: '',
              isFirst: true,
              label: '',
              rowCount: 1,
            });
          }
        }

        // Compute labelPart.isFirst, labelPart.rowCount.
        for (let rowIndex = 1; rowIndex < rows.length; ++rowIndex) {
          for (let partIndex = 0; partIndex < maxLabelParts; ++partIndex) {
            if (rows[rowIndex].labelParts[partIndex].label !==
                rows[rowIndex - 1].labelParts[partIndex].label) {
              continue;
            }
            rows[rowIndex].labelParts[partIndex].isFirst = false;
            let firstRi = rowIndex - 1;
            while (!rows[firstRi].labelParts[partIndex].isFirst) {
              --firstRi;
            }
            ++rows[firstRi].labelParts[partIndex].rowCount;
          }
        }

        // TODO compute colors for deltaPercent columns
        tables.push({
          ...report,
          isEditing: false,
          rows,
          maxLabelParts,
          owners: (report.owners || []).join(', '),
          statistic: {
            label: 'Statistics',
            query: '',
            options: [
              'avg',
              'std',
              'count',
              'min',
              'max',
              'median',
              'iqr',
              '90%',
              '95%',
              '99%',
            ],
            selectedOptions: report.statistics,
            required: true,
          },
        });
      }
      return {
        ...state,
        isLoading: false,
        areTablesPlaceholders: false,
        tables,
      };
    }),

    templateRemoveRow: cp.ElementBase.statePathReducer((state, action) => {
      const tables = [...state.tables];
      const table = tables[action.tableIndex];
      const rows = [...table.rows];
      rows.splice(action.rowIndex, 1);
      tables[action.tableIndex] = {
        ...table,
        rows,
      };
      return {...state, tables};
    }),

    templateAddRow: cp.ElementBase.statePathReducer((state, action) => {
      const tables = [...state.tables];
      const table = tables[action.tableIndex];
      tables[action.tableIndex] = {
        ...table,
        rows: [
          ...table.rows,
          ReportSection.newTemplateRow(action.testSuites),
        ],
      };
      return {...state, tables};
    }),
  };

  ReportSection.newTemplateRow = testSuites => {
    return {
      label: '',
      testSuite: {
        errorMessage: 'required',
        label: `Test suites (${testSuites.count})`,
        options: testSuites.options,
        query: '',
        required: true,
        selectedOptions: [],
      },
      measurement: {
        errorMessage: 'require exactly one',
        label: 'Measurement',
        options: [],
        query: '',
        requireSingle: true,
        required: true,
        selectedOptions: [],
      },
      bot: {
        errorMessage: 'required',
        label: 'Bots',
        options: [],
        query: '',
        required: true,
        selectedOptions: [],
      },
      testCase: {
        label: 'Test cases',
        options: [],
        query: '',
        selectedOptions: [],
      },
    };
  };

  ReportSection.newStateOptionsFromQueryParams = queryParams => {
    const options = {
      sources: queryParams.getAll('report'),
      milestone: parseInt(queryParams.get('m')) || undefined,
      minRevision: parseInt(queryParams.get('minRev')) || undefined,
      maxRevision: parseInt(queryParams.get('maxRev')) || undefined,
    };
    if (options.maxRevision < options.minRevision) {
      [options.maxRevision, options.minRevision] = [
        options.minRevision, options.maxRevision];
    }
    if (options.milestone === undefined &&
        options.minRevision !== undefined &&
        options.maxRevision !== undefined) {
      const paramRevisions = tr.b.math.Range.fromExplicitRange(
          options.minRevision, options.maxRevision);
      // Find the milestone that most intersects paramRevisions;
      let largestIntersection = -1;
      for (const [milestone, milestoneRevisions] of Object.entries(
          CHROMIUM_MILESTONES)) {
        const intersection = paramRevisions.findIntersection(
            tr.b.math.Range.fromExplicitRange(...milestoneRevisions)).range;
        if (intersection < largestIntersection) break;
        largestIntersection = intersection;
        options.milestone = milestone;
      }
    }
    return options;
  };

  ReportSection.newState = options => {
    const sources = options.sources ? options.sources : [
      ReportSection.DEFAULT_NAME,
    ];
    return {
      isLoading: false,
      source: {
        label: 'Reports (loading)',
        options: [
          ReportSection.DEFAULT_NAME,
          ReportSection.CREATE,
        ],
        query: '',
        selectedOptions: sources,
      },
      templateIds: new Map(),
      milestone: parseInt(options.milestone) || CURRENT_MILESTONE,
      minRevision: undefined,
      maxRevision: undefined,
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
        selectedOptions[0] === ReportSection.DEFAULT_NAME) {
      return routeParams;
    }
    for (const option of selectedOptions) {
      if (option === ReportSection.CREATE) continue;
      routeParams.append('report', option);
    }
    routeParams.set('minRev', state.minRevision);
    routeParams.set('maxRev', state.maxRevision);
    return routeParams;
  };

  ReportSection.isValid = table => {
    if (!table) return false;
    if (!table.name) return false;
    if (!table.owners) return false;
    if (table.statistic.selectedOptions.length === 0) return false;
    for (const row of table.rows) {
      if (!row.label) return false;
      if (row.testSuite.selectedOptions.length === 0) return false;
      if (row.measurement.selectedOptions.length === 0) return false;
      if (row.bot.selectedOptions.length === 0) return false;
    }
    return true;
  };

  cp.ElementBase.register(ReportSection);

  return {
    ReportSection,
  };
});
