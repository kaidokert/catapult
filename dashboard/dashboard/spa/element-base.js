/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

tr.exportTo('cp', () => {
  const ReduxMixin = PolymerRedux(Redux.createSimpleStore({
    devtools: {
      // Do not record changes automatically when in a production environment.
      shouldRecordChanges: !window.IS_PRODUCTION,

      // Increase the maximum number of actions stored in the history tree. The
      // oldest actions are removed once maxAge is reached.
      maxAge: 75,
    },
  }));

  /*
   * This base class mixes Polymer.Element with Polymer-Redux and provides
   * utility functions to help data-bindings in elements perform minimal
   * computation without computed properties.
   */
  class ElementBase extends ReduxMixin(Polymer.Element) {
    constructor() {
      super();
      this.debounceJobs_ = new Map();
    }

    add_() {
      let sum = arguments[0];
      for (const arg of Array.from(arguments).slice(1)) {
        sum += arg;
      }
      return sum;
    }

    isEqual_() {
      const test = arguments[0];
      for (const arg of Array.from(arguments).slice(1)) {
        if (arg !== test) return false;
      }
      return true;
    }

    plural_(count, pluralSuffix = 's', singularSuffix = '') {
      return cp.plural(count, pluralSuffix, singularSuffix);
    }

    lengthOf_(seq) {
      if (seq === undefined) return 0;
      if (seq === null) return 0;
      if (seq instanceof Array || typeof(seq) === 'string') return seq.length;
      if (seq instanceof Map || seq instanceof Set) return seq.size;
      if (seq instanceof tr.v.HistogramSet) return seq.length;
      return Object.keys(seq).length;
    }

    isMultiple_(seq) {
      return this.lengthOf_(seq) > 1;
    }

    isEmpty_(seq) {
      return this.lengthOf_(seq) === 0;
    }

    /**
     * Wrap Polymer.Debouncer in a friendlier syntax.
     *
     * @param {*} jobName
     * @param {Function()} callback
     * @param {Object=} asyncModule See Polymer.Async.
     */
    debounce(jobName, callback, opt_asyncModule) {
      const asyncModule = opt_asyncModule || Polymer.Async.microTask;
      this.debounceJobs_.set(jobName, Polymer.Debouncer.debounce(
          this.debounceJobs_.get(jobName), asyncModule, callback));
    }

    // This is used to bind state properties in `buildProperties()` in utils.js.
    identity_(x) { return x; }
  }

  if (window.location.hostname === 'localhost') {
    // timeReducer should appear before freezingReducer so that the timing
    // doesn't include the overhead from freezingReducer. statePathReducer must
    // be last because it changes the function signature.
    Redux.DEFAULT_REDUCER_WRAPPERS.splice(1, 0, Redux.freezingReducer);
  }

  ElementBase.register = subclass => {
    subclass.is = Polymer.CaseMap.camelToDashCase(subclass.name).substr(1);
    customElements.define(subclass.is, subclass);
    if (subclass.reducers) {
      Redux.registerReducers(subclass.reducers, [
        Redux.renameReducer(subclass.name + '.'),
        ...Redux.DEFAULT_REDUCER_WRAPPERS,
      ]);
    }
    timeActions(subclass);
    timeEventListeners(subclass);
  };

  function timeActions(cls) {
    if (!cls.actions) return;
    for (const [name, action] of Object.entries(cls.actions)) {
      const debugName = `${cls.name}.actions.${name}`;
      const actionReplacement = (...args) => {
        const thunk = action(...args);
        Object.defineProperty(thunk, 'name', {value: debugName});
        const thunkReplacement = async(dispatch, getState) => {
          const mark = Timing.mark('action', debugName);
          try {
            return await thunk(dispatch, getState);
          } finally {
            mark.end();
          }
        };
        Object.defineProperty(thunkReplacement, 'name', {
          value: 'timeActions:wrapper',
        });
        return thunkReplacement;
      };
      actionReplacement.implementation = action;
      Object.defineProperty(actionReplacement, 'name', {value: debugName});
      cls.actions[name] = actionReplacement;
    }
  }

  function timeEventListeners(cls) {
    // Polymer handles the addEventListener() calls, this method just wraps
    // 'on*_' methods with Timing marks.
    for (const name of Object.getOwnPropertyNames(cls.prototype)) {
      if (!name.startsWith('on')) continue;
      if (!name.endsWith('_')) continue;
      (() => {
        const wrapped = cls.prototype[name];
        const debugName = cls.name + '.' + name;

        cls.prototype[name] = async function eventListenerWrapper(event) {
          // Measure the time from when the browser receives the event to when
          // we receive the event.
          if (event && event.timeStamp) {
            Timing.mark('listener', debugName, event.timeStamp).end();
          }

          // Measure the first paint latency by starting the event listener
          // without awaiting it.
          const firstPaintMark = Timing.mark('firstPaint', debugName);
          const resultPromise = wrapped.call(this, event);
          (async() => {
            await cp.afterRender();
            firstPaintMark.end();
          })();

          const result = await resultPromise;

          const lastPaintMark = Timing.mark('lastPaint', debugName);
          (async() => {
            await cp.afterRender();
            lastPaintMark.end();
          })();

          return result;
        };
      })();
    }
  }

  return {ElementBase};
});
