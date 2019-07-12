/* Copyright 2019 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import './cp-flex.js';
import './cp-icon.js';
import './cp-toast.js';
import './scalar-span.js';
import {ElementBase, STORE} from './element-base.js';
import {LATEST_REVISION} from './report-fetcher.js';
import {TOGGLE, UPDATE} from './simple-redux.js';
import {get} from 'dot-prop-immutable';
import {html, css} from 'lit-element';
import {isDebug, measureElement} from './utils.js';

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

export class ReportTable extends ElementBase {
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
    };
  }

  static get styles() {
    return css`
      :host {
        position: relative;
      }
      .report_name {
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

      cp-icon[hidden] {
        display: none;
      }
    `;
  }

  render() {
    return html`
      <cp-flex class="report_name">
        <h2>${this.name}</h2>

        ${!this.url ? '' : html`
          <a id="documentation"
              href="${this.url}"
              target="_blank"
              title="Documentation">
            <cp-icon icon="help"></cp-icon>
          </a>
        `}

        <cp-icon
            id="copy"
            icon="copy"
            title="Copy measurements"
            @click="${this.onCopy_}">
        </cp-icon>

        <cp-icon
            id="edit"
            ?hidden="${!ReportTable.canEdit(this.owners, this.userEmail)}"
            icon="edit"
            title="Edit template"
            @click="${this.onToggleEditing_}">
        </cp-icon>
      </cp-flex>

      <table id="table" ?placeholder="${this.isPlaceholder}">
        <thead>
          <tr>
            <th colspan="${this.maxLabelParts}">&nbsp;</th>
            <th colspan="${this.statistics.length}">
              M${this.milestone}
              <br>
              ${this.minRevision}
            </th>
            <th colspan="${this.statistics.length}">
              M${this.milestone + 1}
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
          ${(this.rows || []).map(row => html`
            <tr>
              ${row.labelParts.map((labelPart, labelPartIndex) =>
    (!labelPart.isFirst ? '' : html`
                  <td rowspan="${labelPart.rowCount}">
                    <a href="${labelPart.href}"
                        @click="${event =>
        this.onOpenChart_(event, labelPartIndex, row)}">
                      ${labelPart.label}
                    </a>
                  </td>
              `))}

              ${row.scalars.map(scalar => html`
                <td>
                  <scalar-span
                      .unit="${scalar.unit}"
                      .unitPrefix="${scalar.unitPrefix}"
                      .value="${scalar.value}">
                  </scalar-span>
                </td>
              `)}
            </tr>
          `)}
        </tbody>
      </table>

      <div id="scratch">
      </div>

      <cp-toast id="copied">
        Copied measurements
      </cp-toast>
    `;
  }

  firstUpdated() {
    this.scratch = this.shadowRoot.querySelector('#scratch');
    this.copiedToast = this.shadowRoot.querySelector('#copied');
    this.table = this.shadowRoot.querySelector('#table');
  }

  stateChanged(rootState) {
    this.userEmail = rootState.userEmail;
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

    this.scratch.appendChild(table);
    const range = document.createRange();
    range.selectNodeContents(this.scratch);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
    document.execCommand('copy');
    await this.copiedToast.open();
    this.scratch.innerText = '';
  }

  async onToggleEditing_(event) {
    await STORE.dispatch(TOGGLE(this.statePath + '.isEditing'));
  }

  async onOpenChart_(event, labelPartIndex, row) {
    event.preventDefault();

    const parameters = {
      suites: new Set(),
      measurements: new Set(),
      bots: new Set(),
      cases: new Set(),
    };

    // The user may have clicked a link for an individual row (in which case
    // labelPartIndex = labelParts.length - 1) or a group of rows (in which
    // case labelPartIndex < labelParts.length - 1). In the latter case,
    // collect all parameters for all rows in the group (all measurements, all
    // bots, all test cases, all test suites).
    function getLabelPrefix(row) {
      return row.labelParts.slice(0, labelPartIndex + 1).map(
          p => p.label).join(':');
    }
    const labelPrefix = getLabelPrefix(row);
    for (const row of this.rows) {
      if (getLabelPrefix(row) !== labelPrefix) continue;

      for (const suite of row.descriptor.suites) {
        parameters.suites.add(suite);
      }
      parameters.measurements.add(row.descriptor.measurement);
      for (const bot of row.descriptor.bots) {
        parameters.bots.add(bot);
      }
      for (const cas of row.descriptor.cases) {
        parameters.cases.add(cas);
      }
    }

    parameters.suites = [...parameters.suites];
    parameters.measurements = [...parameters.measurements];
    parameters.bots = [...parameters.bots];
    parameters.cases = [...parameters.cases];

    this.dispatchEvent(new CustomEvent('new-chart', {
      bubbles: true,
      composed: true,
      detail: {
        options: {
          minRevision: this.minRevision,
          maxRevision: (this.maxRevision === LATEST_REVISION) ?
            undefined : this.maxRevision,
          parameters,
        },
      },
    }));
  }

  static canEdit(owners, userEmail) {
    return isDebug() || (owners && userEmail && owners.includes(userEmail));
  }

  static placeholderTable(name) {
    return {...PLACEHOLDER_TABLE, name};
  }
}

ElementBase.register(ReportTable);
