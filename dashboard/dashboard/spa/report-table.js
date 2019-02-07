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
      const suites = new Set();
      const measurements = new Set();
      const bots = new Set();
      const cases = new Set();
      for (const row of this.rows) {
        if (getLabelPrefix(row) !== labelPrefix) continue;
        for (const suite of row.suite.selectedOptions) {
          suites.add(suite);
        }
        for (const measurement of row.measurement.selectedOptions) {
          measurements.add(measurement);
        }
        for (const bot of row.bot.selectedOptions) {
          bots.add(bot);
        }
        for (const cas of row.case.selectedOptions) {
          cases.add(cas);
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
              suites: [...suites],
              measurements: [...measurements],
              bots: [...bots],
              cases: [...cases],
            },
          },
        },
      }));
    }

    numChangeColumns_(statistics) {
      return 2 * this.lengthOf_(statistics);
    }

    canEdit_(userEmail) {
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
          descriptor.suite, descriptor.bot, descriptor.case]),
        top: tdRect.bottom,
        left: tdRect.left,
      });
    }

    async onOutRow_(event) {
      await this.dispatch('hideTooltip', this.statePath);
    }
  }

  ReportTable.canEdit = (owners, userEmail) =>
    window.IS_DEBUG ||
    (owners && userEmail && owners.includes(userEmail));

  ReportTable.State = {
    name: options => options.name || '',
    url: options => options.url || '',
    isPlaceholder: options => options.isPlaceholder || false,
    maxLabelParts: options => options.maxLabelParts || 1,
    statistics: options => options.statistics || ['avg'],
    rows: options => options.rows || [],
    owners: options => options.owners || [],
    tooltip: options => {return {};},
  };

  ReportTable.buildState = options => cp.buildState(
      ReportTable.State, options);

  ReportTable.properties = cp.buildProperties('state', ReportTable.State);

  ReportTable.actions = {
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
