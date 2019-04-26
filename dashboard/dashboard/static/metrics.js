/* Copyright 2019 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

window.METRICS = new class extends window.chops.tsmon.TSMonClient {
  constructor() {
    super();

    this.pageLoad_ = this.cumulativeDistribution(
        'chromeperf/load/page',
        'page loadEventEnd - fetchStart',
        {}, new Map());

    this.chartLoadStart_ = undefined;
    this.chartLoad_ = this.cumulativeDistribution(
        'chromeperf/load/chart',
        'chart load latency',
        {}, new Map());

    this.alertsLoadStart_ = undefined;
    this.alertsLoad_ = this.cumulativeDistribution(
        'chromeperf/load/alerts',
        'alerts load latency',
        {}, new Map());

    this.menuLoadStart_ = undefined;
    this.menuLoad_ = this.cumulativeDistribution(
        'chromeperf/load/menu',
        'menu load latency',
        {}, new Map());

    this.chartActionStart_ = undefined;
    this.chartAction_ = this.cumulativeDistribution(
        'chromeperf/action/chart',
        'timeseries picker activity duration',
        {}, new Map());

    this.triageActionStart_ = undefined;
    this.triageAction_ = this.cumulativeDistribution(
        'chromeperf/action/triage',
        'alert triage latency',
        {}, new Map());
  }

  onLoad() {
    const ms = performance.timing.loadEventEnd - performance.timing.fetchStart;
    const fields = new Map();
    this.pageLoad_.add(ms, fields);
  }

  startLoadChart() {
    this.chartLoadStart_ = performance.now();
  }

  endLoadChart() {
    if (this.chartLoadStart_ === undefined) return;
    const ms = performance.now() - this.chartLoadStart_;
    const fields = new Map();
    this.chartLoad_.add(ms, fields);
    this.chartLoadStart_ = undefined;
  }

  startLoadAlerts() {
    this.alertsLoadStart_ = performance.now();
  }

  endLoadAlerts() {
    if (this.alertsLoadStart_ === undefined) return;
    const ms = performance.now() - this.alertsLoadStart_;
    const fields = new Map();
    this.alertsLoad_.add(ms, fields);
    this.alertsLoadStart_ = undefined;
  }

  startLoadMenu() {
    this.menuLoadStart_ = performance.now();
  }

  endLoadMenu() {
    if (this.menuLoadStart_ === undefined) return;
    const ms = performance.now() - this.menuLoadStart_;
    const fields = new Map();
    this.menuLoad_.add(ms, fields);
    this.menuLoadStart_ = undefined;
  }

  startChartAction() {
    this.chartActionStart_ = performance.now();
  }

  endChartAction() {
    if (this.chartActionStart_ === undefined) return;
    const ms = performance.now() - this.chartActionStart_;
    const fields = new Map();
    this.chartAction_.add(ms, fields);
    this.chartActionStart_ = undefined;
  }

  startTriage() {
    this.triageActionStart_ = performance.now();
  }

  endTriage() {
    if (this.triageActionStart_ === undefined) return;
    const ms = performance.now() - this.triageActionStart_;
    const fields = new Map();
    this.triageAction_.add(ms, fields);
    this.triageActionStart_ = undefined;
  }
};

window.addEventListener('load', () => setTimeout(() => METRICS.onLoad(), 1000));
