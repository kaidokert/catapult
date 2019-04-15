/* Copyright 2019 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

export default class AlertDetail extends cp.ElementBase {
  static get template() {
    return Polymer.html`
      <style>
      </style>

      <a href="">[[bugId]]</a>
      <iron-icon icon="cp:edit"></iron-icon>
      <raised-button id="untriage">Untriage</raised-button>
      <raised-button id="ignore">Ignore</raised-button>
      <cp-input id="bug-id" value="[[bugId]]"></cp-input>
      <raised-button id="save">Save</raised-button>

      <scalar-span
          value="[[alert.deltaValue]]"
          unit="[[alert.deltaUnit]]">
      </scalar-span>

      <scalar-span
          value="[[alert.percentDeltaValue]]"
          unit="[[alert.percentDeltaUnit]]"
          maximum-fraction-digits="1">
      </scalar-span>

      Revision: [[startRevision]]-[[endRevision]]
      <iron-icon icon="cp:edit"></iron-icon>
      <cp-input id="start-revision" value="[[startRevision]]"></cp-input>
      <cp-input id="end-revision" value="[[endRevision]]"></cp-input>
      <raised-button id="save">Save</raised-button>

      <!-- TODO bugComponents, bugLabels -->
    `;
  }
}

AlertDetail.State = {
  bugId: options => 0,
};
AlertDetail.properties = cp.buildProperties('state', AlertDetail.State);
AlertDetail.buildState = options => cp.buildState(AlertDetail.State, options);

AlertDetail.actions = {
};

AlertDetail.reducers = {
};

cp.ElementBase.register(AlertDetail);
