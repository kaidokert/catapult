/* Copyright 2019 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

export default class AlertDetail extends cp.ElementBase {
  static get template() {
    return Polymer.html`
      <style>
        table {
          width: 100%;
        }
        #triage {
          display: flex;
        }
        #edit-revisions {
          align-items: center;
          display: flex;
        }
        cp-input {
          margin-top: 12px;
          width: 100px;
        }
        #start-revision {
          margin-right: 8px;
        }
      </style>

      <table>
        <tr>
          <td>&#916;[[statistic]]</td>
          <td>
            <scalar-span
                value="[[deltaValue]]"
                unit="[[deltaUnit]]">
            </scalar-span>
          </td>
        </tr>
        <tr>
          <td>%&#916;[[statistic]]</td>
          <td>
            <scalar-span
                value="[[percentDeltaValue]]"
                unit="[[percentDeltaUnit]]"
                maximum-fraction-digits="1">
            </scalar-span>
          </td>
        </tr>
      </table>

      <template is="dom-if" if="[[isValidBugId_(bugId)]]">
        <a href="[[crbug_(bugId)]]" target="_blank">[[bugId]]</a>
        <iron-icon icon="cp:edit"></iron-icon>
        <raised-button id="untriage">Untriage</raised-button>
      </template>

      <template is="dom-if" if="[[isInvalidBugId_(bugId)]]">
        Ignored
        <raised-button id="untriage">Untriage</raised-button>
      </template>

      <template is="dom-if" if="[[!bugId]]">
        <div id="triage">
          <raised-button id="new">
            New Bug
          </raised-button>
          <raised-button id="existing">
            Existing Bug
          </raised-button>
          <raised-button id="ignore">
            Ignore
          </raised-button>
        </div>
      </template>

      <iron-collapse opened="[[!isEditingRevisions]]">
        Revision range: [[startRevision]]-[[endRevision]]
        <iron-icon icon="cp:edit" on-click="onEditRevisions_"></iron-icon>
      </iron-collapse>

      <iron-collapse id="edit-revisions" opened="[[isEditingRevisions]]">
        <cp-input id="start-revision" label="Start" value="[[startRevision]]">
        </cp-input>
        <cp-input id="end-revision" label="End" value="[[endRevision]]">
        </cp-input>
        <raised-button id="save">Save</raised-button>
      </iron-collapse>

      <!-- TODO bugComponents, bugLabels -->
    `;
  }

  connectedCallback() {
    super.connectedCallback();
    if (this.isEditingRevisions === undefined) {
      this.dispatch(Redux.UPDATE(this.statePath, {isEditingRevisions: false}));
    }
  }

  async onEditRevisions_(event) {
    await this.dispatch(Redux.TOGGLE(this.statePath + '.isEditingRevisions'));
  }

  isValidBugId_(bugId) {
    return bugId > 0;
  }

  isInvalidBugId_(bugId) {
    return bugId < 0;
  }

  crbug_(bugId) {
    return cp.crbug(bugId);
  }
}

AlertDetail.State = {
  bugId: options => 0,
  deltaUnit: options => undefined,
  deltaValue: options => 0,
  endRevision: options => 0,
  isEditingRevisions: options => false,
  key: options => '',
  percentDeltaUnit: options => undefined,
  percentDeltaValue: options => 0,
  startRevision: options => 0,
  statistic: options => '',
};
AlertDetail.properties = cp.buildProperties('state', AlertDetail.State);
AlertDetail.buildState = options => cp.buildState(AlertDetail.State, options);

AlertDetail.actions = {
};

AlertDetail.reducers = {
};

cp.ElementBase.register(AlertDetail);
