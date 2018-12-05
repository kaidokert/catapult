/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class ReportTable extends cp.ElementBase {
    prevMstoneLabel_(milestone, maxRevision) {
      if (maxRevision === 'latest') milestone += 1;
      return `M${milestone - 1}`;
    }

    curMstoneLabel_(milestone, maxRevision) {
      if (maxRevision === 'latest') return '';
      return `M${milestone}`;
    }

    async onCopy_(event) {
      // TODO maybe use the template to render this table?
      const table = document.createElement('table');
      const statisticsCount = event.model.table.statistics.length;
      for (const row of event.model.table.rows) {
        const tr = document.createElement('tr');
        table.appendChild(tr);
        // b/111692559
        const td = document.createElement('td');
        td.innerText = row.label;
        tr.appendChild(td);

        for (let scalarIndex = 0; scalarIndex < 2 * statisticsCount;
          ++scalarIndex) {
          const td = document.createElement('td');
          tr.appendChild(td);
          const scalar = row.scalars[scalarIndex];
          if (isNaN(scalar.value) || !isFinite(scalar.value)) continue;
          const scalarStr = scalar.unit.format(scalar.value, {
            unitPrefix: scalar.unitPrefix,
          });
          const numberMatch = scalarStr.match(/^(-?[,0-9]+\.?[0-9]*)/);
          if (!numberMatch) continue;
          td.innerText = numberMatch[0];
        }
      }

      this.$.scratch.appendChild(table);
      const range = document.createRange();
      range.selectNodeContents(this.$.scratch);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      document.execCommand('copy');
      await this.$.copied.open();
      this.$.scratch.innerText = '';
    }

    async onOpenChart_(event) {
      // The user may have clicked a link for an individual row (in which case
      // labelPartIndex = labelParts.length - 1) or a group of rows (in which
      // case labelPartIndex < labelParts.length - 1). In the latter case,
      // collect all parameters for all rows in the group (all measurements, all
      // bots, all test cases, all test suites).
      function getLabelPrefix(row) {
        return row.labelParts.slice(0, event.model.labelPartIndex + 1).map(
            p => p.label).join(':');
      }
      const labelPrefix = getLabelPrefix(event.model.parentModel.row);
      const table = event.model.parentModel.parentModel.table;
      const testSuites = new Set();
      const measurements = new Set();
      const bots = new Set();
      const testCases = new Set();
      for (const row of table.rows) {
        if (getLabelPrefix(row) !== labelPrefix) continue;
        for (const testSuite of row.testSuite.selectedOptions) {
          testSuites.add(testSuite);
        }
        for (const measurement of row.measurement.selectedOptions) {
          measurements.add(measurement);
        }
        for (const bot of row.bot.selectedOptions) {
          bots.add(bot);
        }
        for (const testCase of row.testCase.selectedOptions) {
          testCases.add(testCase);
        }
      }
      let maxRevision = this.maxRevision;
      if (maxRevision === 'latest') {
        maxRevision = undefined;
      }

      this.dispatchEvent(new CustomEvent('new-chart', {
        bubbles: true,
        composed: true,
        detail: {
          options: {
            minRevision: this.minRevision,
            maxRevision,
            parameters: {
              testSuites: [...testSuites],
              measurements: [...measurements],
              bots: [...bots],
              testCases: [...testCases],
            },
          },
        },
      }));
    }

    async onToggleEditing_(event) {
      await this.dispatch('toggleEditing', this.statePath,
          event.model.tableIndex);
      if (this.tables[event.model.tableIndex].isEditing) {
        this.shadowRoot.querySelector('.report_name_input').focus();
      }
    }

    numChangeColumns_(statistics) {
      return 2 * this.lengthOf_(statistics);
    }

    canEdit_(table, userEmail) {
      return ReportTable.canEdit(table, userEmail);
    }

    async onOverRow_(event) {
      if (!event.model.row.actualDescriptors) return;
      let tr;
      for (const elem of event.path) {
        if (elem.tagName === 'TR') {
          tr = elem;
          break;
        }
      }
      if (!tr) return;
      const td = tr.querySelectorAll('td')[event.model.row.labelParts.length];
      const tdRect = await cp.measureElement(td);
      await this.dispatch('showTooltip', this.statePath, {
        rows: event.model.row.actualDescriptors.map(descriptor => [
          descriptor.testSuite, descriptor.bot, descriptor.testCase]),
        top: tdRect.bottom,
        left: tdRect.left,
      });
    }

    async onOutRow_(event) {
      await this.dispatch('hideTooltip', this.statePath);
    }
  }

  ReportTable.canEdit = (table, userEmail) =>
    window.IS_DEBUG ||
    (table && table.owners && userEmail && table.owners.includes(userEmail));

  ReportTable.State = {
    copiedMeasurements: options => false,
    isLoading: options => false,
    milestone: options => parseInt(options.milestone) || CURRENT_MILESTONE,
    minRevision: options => options.minRevision,
    maxRevision: options => options.maxRevision,
    minRevisionInput: options => options.minRevision,
    maxRevisionInput: options => options.maxRevision,
    sectionId: options => options.sectionId || tr.b.GUID.allocateSimple(),
    source: options => cp.MenuInput.buildState({
      label: 'Reports (loading)',
      options: [
        ReportTable.DEFAULT_NAME,
        ReportTable.CREATE,
      ],
      selectedOptions: options.sources ? options.sources : [
        ReportTable.DEFAULT_NAME,
      ],
    }),
    tables: options => [PLACEHOLDER_TABLE],
    tooltip: options => {return {};},
  };

  ReportTable.buildState = options => cp.buildState(
      ReportTable.State, options);

  ReportTable.properties = {
    ...cp.buildProperties('state', ReportTable.State),
  };

  ReportTable.actions = {
    toggleEditing: (statePath, tableIndex) => async(dispatch, getState) => {
      const rootState = getState();
      const state = Polymer.Path.get(rootState, statePath);
      const table = state.tables[tableIndex];
      if (table.canEdit !== true) {
        // TODO isLoading
        await ReportTable.actions.renderEditForm(
            statePath, tableIndex)(dispatch, getState);
      }
      dispatch(Redux.TOGGLE(`${statePath}.tables.${tableIndex}.isEditing`));
    },

    showTooltip: (statePath, tooltip) => async(dispatch, getState) => {
      dispatch(Redux.UPDATE(statePath, {tooltip}));
    },

    hideTooltip: statePath => async(dispatch, getState) => {
      dispatch(Redux.UPDATE(statePath, {tooltip: {}}));
    },
  };

  ReportTable.reducers = {
  };

  cp.ElementBase.register(ReportTable);

  return {ReportTable};
});
