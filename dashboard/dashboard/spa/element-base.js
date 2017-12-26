/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

tr.exportTo('cp', () => {
  // Reducers MUST NOT have side effects.
  // Reducers MUST NOT modify state.
  // Reducers MUST return a new object.
  // Reducers MAY copy properties from state.

  // Action creators SHOULD contain all async code in the app.
  // Action creators MAY have side-effects.
  // Action creators MAY take any number of parameters.

  // Maps from string "action type" to synchronous
  // function(!Object state, !Object action):!Object state.
  const REDUCERS = new Map();

  // In order for ElementBase to be useful in multiple different apps, the
  // default state must be empty, and each app must populate it.
  const DEFAULT_STATE = {};

  // Forwards (state, action) to the registered reducer function in the REDUCERS
  // Map.
  function rootReducer(state, action) {
    if (state === undefined) return DEFAULT_STATE;
    if (!REDUCERS.has(action.type)) return state;
    return REDUCERS.get(action.type)(state, action);
  }

  // This is all that is needed from redux-thunk to enable asynchronous action
  // creators.
  // https://tur-nr.github.io/polymer-redux/docs#async-actions
  const THUNK = ({dispatch, getState}) => next => action => {
    if (typeof action === 'function') {
      return action(dispatch, getState);
    }
    return next(action);
  };

  const STORE = Redux.createStore(
      rootReducer, DEFAULT_STATE, Redux.applyMiddleware(THUNK));

  const ReduxMixin = PolymerRedux(STORE);

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

    _add() {
      let sum = arguments[0];
      for (const arg of Array.from(arguments).slice(1)) {
        sum += arg;
      }
      return sum;
    }

    _concat() {
      const result = [];
      for (const arg of arguments) {
        if (arg instanceof Array) {
          result.push.apply(result, arg);
        } else {
          result.push(arg);
        }
      }
      return result;
    }

    _eq() {
      const test = arguments[0];
      for (const arg of Array.from(arguments).slice(1)) {
        if (arg !== test) return false;
      }
      return true;
    }

    _len(seq) {
      if (seq === undefined) return 0;
      if (seq === null) return 0;
      if (seq instanceof Array) return seq.length;
      if (seq instanceof Map || seq instanceof Set) return seq.size;
      if (seq instanceof tr.v.HistogramSet) return seq.length;
      return Object.keys(seq).length;
    }

    _empty(seq) {
      return this._len(seq) === 0;
    }

    _plural(num) {
      return num === 1 ? '' : 's';
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

    static statePathProperties(statePathName, configs) {
      const properties = {};
      properties[statePathName] = {
        type: String,
      };

      for (const [name, config] of Object.entries(configs)) {
        properties[name] = {
          ...config,
          statePath(state) {
            return ElementBase.getStateAtPath(
                state, this[statePathName] + '.' + name);
          },
        };
      }

      return properties;
    }

    static getStateAtPath(state, path) {
      for (const name of path) {
        if (state === undefined) return undefined;
        state = state[name];
      }
      return state;
    }

    static setStateAtPath(state, path, delta) {
      let branch = state;
      const branches = [];
      for (const name of path) {
        branch = branch[name];
        branches.push(branch);
      }
      for (let i = path.length - 1; i >= 0; --i) {
        const name = path[i];
        if (branches[i] instanceof Array) {
          const branchIndex = parseInt(name);
          const nextDelta = Array.from(branches[i]);
          nextDelta.splice(branchIndex, 1, delta);
          delta = nextDelta;
        } else {
          const nextDelta = {};
          nextDelta[name] = {...branches[i], ...delta};
          delta = nextDelta;
        }
      }
      return {...state, ...delta};
    }

    static register(subclass) {
      customElements.define(subclass.is, subclass);

      for (const [name, reducer] of Object.entries(subclass.reducers)) {
        REDUCERS.set(`${subclass.is}.${name}`, reducer);
      }
    }

    static afterRender() {
      return new Promise(resolve => {
        Polymer.RenderStatus.afterNextRender({}, () => {
          resolve();
        });
      });
    }

    static beforeRender() {
      return new Promise(resolve => {
        Polymer.RenderStatus.beforeNextRender({}, () => {
          resolve();
        });
      });
    }

    static statePathReducer(reducer) {
      return (state, action) => {
        if (typeof action.statePath !== 'string') {
          throw new Error(`Invalid statePath ${action.statePath}`);
        }
        const branch = ElementBase.getStateAtPath(state, action.statePath);
        const delta = reducer(branch, action);
        return ElementBase.setStateAtPath(state, action.statePath, delta);
      };
    }

    static async measureInputLatency(groupName, functionName, event) {
      const mark = tr.b.Timing.mark(
          groupName, functionName,
          event.timeStamp || event.detail.sourceEvent.timeStamp);
      await afterRender();
      mark.end();
    }
  }

  REDUCERS.set('element-base.setStateAtPath', ElementBase.statePathReducer(
      (state, action) => action.delta));

  return {
    ElementBase,
  };
});
