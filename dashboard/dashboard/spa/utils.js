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
   * |tasks| is expected to be a mixed array of promises and asynchronous
   * iterators. Promises do not have to be cp.RequestBase.response.
   */
  async function* batchResponses(tasks, opt_getDelayPromise) {
    const getDelayPromise = opt_getDelayPromise || (() => timeout(500));

    const promises = [];
    let delay;
    let results = [];
    let errors = [];

    // Aggregates results and errors for promises and asynchronous generators.
    function wrap(task) {
      const promise = (async() => {
        try {
          if (typeof task.next === 'function') {
            // Task is an asynchronous iterator.
            const { value, done } = await task.next();
            if (!done) {
              results.push(value);
              const next = wrap(task);
              promises.push(next);
            }
          } else {
            // Task has to be a promise.
            results.push(await task);
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

    // Convert tasks to promises by "wrapping" them.
    for (const task of tasks) {
      promises.push(wrap(task));
    }

    while (promises.length) {
      if (delay) {
        // Race promises with a delay acting as a timeout for yielding
        // aggregated results and errors.
        await Promise.race([delay, ...promises]);

        // Inform the caller of results/errors then reset everything.
        if (delay.isResolved) {
          yield {results, errors};
          results = [];
          errors = [];
          delay = undefined;
        }
      } else {
        // Wait for the first result to come back, then start a new delay
        // acting as a timeout for yielding aggregated results and errors.
        await Promise.race(promises);
        delay = (async() => {
          await getDelayPromise();
          delay.isResolved = true;
        })();
        delay.isResolved = false;
      }
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
