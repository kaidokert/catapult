/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class TriageNew extends cp.ElementBase {
    static get is() { return 'triage-new'; }

    static get properties() {
      return {
        ...cp.ElementBase.statePathProperties('statePath', {
          cc: {type: String},
          components: {type: Array},
          description: {type: String},
          isOpen: {type: Boolean},
          labels: {type: Array},
          owner: {type: String},
          summary: {type: String},
        }),
        disabled: {type: Boolean},
      };
    }
  }

  cp.ElementBase.register(TriageNew);

  return {
    TriageNew,
  };
});
