/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  function deferred() {
    const def = {};
    def.promise = new Promise((resolve, reject) => {
      def.resolve = resolve;
      def.reject = reject;
    });
    return def;
  }

  /**
   * ServiceWorkerListener creates a communication channel between the
   * application and the service worker. Use as an asynchronous iterator.
   * See https://jakearchibald.com/2017/async-iterators-and-generators/
   */
  class ServiceWorkerListener {
    constructor(url) {
      this.channel_ = new BroadcastChannel(url);
      this.messageQueue_ = [];
      this.waitingConsumers_ = [];

      if (navigator.serviceWorker.controller === null) {
        // The request is force refresh (Shift + refresh) or there is no
        // active service worker.
        this.done_ = true;
      } else {
        this.done_ = false;
        this.listenOnChannel();
      }
    }
    listenOnChannel() {
      const handler = event => {
        const {type, payload} = event.data;

        switch (type) {
          case 'RESULTS':
            if (this.waitingConsumers_.length) {
              const consumer = this.waitingConsumers_.shift();
              consumer.resolve({ done: false, value: payload });
            } else {
              this.messageQueue_.push({ done: false, value: payload });
            }
            return;
          case 'DONE':
            for (const consumer of this.waitingConsumers_) {
              consumer.resolve({ done: true });
            }
            this.waitingConsumers_ = [];
            this.done_ = true;

            this.channel_.removeEventListener('message', handler);
            this.channel_.close();
            return;
          default:
            throw new Error(`Unknown Service Worker message type: ${type}`);
        }
      };

      this.channel_.addEventListener('message', handler);
    }
    [Symbol.asyncIterator]() {
      return this;
    }
    next() {
      if (this.done_) {
        return Promise.resolve({ done: true });
      }

      if (this.messageQueue_.length) {
        return Promise.resolve({
          done: false,
          value: this.messageQueue_.shift()
        });
      }

      const consumer = deferred();
      this.waitingConsumers_.push(consumer);
      return consumer.promise;
    }
  }

  return {
    ServiceWorkerListener,
  };
});
