/* Copyright 2019 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import './cp-dialog.js';
import '@chopsui/chops-loading';
import * as PolymerAsync from '@polymer/polymer/lib/utils/async.js';
import {BatchIterator} from '@chopsui/batch-iterator';
import {ElementBase, STORE, maybeScheduleAutoReload} from './element-base.js';
import {ReportControls} from './report-controls.js';
import {ReportFetcher, LATEST_REVISION} from './report-fetcher.js';
import {ReportMerger} from './report-merger.js';
import {ReportNamesRequest} from './report-names-request.js';
import {ReportTable} from './report-table.js';
import {ReportTemplate} from './report-template.js';
import {TimeseriesDescriptor} from './timeseries-descriptor.js';
import {UPDATE} from './simple-redux.js';
import {animationFrame} from './utils.js';
import {get} from 'dot-prop-immutable';
import {html, css} from 'lit-element';

const DEBOUNCE_LOAD_MS = 200;

export class ReportSection extends ElementBase {
  static get is() { return 'report-section'; }

  static get properties() {
    return {
      statePath: String,
      isLoading: Boolean,
      tables: Array,
    };
  }

  static buildState(options = {}) {
    return {
      ...ReportControls.buildState(options),
      isLoading: false,
      tables: [ReportTable.placeholderTable(
          ReportControls.DEFAULT_NAME)],
    };
  }

  static get styles() {
    return css`
      #tables {
        align-items: center;
        display: flex;
        flex-direction: column;
      }
      report-template {
        background-color: var(--background-color, white);
        overflow: auto;
      }
    `;
  }

  render() {
    return html`
      <report-controls .statePath="${this.statePath}">
      </report-controls>

      <chops-loading ?loading="${this.isLoading}"></chops-loading>

      <div id="tables">
        ${(this.tables || []).map((table, tableIndex) => html`
          <chops-loading ?loading="${table.isLoading}"></chops-loading>

          <report-table .statePath="${this.statePath}.tables.${tableIndex}">
          </report-table>

          ${!table.isEditing ? '' : html`
            <cp-dialog>
              <report-template
                  .statePath="${this.statePath}.tables.${tableIndex}"
                  @save="${this.onSave_}">
              </report-template>
            </cp-dialog>
          `}
        `)}
      </div>
    `;
  }

  firstUpdated() {
    this.scrollIntoView(true);
  }

  async onSave_(event) {
    await ReportSection.loadReports(this.statePath);
  }

  stateChanged(rootState) {
    if (!this.statePath) return;
    const newState = get(rootState, this.statePath);

    const sourcesChanged = newState && newState.source && (
      !this.source ||
      (this.minRevision !== newState.minRevision) ||
      (this.maxRevision !== newState.maxRevision) ||
      !tr.b.setsEqual(
          new Set(this.source.selectedOptions),
          new Set(newState.source.selectedOptions)));

    Object.assign(this, newState);

    if (sourcesChanged) {
      this.debounce('loadReports', () => {
        ReportSection.loadReports(this.statePath);
      }, PolymerAsync.timeOut.after(DEBOUNCE_LOAD_MS));
    }
  }

  static async restoreState(statePath, options) {
    STORE.dispatch({
      type: ReportSection.reducers.restoreState.name,
      statePath,
      options,
    });
    const state = get(STORE.getState(), statePath);
    if (state.minRevision === undefined ||
        state.maxRevision === undefined) {
      STORE.dispatch({
        type: ReportControls.reducers.selectMilestone.name,
        statePath,
        milestone: state.milestone,
      });
    }
  }

  static maybeAutoReload(statePath) {
    const state = get(STORE.getState(), statePath);
    if (!state || !state.minRevision ||
        (state.maxRevision !== 'latest')) {
      return;
    }
    ReportSection.loadReports(statePath);
  }

  static async loadReports(statePath) {
    let state = get(STORE.getState(), statePath);
    if (!state || !state.minRevision || !state.maxRevision) return;

    maybeScheduleAutoReload(statePath,
        state => (state.maxRevision === 'latest'),
        () => ReportSection.maybeAutoReload(statePath));

    STORE.dispatch({
      type: ReportSection.reducers.requestReports.name,
      statePath,
    });

    const names = state.source.selectedOptions.filter(name =>
      name !== ReportControls.CREATE);
    const requestedReports = new Set(state.source.selectedOptions);
    const revisions = [state.minRevision, state.maxRevision];
    const reportTemplateInfos = await new ReportNamesRequest().response;
    const readers = [];

    for (const templateInfo of reportTemplateInfos) {
      if (!names.includes(templateInfo.name)) continue;
      readers.push(new ReportFetcher(templateInfo, revisions));
    }

    for await (const {results, errors} of new BatchIterator(readers)) {
      state = get(STORE.getState(), statePath);
      if (!tr.b.setsEqual(requestedReports, new Set(
          state.source.selectedOptions)) ||
          (state.minRevision !== revisions[0]) ||
          (state.maxRevision !== revisions[1])) {
        return;
      }
      STORE.dispatch({
        type: ReportSection.reducers.receiveReports.name,
        statePath,
        reports: results,
        errors,
      });
      await animationFrame();
    }

    STORE.dispatch(UPDATE(statePath, {isLoading: false}));
  }
}

ReportSection.reducers = {
  restoreState: (state, action, rootState) => {
    if (!action.options || !state) return state;
    const source = {
      ...state.source,
      selectedOptions: action.options.sources,
    };
    return {
      ...state,
      source,
      milestone: parseInt(action.options.milestone ||
        ReportControls.CURRENT_MILESTONE),
      minRevision: action.options.minRevision,
      maxRevision: action.options.maxRevision,
      minRevisionInput: action.options.minRevision,
      maxRevisionInput: action.options.maxRevision,
    };
  },

  requestReports: (state, action, rootState) => {
    const tables = [];
    const tableNames = new Set();
    const selectedNames = state.source.selectedOptions;
    for (const table of state.tables) {
      // Remove tables whose names are unselected.
      if (selectedNames.includes(table.name)) {
        tables.push(table);
        tableNames.add(table.name);
      }
    }
    for (const name of selectedNames) {
      // Add placeholderTables for missing names.
      if (!tableNames.has(name)) {
        if (name === ReportControls.CREATE) {
          tables.push(ReportSection.newTemplate(rootState.userEmail));
        } else {
          tables.push(ReportTable.placeholderTable(name));
        }
      }
    }
    return {...state, isLoading: true, tables};
  },

  receiveReports: (state, {reports, errors}, rootState) => {
    // TODO handle errors

    const tables = [...state.tables];
    for (const report of reports) {
      // TODO handle report.errors

      if (!report || !report.timeseriesesByLine) {
        continue;
      }

      // Remove the placeholderTable for this report.
      const placeholderIndex = tables.findIndex(table =>
        table && (table.name === report.name));
      tables.splice(placeholderIndex, 1);

      const merger = new ReportMerger(
          report.timeseriesesByLine,
          [state.minRevision, state.maxRevision]);
      const rows = merger.mergedRows.map(row =>
        ReportSection.transformReportRow(
            row, state.minRevision, state.maxRevision,
            report.template.statistics));

      // Right-align labelParts.
      const maxLabelParts = tr.b.math.Statistics.max(rows, row =>
        row.labelParts.length);
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

      const minRevisions = new Set();
      const maxRevisions = new Set();
      for (const row of rows) {
        for (const rev of row.minRevisions) {
          minRevisions.add(rev);
        }
        for (const rev of row.maxRevisions) {
          maxRevisions.add(rev);
        }
      }

      tables.push({
        name: report.name,
        milestone: state.milestone,
        minRevision: [...minRevisions].join(','),
        maxRevision: [...maxRevisions].join(','),
        id: report.id,
        internal: report.internal,
        canEdit: false,
        isEditing: false,
        isPlaceholder: false,
        rows,
        maxLabelParts,
        owners: (report.owners || []).join(', '),
        statistics: report.template.statistics,
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
          selectedOptions: report.template.statistics,
          required: true,
        },
      });
    }
    return {...state, tables};
  },
};

ReportSection.newTemplate = userEmail => {
  return {
    isEditing: true,
    isPlaceholder: false,
    name: '',
    owners: userEmail,
    url: '',
    statistics: [],
    rows: [ReportTemplate.newTemplateRow({})],
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
};

function maybeInt(x) {
  const i = parseInt(x);
  return isNaN(i) ? x : i;
}

ReportSection.newStateOptionsFromQueryParams = queryParams => {
  const options = {
    sources: queryParams.getAll('report'),
    milestone: parseInt(queryParams.get('m')) || undefined,
    minRevision: maybeInt(queryParams.get('minRev')) || undefined,
    maxRevision: maybeInt(queryParams.get('maxRev')) || undefined,
  };
  if (options.maxRevision < options.minRevision) {
    [options.maxRevision, options.minRevision] = [
      options.minRevision, options.maxRevision];
  }
  if (options.milestone === undefined &&
      options.minRevision !== undefined &&
      options.maxRevision !== undefined) {
    for (const [milestone, milestoneRevision] of Object.entries(
        ReportControls.CHROMIUM_MILESTONES)) {
      if ((milestoneRevision >= options.minRevision) &&
          ((options.maxRevision === LATEST_REVISION) ||
            (options.maxRevision >= milestoneRevision))) {
        options.milestone = milestone;
        break;
      }
    }
  }
  return options;
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
      selectedOptions[0] === ReportControls.DEFAULT_NAME) {
    return routeParams;
  }
  for (const option of selectedOptions) {
    if (option === ReportControls.CREATE) continue;
    routeParams.append('report', option);
  }
  routeParams.set('minRev', state.minRevision);
  routeParams.set('maxRev', state.maxRevision);
  return routeParams;
};

function chartHref(lineDescriptor) {
  const params = new URLSearchParams({
    measurement: lineDescriptor.measurement,
  });
  for (const suite of lineDescriptor.suites) {
    params.append('suite', suite);
  }
  for (const bot of lineDescriptor.bots) {
    params.append('bot', bot);
  }
  for (const cas of lineDescriptor.cases) {
    params.append('testCase', cas);
  }
  return location.origin + '#' + params;
}

ReportSection.transformReportRow = (
    row, minRevision, maxRevision, statistics) => {
  if (!row.suites) row.suites = row.testSuites;
  if (!row.cases) row.cases = row.testCases;

  const href = chartHref(row);
  const labelParts = row.label.split(':').map(label => {
    return {
      href,
      isFirst: true,
      label,
      rowCount: 1,
    };
  });

  const scalars = [];
  for (const revision of [minRevision, maxRevision]) {
    for (let statistic of statistics) {
      const scalar = {};
      scalars.push(scalar);

      // IndexedDB can return impartial results if there is no data cached for
      // the requested revision.
      if (!row.data[revision] || !row.data[revision].statistics) {
        continue;
      }

      if (statistic === 'avg') statistic = 'mean';
      if (statistic === 'std') statistic = 'stddev';

      scalar.unit = (statistic === 'count') ? tr.b.Unit.byName.count : row.unit;
      if (row.unit.baseUnit === tr.b.Unit.byName.sizeInBytes) {
        scalar.unitPrefix = tr.b.UnitPrefixScale.BINARY.KIBI;
      }
      scalar.value = row.data[revision].statistics[statistic];
    }
  }

  // Create relative and absolute delta scalars.
  for (let statistic of statistics) {
    const relDelta = {};
    const absDelta = {};
    scalars.push(relDelta);
    scalars.push(absDelta);

    if (statistic === 'avg') statistic = 'mean';
    if (statistic === 'std') statistic = 'stddev';

    // IndexedDB can return impartial results if there is no data cached for
    // the requested min or max revision.
    if (!row.data[minRevision] ||
        !row.data[minRevision].statistics ||
        !row.data[maxRevision] ||
        !row.data[maxRevision].statistics) {
      continue;
    }

    absDelta.unit = ((statistic === 'count') ? tr.b.Unit.byName.count :
      row.unit).correspondingDeltaUnit;
    const suffix = tr.b.Unit.nameSuffixForImprovementDirection(
        absDelta.unit.improvementDirection);
    relDelta.unit = tr.b.Unit.byName[`normalizedPercentageDelta${suffix}`];

    const minRevValue = row.data[minRevision].statistics[statistic];
    const maxRevValue = row.data[maxRevision].statistics[statistic];

    absDelta.value = maxRevValue - minRevValue;
    relDelta.value = absDelta.value / minRevValue;
  }

  // row.descriptor is a line descriptor merged from all the fetchDescriptors
  // that contributed data to the scalars.
  // row.suites/measurement/bots/cases are from the template.

  return {
    labelParts,
    scalars,
    label: row.label,
    descriptor: row.descriptor,
    minRevisions: row.data[minRevision] ? row.data[minRevision].revisions : [],
    maxRevisions: row.data[maxRevision] ? row.data[maxRevision].revisions : [],

    ...TimeseriesDescriptor.buildState({
      suite: {
        selectedOptions: row.suites,
        isAggregated: true,
        canAggregate: false,
      },
      measurement: {
        selectedOptions: [row.measurement],
        requireSingle: true,
      },
      bot: {
        selectedOptions: row.bots,
        isAggregated: true,
        canAggregate: false,
      },
      case: {
        selectedOptions: row.cases,
        isAggregated: true,
        canAggregate: false,
      },
    }),
  };
};

ElementBase.register(ReportSection);
