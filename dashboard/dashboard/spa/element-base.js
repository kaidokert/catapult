/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

tr.exportTo('cp', () => {
  function setImmutableInternal_(obj, path, value, depth) {
    if (obj === undefined) {
      throw new Error(`Invalid obj at ${path}`);
    }
    if (path.length === depth) {
      // Recursive base case.
      if (typeof value === 'function') {
        return value(obj);
      }
      return value;
    }
    let key = path[depth];
    if (Array.isArray(obj)) key = parseInt(key);
    const wrappedValue = setImmutableInternal_(
        obj[key], path, value, depth + 1);
    const clone = Array.isArray(obj) ? Array.from(obj) : {...obj};
    if (Array.isArray(obj)) {
      clone.splice(key, 1, wrappedValue);
    } else {
      clone[key] = wrappedValue;
    }
    return clone;
  }

  /**
   * Like Polymer.Path.set(), but returns a modified clone of root instead of
   * modifying root. |value| may be set to a function in order to compute a
   * new value from the old value efficiently instead of calling both Path.get()
   * and then Path.set().
   *
   * @param {!Object|!Array} root
   * @param {string|!Array} path
   * @param {*|function} value
   * @return {!Object|!Array}
   */
  Polymer.Path.setImmutable = (root, path, value) => {
    if (path === '') {
      path = [];
    } else {
      path = Polymer.Path.split(path);
    }
    return setImmutableInternal_(root, path, value, 0);
  };

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
    /**
     * Subclasses should use this to bind properties to redux state.
     * @param {String} statePathPropertyName Typically 'statePath'.
     * @param {!Object} configs
     * @return {!Object} properties
     */
    static statePathProperties(statePathPropertyName, configs) {
      const properties = {};
      properties[statePathPropertyName] = {};

      for (const [name, config] of Object.entries(configs)) {
        properties[name] = {
          ...config,
          readOnly: true,
          statePath(state) {
            return Polymer.Path.get(state, this[statePathPropertyName]);
          },
        };
      }

      return properties;
    }

    static statePathReducer(reducer, opt_options) {
      return (state, action) => Polymer.Path.setImmutable(
          state, action.statePath, value => reducer(value, action));
    }

    static register(subclass) {
      customElements.define(subclass.is, subclass);

      if (subclass.reducers) {
        for (const [name, reducer] of Object.entries(subclass.reducers)) {
          REDUCERS.set(`${subclass.is}.${name}`, reducer);
        }
      }
    }

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

    static async measureInputLatency(groupName, functionName, event) {
      const mark = tr.b.Timing.mark(
          groupName, functionName,
          event.timeStamp || event.detail.sourceEvent.timeStamp);
      await afterRender();
      mark.end();
    }
  }

  ElementBase.actions = {
    updateObjectAtPath: (statePath, delta) => async (dispatch, getState) => {
      dispatch({
        type: 'element-base.updateObjectAtPath',
        statePath,
        delta,
      });
    },

    toggleBooleanAtPath: statePath => async (dispatch, getState) => {
      dispatch({
        type: 'element-base.toggleBooleanAtPath',
        statePath,
      });
    },
  };

  REDUCERS.set('element-base.updateObjectAtPath', ElementBase.statePathReducer(
      (state, action) => {
        return {...state, ...action.delta};
      }));

  REDUCERS.set('element-base.toggleBooleanAtPath', ElementBase.statePathReducer(
      (state, action) => !state));

  return {
    ElementBase,
  };
});
