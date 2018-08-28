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
      if (navigator.serviceWorker.controller === null &&
          !ServiceWorkerListener.TESTING) {
        // The request is force refresh (Shift + refresh) or there is no
        // active service worker.
        this.done_ = true;
        return;
      }

      this.done_ = false;
      this.messageQueue_ = [];
      this.waitingConsumers_ = [];
      this.handleMessage_ = this.handleMessage_.bind(this);

      this.channel_ = new BroadcastChannel(url);
      this.channel_.addEventListener('message', this.handleMessage_);
    }

    handleMessage_({data: {type, payload}}) {
      switch (type) {
        case 'RESULTS':
          if (this.waitingConsumers_.length) {
            const consumer = this.waitingConsumers_.shift();
            consumer.resolve({done: false, value: payload});
          } else {
            this.messageQueue_.push({done: false, value: payload});
          }
          return;
        case 'DONE':
          for (const consumer of this.waitingConsumers_) {
            consumer.resolve({done: true});
          }
          this.waitingConsumers_ = [];
          this.done_ = true;

          this.channel_.removeEventListener('message', this.handleMessage_);
          this.channel_.close();
          return;
        default:
          throw new Error(`Unknown Service Worker message type: ${type}`);
      }
    }

    [Symbol.asyncIterator]() {
      return this;
    }

    async next() {
      if (this.done_) {
        return {done: true};
      }

      if (this.messageQueue_.length) {
        return {done: false, value: this.messageQueue_.shift()};
      }

      const consumer = deferred();
      this.waitingConsumers_.push(consumer);
      return await consumer.promise;
    }
  }

  ServiceWorkerListener.TESTING = false;


  return {
    ServiceWorkerListener,
  };
});
