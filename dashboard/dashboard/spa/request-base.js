/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class RequestBase {
    constructor(options) {
      this.promise_ = undefined;

      this.method_ = 'GET';
      this.headers_ = new Headers(options.headers);
      this.body_ = undefined;

      this.abortController_ = options.abortController;
      if (!this.abortController_ && window.AbortController) {
        this.abortController_ = new window.AbortController();
      }
      this.signal_ = undefined;
      if (this.abortController_) {
        this.signal_ = this.abortController_.signal;
      }
    }

    get response() {
      // Don't call fetch_ before the subclass constructor finishes.
      if (!this.promise_) this.promise_ = this.fetch_();
      return this.promise_;
    }

    async addAuthorizationHeaders_() {
      const headers = await cp.authorizationHeaders();
      for (const [name, value] of headers) {
        this.headers_.set(name, value);
      }
    }

    async fetch_() {
      await this.addAuthorizationHeaders_();

      if (cp.IS_DEBUG) {
        // Simulate network latency in order to test loading state e.g. progress
        // bars.
        await cp.ElementBase.timeout(1000);
        return this.postProcess_(await this.localhostResponse_());
      }

      const mark = tr.b.Timing.mark('fetch', this.constructor.name);
      const response = await fetch(this.url_, {
        body: this.body_,
        headers: this.headers_,
        method: this.method_,
        signal: this.signal_,
      });
      mark.end();
      return this.postProcess_(await response.json());
    }

    abort() {
      if (!this.abortController_) return;
      this.abortController_.abort();
    }

    get url_() {
      throw new Error('subclasses must override get url_()');
    }

    async localhostResponse_() {
      return {};
    }

    postProcess_(json) {
      return json;
    }
  }

  class CacheBase {
    constructor(options, dispatch, getState) {
      this.options_ = options;
      this.dispatch_ = dispatch;
      this.getState_ = getState;
      this.rootState_ = this.getState_();
      this.cacheKey_ = undefined; // will be computed in read()
    }

    // cacheStatePath_ returns the state path to the location of the cached
    // data.
    get cacheStatePath_() {
      // Subclasses may override this to return a statePath. read() will ensure
      // that the statePath exists.
    }

    // defaultCacheState_ provides a sensible default for data during
    // initialization.
    get defaultCacheState_() {
      // Subclasses may override this to return a different default cache state.
    }

    // computeCacheKey_ returns a unique string for the request. This is used to
    // store the data in a predictable location in the Redux state.
    computeCacheKey_() {
      throw new Error('subclasses must override computeCacheKey_');
    }

    // isInCache_ returns true if existing data exists, otherwise false.
    get isInCache_() {
      throw new Error('subclasses must override isInCache_()');
    }

    // createRequest_ returns an instantiation of any class that extends from
    // cp.RequestBase.
    createRequest_() {
      throw new Error('subclasses must override createRequest_()');
    }

    async fetch_() {
      const request = this.createRequest_();

      const completion = (async() => {
        const response = await request.response;
        this.onFinishRequest_(response);
        return response;
      })();
      this.onStartRequest_(request, completion);
      return await completion;
    }

    onStartRequest_(request, completion) {
      // Subclasses may override this to store request or request.response in
      // the redux store.
    }

    onFinishRequest_(response) {
      // Subclasses may override this to store response in the redux store.
    }

    ensureCacheState_() {
      const cacheStatePath = this.cacheStatePath_;
      if (cacheStatePath === undefined) return;
      if (Polymer.Path.get(this.rootState_, cacheStatePath)) return;
      cp.ElementBase.actions.ensureObject(
          cacheStatePath, this.defaultCacheState_)(
          this.dispatch_, this.getState_);
      this.rootState_ = this.getState_();
    }

    // Usage:
    // class FooCache extends CacheBase { ... }
    // const ReadFoo = options => async(dispatch, getState) =>
    //   await new FooCache(options, dispatch, getState).read();
    // const foo = await dispatch(ReadFoo(options))
    async read() {
      this.ensureCacheState_();

      this.cacheKey_ = this.computeCacheKey_();
      if (this.cacheKey_ instanceof Promise) {
        // Some caches need to use async APIs to compute their cacheKey_,
        // some caches need read() to call onStartRequest_() before the first
        // await.
        this.cacheKey_ = await this.cacheKey_;
      }

      if (this.isInCache_) {
        return await this.readFromCache_();
      }

      return await this.fetch_();
    }
  }

  /* Processing results can be costly. Help callers batch process
   * results by waiting a bit to see if more promises resolve.
   * This is similar to Polymer.Debouncer, but as an async generator.
   * Usage:
   * async function fetchThings(things) {
   *   const responses = things.map(thing => new ThingRequest(thing).response);
   *   for await (const {results, errors} of
   *              cp.RequestBase.batchResponses(responses)) {
   *     dispatch({
   *       type: ...mergeAndDisplayThings.typeName,
   *       results, errors,
   *     });
   *   }
   *   dispatch({
   *     type: ...doneReceivingThings.typeName,
   *   });
   * }
   *
   * |tasks| is expected to be a mixed array of promises, iterators, and
   * asynchronous iterators. Promises do not have to be cp.RequestBase.response.
   */
  RequestBase.batchResponses = async function* (tasks, opt_getDelayPromise) {
    const getDelayPromise = opt_getDelayPromise || (() =>
      cp.ElementBase.timeout(500));

    const promises = [];
    let delay;
    let results = [];
    let errors = [];

    function promisifyIterator(reader) {
      const promise = (async() => {
        try {
          const { value, done } = await Promise.resolve(reader.next());
          if (!done) {
            results.push(value);
            const next = promisifyIterator(reader);
            promises.push(next);
          }
        } catch (err) {
          errors.push(err);
        } finally {
          const index = promises.indexOf(promise);
          promises.splice(index, 1);
        }
      })();
      return promise;
    }

    function wrapPromise(dumpPromise) {
      const promise = (async() => {
        try {
          results.push(await dumpPromise);
        } catch (err) {
          errors.push(err);
        } finally {
          const index = promises.indexOf(promise);
          promises.splice(index, 1);
        }
      })();
      return promise;
    }

    for (const task of tasks) {
      if (typeof task.next === 'function') {
        // Task is either a synchronous or asynchronous iterator.
        promises.push(promisifyIterator(task));
      } else {
        // Task has to be a promise.
        promises.push(wrapPromise(task));
      }
    }

    while (promises.length) {
      if (delay) {
        await Promise.race([delay, ...promises]);
        if (delay.isResolved) {
          yield {results, errors};
          results = [];
          errors = [];
          delay = undefined;
        }
      } else {
        await Promise.race(promises);
        delay = (async() => {
          await getDelayPromise();
          delay.isResolved = true;
        })();
        delay.isResolved = false;
      }
    }

    yield {results, errors};
  };

  return {
    CacheBase,
    RequestBase,
  };
});
