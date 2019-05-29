/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import './column-head.js';
import './cp-checkbox.js';
import './expand-button.js';
import './scalar-span.js';
import {ElementBase, STORE} from './element-base.js';
import {breakWords, crbug, get, setImmutable} from './utils.js';
import {html, css} from 'lit-element';

export default class AlertsTable extends ElementBase {
  static get is() { return 'alerts-table'; }

  static get properties() {
    return {
      areAlertGroupsPlaceholders: Boolean,
      statePath: String,
      previousSelectedAlertKey: String,
      alertGroups: Array,
      selectedAlertsCount: Number,
      showBugColumn: Boolean,
      showMasterColumn: Boolean,
      showCaseColumn: Boolean,
      showTriagedColumn: Boolean,
      showingTriaged: Boolean,
      sortColumn: String,
      sortDescending: Boolean,
    };
  }

  static buildState(options = {}) {
    return {
      previousSelectedAlertKey: undefined,
      alertGroups: options.alertGroups ||
        AlertsTable.placeholderAlertGroups(),
      selectedAlertsCount: 0,
      showBugColumn: options.showBugColumn !== false,
      showMasterColumn: options.showMasterColumn !== false,
      showCaseColumn: options.showCaseColumn !== false,
      showTriagedColumn: options.showTriagedColumn !== false,
      showingTriaged: options.showingTriaged || false,
      sortColumn: options.sortColumn || 'startRevision',
      sortDescending: options.sortDescending || false,
    };
  }

  static get styles() {
    return css`
      #cat {
        display: block;
        height: 300px;
        width: 300px;
      }

      :host {
        --min-table-height: 122px;
        --non-table-height: 483px;
      }

      #scroll {
        max-height: calc(100vh - var(--non-table-height));
        margin: 0;
        overflow-y: auto;
        overflow-x: hidden;
      }

      @media screen and (max-height: calc(var(--min-table-height) +
                                          var(--non-table-height))) {
        #scroll {
          max-height: var(--min-table-height);
        }
      }

      table {
        border-collapse: collapse;
        width: 100%;
      }

      table[is-placeholder] {
        color: var(--neutral-color-dark, grey);
      }

      th {
        padding: 8px;
        white-space: nowrap;
      }

      th.checkbox {
        padding-left: 4px;
        text-align: left;
      }

      td {
        padding: 4px;
      }

      tbody tr:hover {
        background: #eee;
      }

      td:last-child {
        padding-right: 0;
      }

      expand-button {
        align-items: center;
        justify-content: flex-end;
        margin-right: 16px;
      }

      tbody {
        border-color: var(--background-color, white);
        border-style: solid;
        border-width: 0 8px;
        transition: border-width var(--transition-short, 0.2s);
      }

      tbody[expandedGroup] {
        border-color: var(--primary-color-light, lightblue);
        border-width: 8px;
      }
    `;
  }

  render() {
    const allTriaged = this.showingTriaged ? (this.alertGroups.length === 0) :
      ((this.alertGroups || []).filter(group =>
        group.alerts.length > group.triaged.count).length === 0);
    const bodies = (this.alertGroups || []).map((alertGroup, alertGroupIndex) =>
      this.renderGroup(alertGroup, alertGroupIndex));

    return allTriaged ? html`
      <center>
        All alerts triaged!
        <iron-icon id="cat" icon="cp-big:cat">
        </iron-icon>
      </center>
    ` : html`
      <div id="scroll">
        <table is-placeholder="${this.areAlertGroupsPlaceholders}">
          <thead>
            <tr>
              <th>
                <column-head
                    name="count"
                    sort-column="${this.sortColumn}"
                    sort-descending="${this.sortDescending}"
                    disabled="${this.areAlertGroupsPlaceholders}"
                    @click="${this.onSort_}">
                  Count
                </column-head>
              </th>

              ${this.showTriagedColumn ? html`
                <th>
                  <column-head
                      name="triaged"
                      sort-column="${this.sortColumn}"
                      sort-descending="${this.sortDescending}"
                      disabled="${this.areAlertGroupsPlaceholders}"
                      @click="${this.onSort_}">
                    Triaged
                  </column-head>
                </th>
              ` : ''}

              <th class="checkbox">
                <cp-checkbox
                    checked="${this.selectedAlertsCount > 0}"
                    disabled="${this.areAlertGroupsPlaceholders}"
                    @change="${this.onSelectAll_}">
                </cp-checkbox>
              </th>

              ${this.showBugColumn ? html`
                <th>
                  <column-head
                      name="bugId"
                      sort-column="${this.sortColumn}"
                      sort-descending="${this.sortDescending}"
                      disabled="${this.areAlertGroupsPlaceholders}"
                      @click="${this.onSort_}">
                    Bug
                  </column-head>
                </th>
              ` : ''}

              <th>
                <column-head
                    name="startRevision"
                    sort-column="${this.sortColumn}"
                    sort-descending="${this.sortDescending}"
                    disabled="${this.areAlertGroupsPlaceholders}"
                    @click="${this.onSort_}">
                  Revisions
                </column-head>
              </th>

              <th>
                <column-head
                    name="suite"
                    sort-column="${this.sortColumn}"
                    sort-descending="${this.sortDescending}"
                    disabled="${this.areAlertGroupsPlaceholders}"
                    @click="${this.onSort_}">
                  Suite
                </column-head>
              </th>

              <th>
                <column-head
                    name="measurement"
                    sort-column="${this.sortColumn}"
                    sort-descending="${this.sortDescending}"
                    disabled="${this.areAlertGroupsPlaceholders}"
                    @click="${this.onSort_}">
                  Measurement
                </column-head>
              </th>

              ${this.showMasterColumn ? html`
                <th>
                  <column-head
                      name="master"
                      sort-column="${this.sortColumn}"
                      sort-descending="${this.sortDescending}"
                      disabled="${this.areAlertGroupsPlaceholders}"
                      @click="${this.onSort_}">
                    Master
                  </column-head>
                </th>
              ` : ''}

              <th>
                <column-head
                    name="bot"
                    sort-column="${this.sortColumn}"
                    sort-descending="${this.sortDescending}"
                    disabled="${this.areAlertGroupsPlaceholders}"
                    @click="${this.onSort_}">
                  Bot
                </column-head>
              </th>

              ${this.showCaseColumn ? html`
                <th>
                  <column-head
                      name="case"
                      sort-column="${this.sortColumn}"
                      sort-descending="${this.sortDescending}"
                      disabled="${this.areAlertGroupsPlaceholders}"
                      @click="${this.onSort_}">
                    Case
                  </column-head>
                </th>
              ` : ''}

              <th>
                <column-head
                    name="deltaValue"
                    sort-column="${this.sortColumn}"
                    sort-descending="${this.sortDescending}"
                    disabled="${this.areAlertGroupsPlaceholders}"
                    @click="${this.onSort_}">
                  Delta
                </column-head>
              </th>

              <th>
                <column-head
                    name="percentDeltaValue"
                    sort-column="${this.sortColumn}"
                    sort-descending="${this.sortDescending}"
                    disabled="${this.areAlertGroupsPlaceholders}"
                    @click="${this.onSort_}">
                  Delta %
                </column-head>
              </th>
            </tr>
          </thead>

          ${bodies}
        </table>
      </div>
    `;
  }

  renderGroup(alertGroup, alertGroupIndex) {
    const expandedGroup = alertGroup.isExpanded ||
      alertGroup.triaged.isExpanded;
    const rows = alertGroup.alerts.map((alert, alertIndex) =>
      this.renderAlert(alertGroup, alertGroupIndex, alert, alertIndex));
    return html`
      <tbody expandedGroup="${expandedGroup}">
        ${rows}
      </tbody>
    `;
  }

  renderAlert(alertGroup, alertGroupIndex, alert, alertIndex) {
    if (!AlertsTable.shouldDisplayAlert(
        this.areAlertGroupsPlaceholders, this.showingTriaged, alertGroup,
        alertIndex, alertGroup.triaged.isExpanded)) {
      return '';
    }

    // Most monitored timeseries on ChromiumPerf bots use revisions that are
    // supported by test-results.appspot.com.
    // TODO(benjhayden) Support revision range links more generally.
    const alertRevisionHref = (alert.master !== 'ChromiumPerf') ? '' :
      `http://test-results.appspot.com/revision_range?start=${alert.startRevision}&end=${alert.endRevision}&n=1000`;

    const alertRevisionString = (alert.startRevision === alert.endRevision) ?
      alert.startRevision : (alert.startRevision + '-' + alert.endRevision);

    const shouldDisplayExpandGroupButton =
      AlertsTable.shouldDisplayExpandGroupButton(
          alertGroup, alertIndex, this.showingTriaged);

    const expandGroupButtonLabel = this.showingTriaged ?
      alertGroup.alerts.length :
      (alertGroup.alerts.length - alertGroup.triaged.count);

    const shouldDisplayExpandTriagedButton =
      AlertsTable.shouldDisplayExpandTriagedButton(
          this.showingTriaged, alertGroup, alertIndex);

    const shouldDisplaySelectedCount = (this.showingTriaged) ?
      (alertIndex === 0) :
      (alertIndex === alertGroup.alerts.findIndex(a => !a.bugId));

    const expandTriagedStatePath =
      `${this.statePath}.alertGroups.${alertGroupIndex}.triaged`;

    return html`
      <tr @click="${this.onRowClick_}">
        <td>
          ${shouldDisplayExpandGroupButton ? html`
            <expand-button
                .statePath="${this.statePath}.alertGroups.${alertGroupIndex}">
              ${expandGroupButtonLabel}
            </expand-button>
          ` : ''}
        </td>

        ${this.showTriagedColumn ? html`
          <td>
            ${shouldDisplayExpandTriagedButton ? html`
              <expand-button .statePath="${expandTriagedStatePath}">
                ${alertGroup.triaged.count}
              </expand-button>
            ` : ''}
          </td>
        ` : ''}

        <td>
          <cp-checkbox
              checked="${alert.isSelected}"
              disabled="${this.areAlertGroupsPlaceholders}"
              @change="${this.onSelect_}">
            ${shouldDisplaySelectedCount ? this.selectedCount_(alertGroup) : ''}
          </cp-checkbox>
        </td>

        ${this.showBugColumn ? html`
          <td>
            ${!alert.bugId ? '' : (this.areAlertGroupsPlaceholders ? html`
              ${alert.bugId}
            ` : ((alert.bugId < 0) ? html`
              ignored
            ` : html`
              <a href="${crbug(alert.bugId)}" target="_blank">
                ${alert.bugId}
              </a>
            `))}
          </td>
        ` : ''}

        <td>
          ${alertRevisionHref ? html`
            <a href="${alertRevisionHref}" target="_blank">
              ${alertRevisionString}
            </a>
          ` : html`
            ${alertRevisionString}
          `}
        </td>

        <td style="color: ${alert.color};">
          ${breakWords(alert.suite)}
        </td>
        <td style="color: ${alert.color};">
          ${breakWords(alert.measurement)}
        </td>

        ${this.showMasterColumn ? html`
          <td style="color: ${alert.color};">
            ${alert.master}
          </td>
        ` : ''}

        <td style="color: ${alert.color};">
          ${alert.bot}
        </td>

        ${this.showCaseColumn ? html`
          <td style="color: ${alert.color};">
            ${breakWords(alert.case)}
          </td>
        ` : ''}

        <td>
          <scalar-span
              .value="${alert.deltaValue}"
              .unit="${alert.deltaUnit}">
          </scalar-span>
        </td>

        <td>
          <scalar-span
              .value="${alert.percentDeltaValue}"
              .unit="${alert.percentDeltaUnit}"
              .maximumFractionDigits="1">
          </scalar-span>
        </td>
      </tr>
    `;
  }

  ready() {
    super.ready();
    this.scrollIntoView(true);
  }

  stateChanged(rootState) {
    super.stateChanged(rootState);
    this.areAlertGroupsPlaceholders = (this.alertGroups ===
      AlertsTable.placeholderAlertGroups());
  }

  selectedCount_(alertGroup) {
    if (!alertGroup) return '';
    if (alertGroup.alerts.length === 1) return '';
    let count = 0;
    for (const alert of alertGroup.alerts) {
      if (alert.isSelected) ++count;
    }
    if (count === 0) return '';
    return `${count}/${alertGroup.alerts.length}`;
  }

  async onSelectAll_(event) {
    event.target.checked = !event.target.checked;
    await STORE.dispatch({
      type: AlertsTable.reducers.selectAllAlerts.name,
      statePath: this.statePath,
    });
    this.dispatchEvent(new CustomEvent('selected', {
      bubbles: true,
      composed: true,
    }));
  }

  async onSelect_(event) {
    let shiftKey = false;
    if (event.detail && event.detail.event &&
        (event.detail.event.shiftKey ||
          (event.detail.event.detail && event.detail.event.detail.shiftKey))) {
      shiftKey = true;
    }
    await STORE.dispatch({
      type: AlertsTable.reducers.selectAlert.name,
      statePath: this.statePath,
      alertGroupIndex: event.model.parentModel.alertGroupIndex,
      alertIndex: event.model.alertIndex,
      shiftKey,
    });
    this.dispatchEvent(new CustomEvent('selected', {
      bubbles: true,
      composed: true,
    }));
  }

  async onSort_(event) {
    await STORE.dispatch({
      type: AlertsTable.reducers.sort.name,
      statePath: this.statePath,
      sortColumn: event.target.name,
    });
    this.dispatchEvent(new CustomEvent('sort', {
      bubbles: true,
      composed: true,
    }));
  }

  async onRowClick_(event) {
    if (event.target.tagName !== 'TD') return;
    this.dispatchEvent(new CustomEvent('alert-click', {
      bubbles: true,
      composed: true,
      detail: {
        alertGroupIndex: event.model.alertGroupIndex,
        alertIndex: event.model.alertIndex,
      },
    }));
  }

  static getSelectedAlerts(alertGroups) {
    const selectedAlerts = [];
    for (const alertGroup of alertGroups) {
      for (const alert of alertGroup.alerts) {
        if (alert.isSelected) {
          selectedAlerts.push(alert);
        }
      }
    }
    return selectedAlerts;
  }
}

AlertsTable.shouldDisplayAlert = (
    areAlertGroupsPlaceholders, showingTriaged, alertGroup, alertIndex,
    triagedExpanded) => {
  if (areAlertGroupsPlaceholders) return true;
  if (showingTriaged) return alertGroup.isExpanded || (alertIndex === 0);

  if (!alertGroup.alerts[alertIndex]) return false;
  const isTriaged = alertGroup.alerts[alertIndex].bugId;
  const firstUntriagedIndex = alertGroup.alerts.findIndex(a => !a.bugId);
  if (alertGroup.isExpanded) {
    return !isTriaged || triagedExpanded || (
      alertIndex === firstUntriagedIndex);
  }
  if (isTriaged) return triagedExpanded;
  return alertIndex === firstUntriagedIndex;
};

AlertsTable.shouldDisplayExpandGroupButton = (
    alertGroup, alertIndex, showingTriaged) => {
  if (showingTriaged) {
    return (alertIndex === 0) && alertGroup.alerts.length > 1;
  }
  return (alertIndex === alertGroup.alerts.findIndex(a => !a.bugId)) && (
    alertGroup.alerts.length > (1 + alertGroup.triaged.count));
};

AlertsTable.shouldDisplayExpandTriagedButton = (
    showingTriaged, alertGroup, alertIndex) => {
  if (showingTriaged || (alertGroup.triaged.count === 0)) return false;
  return alertIndex === alertGroup.alerts.findIndex(a => !a.bugId);
};

AlertsTable.compareAlerts = (alertA, alertB, sortColumn) => {
  let valueA = alertA[sortColumn];
  let valueB = alertB[sortColumn];
  if (sortColumn === 'percentDeltaValue') {
    valueA = Math.abs(valueA);
    valueB = Math.abs(valueB);
  }
  if (typeof valueA === 'string') return valueA.localeCompare(valueB);
  return valueA - valueB;
};

AlertsTable.sortGroups = (
    alertGroups, sortColumn, sortDescending, showingTriaged) => {
  const factor = sortDescending ? -1 : 1;
  if (sortColumn === 'count') {
    alertGroups = [...alertGroups];
    // See AlertsTable.getExpandGroupButtonLabel_.
    if (showingTriaged) {
      alertGroups.sort((groupA, groupB) =>
        factor * (groupA.alerts.length - groupB.alerts.length));
    } else {
      alertGroups.sort((groupA, groupB) =>
        factor * ((groupA.alerts.length - groupA.triaged.count) -
          (groupB.alerts.length - groupB.triaged.count)));
    }
  } else if (sortColumn === 'triaged') {
    alertGroups = [...alertGroups];
    alertGroups.sort((groupA, groupB) =>
      factor * (groupA.triaged.count - groupB.triaged.count));
  } else {
    alertGroups = alertGroups.map(group => {
      const alerts = Array.from(group.alerts);
      alerts.sort((alertA, alertB) => factor * AlertsTable.compareAlerts(
          alertA, alertB, sortColumn));
      return {
        ...group,
        alerts,
      };
    });
    alertGroups.sort((groupA, groupB) => factor * AlertsTable.compareAlerts(
        groupA.alerts[0], groupB.alerts[0], sortColumn));
  }
  return alertGroups;
};

AlertsTable.DASHES = '-'.repeat(5);
const PLACEHOLDER_ALERT_GROUPS = [];
AlertsTable.placeholderAlertGroups = () => {
  if (PLACEHOLDER_ALERT_GROUPS.length) return PLACEHOLDER_ALERT_GROUPS;
  for (let i = 0; i < 5; ++i) {
    PLACEHOLDER_ALERT_GROUPS.push({
      isSelected: false,
      triaged: {
        count: 0,
        isExpanded: false,
      },
      alerts: [
        {
          bugId: AlertsTable.DASHES,
          startRevision: AlertsTable.DASHES,
          endRevision: AlertsTable.DASHES,
          suite: AlertsTable.DASHES,
          measurement: AlertsTable.DASHES,
          master: AlertsTable.DASHES,
          bot: AlertsTable.DASHES,
          case: AlertsTable.DASHES,
          deltaValue: 0,
          deltaUnit: tr.b.Unit.byName.countDelta_biggerIsBetter,
          percentDeltaValue: 0,
          percentDeltaUnit:
            tr.b.Unit.byName.normalizedPercentageDelta_biggerIsBetter,
        },
      ],
    });
  }
  return PLACEHOLDER_ALERT_GROUPS;
};

AlertsTable.reducers = {
  sort: (state, action, rootState) => {
    if (!state ||
        (state.alertGroups === AlertsTable.placeholderAlertGroups())) {
      return state;
    }
    const sortDescending = state.sortDescending ^ (state.sortColumn ===
        action.sortColumn);
    const alertGroups = AlertsTable.sortGroups(
        state.alertGroups, action.sortColumn, sortDescending);
    return {
      ...state,
      sortColumn: action.sortColumn,
      sortDescending,
      alertGroups,
    };
  },

  selectAlert: (state, action, rootState) => {
    let alertGroups = state.alertGroups;
    const alertGroup = alertGroups[action.alertGroupIndex];
    let alerts = alertGroup.alerts;
    const alert = alerts[action.alertIndex];
    const isSelected = !alert.isSelected;

    if (action.shiftKey) {
      // [De]select all alerts between previous selected alert and |alert|.
      // Deep-copy alerts so that we can freely modify them.
      // Copy references to individual alerts out of their groups to reflect
      // the flat list of checkboxes that the user sees.
      const flatList = [];
      alertGroups = alertGroups.map(g => {
        return {
          ...g,
          alerts: g.alerts.map(a => {
            const clone = {...a};
            flatList.push(clone);
            return clone;
          }),
        };
      });
      // Find the indices of the previous selected alert and |alert| in
      // flatList.
      const indices = new tr.b.math.Range();
      const keys = [state.previousSelectedAlertKey, alert.key];
      for (let i = 0; i < flatList.length; ++i) {
        if (keys.includes(flatList[i].key)) indices.addValue(i);
      }
      if (state.previousSelectedAlertKey === undefined) indices.addValue(0);
      // Set isSelected for all alerts that appear in the table between the
      // previous selected alert and |alert|.
      for (let i = indices.min; i <= indices.max; ++i) {
        flatList[i].isSelected = isSelected;
      }
    } else {
      let toggleAll = false;
      if (!alertGroup.isExpanded) {
        if (state.showingTriaged) {
          toggleAll = action.alertIndex === 0;
        } else {
          toggleAll = action.alertIndex === alertGroup.alerts.findIndex(
              a => !a.bugId);
        }
      }
      if (toggleAll) {
        alerts = alerts.map(alert => {
          if (!state.showingTriaged && alert.bugId) return alert;
          return {
            ...alert,
            isSelected,
          };
        });
      } else {
        // Only toggle this alert.
        alerts = setImmutable(
            alerts, `${action.alertIndex}.isSelected`, isSelected);
      }

      alertGroups = setImmutable(
          state.alertGroups, `${action.alertGroupIndex}.alerts`, alerts);
    }

    const selectedAlertsCount = AlertsTable.getSelectedAlerts(
        alertGroups).length;
    return {
      ...state,
      alertGroups,
      previousSelectedAlertKey: alert.key,
      selectedAlertsCount,
    };
  },

  selectAllAlerts: (state, action, rootState) => {
    if (!state) return state;
    const select = (state.selectedAlertsCount === 0);
    const alertGroups = state.alertGroups.map(alertGroup => {
      return {
        ...alertGroup,
        alerts: alertGroup.alerts.map(alert => {
          return {
            ...alert,
            isSelected: select,
          };
        }),
      };
    });
    return {
      ...state,
      alertGroups,
      selectedAlertsCount: AlertsTable.getSelectedAlerts(alertGroups).length,
    };
  },
};

ElementBase.register(AlertsTable);
