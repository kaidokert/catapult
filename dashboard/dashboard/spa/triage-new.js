/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class TriageNew extends cp.ElementBase {
    static get properties() {
      return cp.ElementBase.statePathProperties('statePath', {
        cc: {type: String},
        components: {type: Array},
        description: {type: String},
        isOpen: {type: Boolean},
        labels: {type: Array},
        owner: {type: String},
        summary: {type: String},
      });
    }

    onCancel_(event) {
      this.dispatch('cancel', this.statePath);
    }
  }

  TriageNew.actions = {
    cancel: statePath => async (dispatch, getState) => {
      dispatch(cp.ElementBase.actions.updateObject(
          statePath, {isOpen: false}));
    },
  };

  TriageNew.newState = (alerts, userEmail) => {
    return {
      cc: userEmail,
      components: TriageNew.collectComponents(alerts),
      description: '',
      isOpen: true,
      labels: TriageNew.collectLabels(alerts),
      owner: '',
      summary: TriageNew.summarize(alerts),
    };
  };

  TriageNew.summarize = alerts => {
    const pctDeltaRange = new tr.b.math.Range();
    const revisionRange = new tr.b.math.Range();
    let testSuites = new Set();
    cp.todo('handle non-numeric revisions');
    for (const alert of alerts) {
      if (!alert.improvement) {
        pctDeltaRange.addValue(Math.abs(100 * alert.percentDeltaValue));
      }
      revisionRange.addValue(alert.startRevision);
      revisionRange.addValue(alert.endRevision);
      testSuites.add(alert.testSuite);
    }
    testSuites = Array.from(testSuites);
    testSuites.sort((x, y) => x.localeCompare(y));
    testSuites = testSuites.join(',');

    let pctDeltaString = pctDeltaRange.min.toLocaleString(undefined, {
      maximumFractionDigits: 1,
    }) + '%';
    if (pctDeltaRange.min !== pctDeltaRange.max) {
      pctDeltaString += '-' + pctDeltaRange.max.toLocaleString(undefined, {
        maximumFractionDigits: 1,
      }) + '%';
    }

    let revisionString = revisionRange.min;
    if (revisionRange.min !== revisionRange.max) {
      revisionString += ':' + revisionRange.max;
    }

    return `${pctDeltaString} regression in ${testSuites} at ${revisionString}`;
  };

  TriageNew.collectLabels = alerts => {
    let labels = new Set();
    labels.add('Pri-2');
    labels.add('Type-Bug-Regression');
    for (const alert of alerts) {
      for (const label of alert.bugLabels) {
        labels.add(label);
      }
    }
    labels = Array.from(labels);
    labels.sort((x, y) => x.localeCompare(y));
    return labels.map(name => {
      return {
        isEnabled: true,
        name,
      };
    });
  };

  TriageNew.collectComponents = alerts => {
    let components = new Set();
    for (const alert of alerts) {
      for (const component of alert.bugComponents) {
        components.add(component);
      }
    }
    components = Array.from(components);
    components.sort((x, y) => x.localeCompare(y));
    return components.map(name => {
      return {
        isEnabled: true,
        name,
      };
    });
  };

  cp.ElementBase.register(TriageNew);

  return {
    TriageNew,
  };
});
