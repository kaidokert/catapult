/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class TriageExisting extends cp.ElementBase {
    static get is() { return 'triage-existing'; }

    static get properties() {
      return {
        ...cp.ElementBase.statePathProperties('statePath', {
          bugId: {type: String},
          isOpen: {type: Boolean},
          nonOverlappingRecentBugs: {type: Boolean},
          recentBugs: {type: Array},
        }),
        disabled: {type: Boolean},
      };
    }
  }

  cp.ElementBase.register(TriageExisting);

  return {
    TriageExisting,
  };
});
