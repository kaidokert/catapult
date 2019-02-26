/* Copyright 2019 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class ReportTemplate extends cp.ElementBase {
    canSave_(name, owners, statistic, rows) {
      return ReportTemplate.canSave(name, owners, statistic, rows);
    }

    isLastRow_(rows) {
      return rows.length === 1;
    }

    async onCancel_(event) {
      await this.dispatch(Redux.TOGGLE(this.statePath + '.isEditing'));
    }

    async onTemplateNameKeyUp_(event) {
      await this.dispatch(Redux.UPDATE(this.statePath, {
        name: event.target.value,
      }));
    }

    async onTemplateOwnersKeyUp_(event) {
      await this.dispatch(Redux.UPDATE(this.statePath, {
        owners: event.target.value,
      }));
    }

    async onTemplateUrlKeyUp_(event) {
      await this.dispatch(Redux.UPDATE(this.statePath, {
        url: event.target.value,
      }));
    }

    async onTemplateRowLabelKeyUp_(event) {
      await this.dispatch(Redux.UPDATE(
          this.statePath + '.rows.' + event.model.rowIndex,
          {label: event.target.value}));
    }

    async onTemplateRemoveRow_(event) {
      await this.dispatch('removeRow', this.statePath, event.model.rowIndex);
    }

    async onTemplateAddRow_(event) {
      await this.dispatch('addRow', this.statePath, event.model.rowIndex);
    }

    async onTemplateSave_(event) {
      await this.dispatch('save', this.statePath);
      this.dispatchEvent(new CustomEvent('save', {
        bubbles: true,
        composed: true,
      }));
    }
  }

  ReportTemplate.State = {
    name: options => options.name || '',
    owners: options => options.owners || [],
    rows: options => options.rows || [],
    statistic: options => options.statistic,
    url: options => options.url || '',
  };

  ReportTemplate.buildState = options => cp.buildState(
      ReportTemplate.State, options);

  ReportTemplate.properties = {
    ...cp.buildProperties('state', ReportTemplate.State),
  };

  ReportTemplate.actions = {
    removeRow: (statePath, rowIndex) =>
      async(dispatch, getState) => {
        dispatch({
          type: ReportTemplate.reducers.removeRow.name,
          statePath,
          rowIndex,
        });
      },

    addRow: (statePath, rowIndex) =>
      async(dispatch, getState) => {
        dispatch({
          type: ReportTemplate.reducers.addRow.name,
          statePath,
          rowIndex,
          suites: await new cp.TestSuitesRequest({}).response,
        });
        const path = `${statePath}.rows.${rowIndex + 1}`;
        cp.ChartSection.actions.describeTestSuites(path)(dispatch, getState);
      },

    save: statePath => async(dispatch, getState) => {
      dispatch(Redux.UPDATE(statePath, {isLoading: true, isEditing: false}));
      const table = Polymer.Path.get(getState(), statePath);
      const request = new cp.ReportTemplateRequest({
        id: table.id,
        name: table.name,
        owners: table.owners.split(',').map(o => o.replace(/ /g, '')),
        url: table.url,
        statistics: table.statistic.selectedOptions,
        rows: table.rows.map(row => {
          return {
            label: row.label,
            suites: row.suite.selectedOptions,
            measurement: row.measurement.selectedOptions[0],
            bots: row.bot.selectedOptions,
            cases: row.case.selectedOptions,
          };
        }),
      });
      const reportTemplateInfos = await request.response;
      dispatch(Redux.UPDATE('', {reportTemplateInfos}));
    },
  };

  ReportTemplate.reducers = {
    removeRow: (state, action, rootState) => {
      const rows = [...state.rows];
      rows.splice(action.rowIndex, 1);
      return {...state, rows};
    },

    addRow: (table, action, rootState) => {
      const contextRow = table.rows[action.rowIndex];
      const newRow = ReportTemplate.newTemplateRow({
        suite: {
          options: cp.OptionGroup.groupValues(action.suites),
          label: `Test suites (${action.suites.length})`,
          selectedOptions: [...contextRow.suite.selectedOptions],
        },
        bot: {
          selectedOptions: [...contextRow.bot.selectedOptions],
        },
        case: {
          selectedOptions: [...contextRow.case.selectedOptions],
        },
      });
      const rows = [...table.rows];
      rows.splice(action.rowIndex + 1, 0, newRow);
      return {...table, rows};
    },
  };

  ReportTemplate.newTemplateRow = ({suite, bot, cas}) => {
    return {
      label: '',
      suite: {
        ...suite,
        errorMessage: 'Required',
        query: '',
        required: true,
        selectedOptions: suite.selectedOptions || [],
      },
      measurement: {
        errorMessage: 'Require exactly one',
        label: 'Measurement',
        options: [],
        query: '',
        requireSingle: true,
        required: true,
        selectedOptions: [],
      },
      bot: {
        errorMessage: 'Required',
        label: 'Bots',
        options: [],
        query: '',
        required: true,
        selectedOptions: bot ? bot.selectedOptions : [],
      },
      case: {
        label: 'Test cases',
        options: [],
        query: '',
        selectedOptions: cas ? cas.selectedOptions : [],
      },
    };
  };

  ReportTemplate.canSave = (name, owners, statistic, rows) => {
    if (!name || !owners || !statistic || !rows ||
        statistic.selectedOptions.length === 0) {
      return false;
    }
    for (const row of rows) {
      if (!row.label || !row.suite || !row.measurement || !row.bot ||
          row.suite.selectedOptions.length === 0 ||
          row.measurement.selectedOptions.length !== 1 ||
          row.bot.selectedOptions.length === 0) {
        return false;
      }
    }
    return true;
  };

  cp.ElementBase.register(ReportTemplate);

  return {ReportTemplate};
});
