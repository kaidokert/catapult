/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  // ServiceWorkerListener creates a communication channel between the
  // application and the service worker. Use as an asynchronous iterator.
  // See https://jakearchibald.com/2017/async-iterators-and-generators/
  class ServiceWorkerListener {
    constructor(url) {
      this.channel = new BroadcastChannel(url);
    }
    [Symbol.asyncIterator]() {
      return this;
    }
    next() {
      const { serviceWorker } = navigator;

      // Listen to the Service Worker for specific messages.
      return new Promise((resolve, reject) => {
        const handler = event => {
          this.channel.removeEventListener('message', handler);
          const { type, payload } = event.data;

          switch (type) {
            case 'RESULTS':
              resolve({
                value: payload,
                done: false,
              });
              return;
            case 'DONE':
              this.channel.close();
              resolve({
                done: true,
              });
              return;
            default:
              reject(new Error(`Unknown Service Worker message type: ${type}`));
          }
        };

        this.channel.addEventListener('message', handler);
      });
    }
  }

  return {
    ServiceWorkerListener,
  };
});

