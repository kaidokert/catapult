/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('service-worker.js');
}

// Use native shadow DOM to encapsulate web components instead of the slower
// shady DOM.
window.Polymer = {dom: 'shadow'};
window.addEventListener('load', () => {
  const loadTimes = Object.entries(performance.timing.toJSON()).filter(p =>
    p[1] > 0);
  loadTimes.sort((a, b) => a[1] - b[1]);
  const start = loadTimes.shift()[1];
  for (const [name, timeStamp] of loadTimes) {
    tr.b.Timing.mark('load', name, start).end(timeStamp);
  }
});
