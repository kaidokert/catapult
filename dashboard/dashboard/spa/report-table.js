/* Copyright 2019 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import './cp-toast.js';
import './scalar-span.js';
import {ElementBase, STORE} from './element-base.js';
import {TOGGLE, UPDATE} from './simple-redux.js';
import {html, css} from 'lit-element';
import {get, measureElement} from './utils.js';

export default class ReportTable extends ElementBase {
  static get is() { return 'report-table'; }

  static get properties() {
    return {
      userEmail: String,

      statePath: String,
      milestone: Number,
      minRevision: String,
      maxRevision: String,
      name: String,
      url: String,
      isPlaceholder: Boolean,
      maxLabelParts: Number,
      statistics: Array,
      rows: Array,
      owners: Array,
      tooltip: Object,
    };
  }

  static buildState(options = {}) {
    return {
      milestone: options.milestone,
      minRevision: options.minRevision,
      maxRevision: options.maxRevision,
      name: options.name || '',
      url: options.url || '',
      isPlaceholder: options.isPlaceholder || false,
      maxLabelParts: options.maxLabelParts || 1,
      statistics: options.statistics || ['avg'],
      rows: options.rows || [],
      owners: options.owners || [],
      tooltip: {},
    };
  }

  static get styles() {
    return css`
      :host {
        position: relative;
      }
      .report_name {
        display: flex;
        justify-content: center;
        margin: 24px 0 0 0;
      }

      table {
        border-collapse: collapse;
      }

      #table tbody tr {
        border-bottom: 1px solid var(--neutral-color-medium, grey);
      }

      table[placeholder] {
        color: var(--neutral-color-dark, grey);
      }

      h2 {
        text-align: center;
        margin: 0;
      }

      .name_column {
        text-align: left;
      }

      td, th {
        padding: 4px;
        vertical-align: top;
      }

      #edit,
      #copy,
      #documentation {
        color: var(--primary-color-dark, blue);
        cursor: pointer;
        flex-shrink: 0;
        margin: 0 0 0 8px;
        padding: 0;
        width: var(--icon-size, 1em);
        height: var(--icon-size, 1em);
      }

      .report_name span {
        position: relative;
        display: flex;
        align-items: center;
      }

      #tooltip {
        display: none;
        position: absolute;
        z-index: var(--layer-menu, 100);
      }

      :host(:hover) #tooltip {
        display: block;
      }

      #tooltip table {
        background-color: var(--background-color, white);
        border: 2px solid var(--primary-color-dark, blue);
        padding: 8px;
      }

      #tooltip td {
        padding: 2px;
      }

      #copied {
        display: flex;
        justify-content: center;
        background-color: var(--primary-color-dark, blue);
        color: var(--background-color, white);
        padding: 8px;
      }

      #scratch {
        opacity: 0;
        position: absolute;
        z-index: var(--layer-hidden, -100);
      }

      iron-icon[hidden] {
        display: none;
      }
    `;
  }

  render() {
    return html`
      <div class="report_name">
        <h2>${this.name}</h2>

        ${!this.url ? '' : html`
          <a id="documentation"
              href="${this.url}"
              target="_blank"
              title="Documentation">
            <iron-icon icon="cp:help">
            </iron-icon>
          </a>
        `}

        <iron-icon
            id="copy"
            icon="cp:copy"
            title="Copy measurements"
            @click="${this.onCopy_}">
        </iron-icon>

        <iron-icon
            id="edit"
            hidden="${!ReportTable.canEdit(this.owners, this.userEmail)}"
            icon="cp:edit"
            title="Edit template"
            @click="${this.onToggleEditing_}">
        </iron-icon>
      </div>

      <table id="table" placeholder="${this.isPlaceholder}">
        <thead>
          <tr>
            <th colspan="${this.maxLabelParts}">&nbsp;</th>
            <th colspan="${this.statistics.length}">
              M${(this.maxRevision === 'latest') ? this.milestone :
    (this.milestone - 1)}
              <br>
              ${this.minRevision}
            </th>
            <th colspan="${this.statistics.length}">
              ${(this.maxRevision === 'latest') ? '' : ('M' + this.milestone)}
              <br>
              ${this.maxRevision}
            </th>
            <th colspan="${2 * this.statistics.length}">Change</th>
          </tr>
          ${(this.statistics.length <= 1) ? '' : html`
            <tr>
              <th colspan="${this.maxLabelParts}">&nbsp;</th>
              ${this.statistics.map(statistic => html`
                <th>${statistic}</th>
              `)}
              ${this.statistics.map(statistic => html`
                <th>${statistic}</th>
              `)}
              ${this.statistics.map(statistic => html`
                <th colspan="2">${statistic}</th>
              `)}
            </tr>
          `}
        </thead>

        <tbody>
          ${this.rows.map(row => html`
            <tr @mouseenter="${this.onEnterRow_}">
              ${row.labelParts.map((labelPart, labelPartIndex) =>
    (!labelPart.isFirst ? '' : html`
                  <td row-span="${labelPart.rowCount}">
                    <a href="${labelPart.href}"
                        @click="${this.onOpenChart_}">
                      ${labelPart.label}
                    </a>
                  </td>
              `))}

              ${row.scalars.map(scalar => html`
                <td>
                  <scalar-span
                      unit="${scalar.unit}"
                      unit-prefix="${scalar.unitPrefix}"
                      value="${scalar.value}">
                  </scalar-span>
                </td>
              `)}
            </tr>
          `)}
        </tbody>
      </table>

      <div id="tooltip"
          style="top: ${this.tooltip.top}px; left: ${this.tooltip.left}px;">
        ${(!this.tooltip.rows || !this.tooltip.rows.length) ? '' : html`
          <table>
            <tbody>
              ${this.tooltip.rows.map(row => html`
                <tr>
                  ${row.map(cell => html`
                    <td>${cell}</td>
                  `)}
                </tr>
              `)}
            </tbody>
          </table>
        `}
      </div>

      <div id="scratch">
      </div>

      <cp-toast id="copied">
        Copied measurements
      </cp-toast>
    `;
  }

  stateChanged(rootState) {
    this.set('userEmail', rootState.userEmail);
    super.stateChanged(rootState);
  }

  async onCopy_(event) {
    const table = document.createElement('table');
    const statisticsCount = this.statistics.length;
    for (const row of this.rows) {
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

  async onToggleEditing_(event) {
    await STORE.dispatch(TOGGLE(this.statePath + '.isEditing'));
  }

  async onOpenChart_(event) {
    event.preventDefault();

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

  async onEnterRow_(event) {
    if (!event.model.row.actualDescriptors) return;
    let tr;
    for (const elem of event.path) {
      if (elem.tagName === 'TR') {
        tr = elem;
        break;
      }
    }
    if (!tr) return;
    const td = tr.querySelector('scalar-span').parentNode;
    const tdRect = await measureElement(td);
    const thisRect = await measureElement(this);
    await STORE.dispatch(UPDATE(this.statePath, {
      tooltip: {
        rows: event.model.row.actualDescriptors.map(descriptor => [
          descriptor.testSuite, descriptor.bot, descriptor.testCase]),
        top: (tdRect.bottom - thisRect.top),
        left: (tdRect.left - thisRect.left),
      },
    }));
  }
}

ReportTable.canEdit = (owners, userEmail) =>
  window.IS_DEBUG ||
  (owners && userEmail && owners.includes(userEmail));

const DASHES = '-'.repeat(5);
const PLACEHOLDER_TABLE = {
  name: DASHES,
  isPlaceholder: true,
  statistics: ['avg'],
  report: {rows: []},
};
// Keep this the same shape as the default report so that the buttons don't
// move when the default report loads.
for (let i = 0; i < 4; ++i) {
  const scalars = [];
  for (let j = 0; j < 4 * PLACEHOLDER_TABLE.statistics.length; ++j) {
    scalars.push({value: 0});
  }
  PLACEHOLDER_TABLE.report.rows.push({
    labelParts: [
      {
        href: '',
        label: DASHES,
        isFirst: true,
        rowCount: 1,
      },
    ],
    scalars,
  });
}

ReportTable.placeholderTable = name => {
  return {
    ...PLACEHOLDER_TABLE,
    name,
  };
};

ElementBase.register(ReportTable);
