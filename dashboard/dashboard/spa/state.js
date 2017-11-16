/*
Copyright 2017 The Chromium Authors. All rights reserved.
Use of this source code is governed by a BSD-style license that can be
found in the LICENSE file.
*/
'use strict';

const DEFAULT_STATE = {
  sections: [],
};

const NEW_CHART_SECTION_STATE = {
  type: 'chart',
  isLoading: false,
};

const NEW_ALERTS_SECTION_STATE = {
  type: 'alerts',
  rows: [],
  isLoading: false,
  showingImprovements: false,
  showingTriaged: false,
  sheriffList: [
    "ARC Perf Sheriff",
    "Angle Perf Sheriff",
    "Binary Size Sheriff",
    "Blink Memory Mobile Sheriff",
    "Chrome OS Graphics Perf Sheriff",
    "Chrome OS Installer Perf Sheriff",
    "Chrome OS Perf Sheriff",
    "Chrome Perf Accessibility Sheriff",
    "Chromium Perf AV Sheriff",
    "Chromium Perf Sheriff",
    "Chromium Perf Sheriff - Sub-series",
    "CloudView Perf Sheriff",
    "Cronet Perf Sheriff",
    "Jochen",
    "Mojo Perf Sheriff",
    "NaCl Perf Sheriff",
    "Network Service Sheriff",
    "OWP Storage Perf Sheriff",
    "Oilpan Perf Sheriff",
    "Pica Sheriff",
    "Power Perf Sheriff",
    "Service Worker Perf Sheriff",
    "Tracing Perftests Sheriff",
    "V8 Memory Perf Sheriff",
    "V8 Perf Sheriff",
    "WebView Perf Sheriff",
  ],
};

const NEW_RELEASING_SECTION_STATE = {
  type: 'releasing',
  isLoading: false,
};

function bindSectionState(type, name) {
  const obj = {};
  obj[name] = {
    type,
    statePath(state) {
      if (!state.sections[this.sectionId]) return undefined;
      return state.sections[this.sectionId][name];
    }
  };
  return obj;
}
