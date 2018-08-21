/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  function deepFreeze(o) {
    Object.freeze(o);
    for (const [name, value] of Object.entries(o)) {
      if (typeof(value) !== 'object') continue;
      if (Object.isFrozen(value)) continue;
      if (value instanceof tr.b.Unit) continue;
      deepFreeze(value);
    }
  }

  function isElementChildOf(el, potentialParent) {
    if (el === potentialParent) return false;
    while (Polymer.dom(el).parentNode) {
      if (el === potentialParent) return true;
      el = Polymer.dom(el).parentNode;
    }
    return false;
  }

  function getActiveElement() {
    let element = document.activeElement;
    while (element !== null && element.shadowRoot) {
      element = element.shadowRoot.activeElement;
    }
    return element;
  }

  function afterRender() {
    return new Promise(resolve => {
      Polymer.RenderStatus.afterNextRender({}, () => {
        resolve();
      });
    });
  }

  function timeout(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  function animationFrame() {
    return new Promise(resolve => requestAnimationFrame(resolve));
  }

  function idle() {
    new Promise(resolve => requestIdleCallback(resolve));
  }

  function measureTrace() {
    const events = [];
    const loadTimes = Object.entries(performance.timing.toJSON()).filter(p =>
      p[1] > 0);
    loadTimes.sort((a, b) => a[1] - b[1]);
    const start = loadTimes.shift()[1];
    for (const [name, timeStamp] of loadTimes) {
      events.push({
        name: 'load:' + name,
        start,
        end: timeStamp,
        duration: timeStamp - start,
      });
    }
    for (const measure of performance.getEntriesByType('measure')) {
      const name = measure.name.replace(/[ \.]/g, ':').replace(
          ':reducers:', ':').replace(':actions:', ':');
      events.push({
        name,
        start: measure.startTime,
        duration: measure.duration,
        end: measure.startTime + measure.duration,
      });
    }
    return events;
  }

  function measureHistograms() {
    const histograms = new tr.v.HistogramSet();
    const unit = tr.b.Unit.byName.timeDurationInMs_smallerIsBetter;
    for (const event of measureTrace()) {
      let hist = histograms.getHistogramNamed(event.name);
      if (!hist) {
        hist = histograms.createHistogram(event.name, unit, []);
      }
      hist.addSample(event.duration);
    }
    return histograms;
  }

  function measureTable() {
    const table = [];
    for (const hist of measureHistograms()) {
      table.push([hist.average, hist.name]);
    }
    table.sort((a, b) => (b[0] - a[0]));
    return table.map(p =>
      parseInt(p[0]).toString().padEnd(6) + p[1]).join('\n');
  }

  /* Processing results can be costly. Help callers batch process
   * results by waiting a bit to see if more promises resolve.
   * This is similar to Polymer.Debouncer, but as an async generator.
   * Usage:
   * async function fetchThings(things) {
   *   const responses = things.map(thing => new ThingRequest(thing).response);
   *   for await (const {results, errors} of cp.batchResponses(responses)) {
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
   * |tasks| is expected to be an array of promises or asynchronous iterators.
   * Promises do not have to be cp.RequestBase.response.
   */
  async function* batchResponses(tasks, opt_getDelayPromise) {
    let results = [];
    let errors = [];

    // aggregate wraps a promise or async iterator to aggregate their results
    // and errors into the arrays above since they do not have access to them
    // themselves. Returns a promise if the async iterator is not done,
    // `undefined` otherwise.
    function aggregate(task) {
      return (async() => {
        const isIterator = typeof task.next === 'function';
        const isPromise = task instanceof Promise;
        if (!isIterator && !isPromise) {
          throw new TypeError(`Task is of invalid type: ${typeof task}`);
        }

        try {
          if (isPromise) {
            results.push(await task);
            return;
          }

          // Task must be an asynchronous iterator.
          const { value, done } = await task.next();
          if (!done) {
            results.push(value);
            return smartPromisify(task);
          }
        } catch (err) {
          errors.push(err);
        }
      })();
    }

    const promises = [];

    // Promises need to remove themselves from the above `promises` array so we
    // don't race them again.
    function autoRemove(promise) {
      const self = (async() => {
        const next = await promise;
        if (next) {
          promises.push(removeSelf(next));
        }
        const index = promises.indexOf(self);
        promises.splice(index, 1);
      })();
      return self;
    }

    for (const task of tasks) {
      promises.push(autoRemove(aggregate(task)));
    }

    let timeToYield = 0;
    let timeoutPromise;

    while (promises.length) {
      await Promise.race(timeoutPromise ? [timeoutPromise, ...promises] :
        promises);

      if (!timeoutPromise) {
        timeoutPromise = (async() => {
          await timeout(timeToYield);
          timeoutPromise.isResolved = true;
        })();
        timeoutPromise.isResolved = false;
        continue;
      }

      if (!timeoutPromise.isResolved) continue;

      // The delay promise resolved, indiciating we need to send out results.
      // Measure how long it takes the caller to process yielded results to
      // avoid overloading the caller the next time around.
      const startTime = performance.now();
      yield {results, errors};
      timeToYield = performance.now() - startTime;

      results = [];
      errors = [];
      timeoutPromise = undefined;
    }

    yield {results, errors};
  }

  return {
    afterRender,
    animationFrame,
    batchResponses,
    deepFreeze,
    isElementChildOf,
    getActiveElement,
    idle,
    measureHistograms,
    measureTable,
    measureTrace,
    timeout,
  };
});
