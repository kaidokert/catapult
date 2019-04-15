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
      </style>

      <template is="dom-if" if="[[isValidBugId_(bugId)]]">
        <a href="[[crbug_(bugId)]]" target="_blank">[[bugId]]</a>
        <iron-icon icon="cp:edit"></iron-icon>
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
          <td>%&#916;[[statistic]]</td>
          <td>
            <scalar-span
                value="[[percentDeltaValue]]"
                unit="[[percentDeltaUnit]]"
                maximum-fraction-digits="1">
            </scalar-span>
          </td>
        <tr>
      </table>

      Revision: [[startRevision]]-[[endRevision]]
      <iron-icon icon="cp:edit"></iron-icon>
      <cp-input id="start-revision" value="[[startRevision]]"></cp-input>
      <cp-input id="end-revision" value="[[endRevision]]"></cp-input>
      <raised-button id="save">Save</raised-button>

      <!-- TODO bugComponents, bugLabels -->
    `;
  }

  isValidBugId_(bugId) {
    return bugId > 0;
  }

  crbug_(bugId) {
    return cp.crbug(bugId);
  }
}

AlertDetail.State = {
  bugId: options => 0,
  deltaUnit: options => undefined,
  deltaValue: options => 0,
  key: options => '',
  percentDeltaUnit: options => undefined,
  percentDeltaValue: options => 0,
  statistic: options => '',
  startRevision: options => 0,
  endRevision: options => 0,
};
AlertDetail.properties = cp.buildProperties('state', AlertDetail.State);
AlertDetail.buildState = options => cp.buildState(AlertDetail.State, options);

AlertDetail.actions = {
};

AlertDetail.reducers = {
};

cp.ElementBase.register(AlertDetail);
