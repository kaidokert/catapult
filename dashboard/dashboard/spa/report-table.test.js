/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import {CHAIN, ENSURE, UPDATE} from './simple-redux.js';
import {ReportTable} from './report-table.js';
import {STORE} from './element-base.js';
import {afterRender} from './utils.js';
import {assert} from 'chai';

suite('report-table', function() {
  async function fixture() {
    const report = document.createElement('report-table');
    report.statePath = 'test';
    await STORE.dispatch(CHAIN(
        ENSURE('test'),
        UPDATE('test', ReportTable.buildState(options()))));
    document.body.appendChild(report);
    await afterRender();
    return report;
  }

  teardown(() => {
    for (const child of document.body.children) {
      if (!child.matches('report-table')) continue;
      document.body.removeChild(child);
    }
  });

  function options() {
    return {
      minRevision: 10,
      maxRevision: 100,
      rows: [
        {
          suite: {
            selectedOptions: ['suite'],
          },
          measurement: {
            selectedOptions: ['measure'],
          },
          bot: {
            selectedOptions: ['bot'],
          },
          case: {
            selectedOptions: ['case'],
          },
          labelParts: [
            {isFirst: true, rowCount: 2, label: 'measure', href: '/'},
          ],
          scalars: [
            {unit: tr.b.Unit.byName.count, value: 2},
            {unit: tr.b.Unit.byName.count, value: 1},
            {unit: tr.b.Unit.byName.countDelta_smallerIsBetter, value: -1},
          ],
        },
      ],
    };
  }

  test('copy', async function() {
    const report = await fixture();
    report.shadowRoot.querySelector('#copy').click();
    assert.isTrue(report.copiedToast.opened);
  });
});
