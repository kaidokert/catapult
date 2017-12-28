/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

tr.exportTo('cp', () => {
  // Rules for reducers (See Redux docs):
  // Reducers MUST NOT have side effects.
  // Reducers MUST NOT modify state.
  // Reducers MUST return a new object.
  // Reducers MAY copy properties from state.

  // Rules for action creators (See Polymer Redux docs):
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
    /**
     * Subclasses should use this to bind properties to redux state.
     * @param {String} statePathPropertyName Typically 'statePath'.
     * @param {!Object} configs
     * @return {!Object} properties
     */
    static statePathProperties(statePathPropertyName, configs) {
      const properties = {};
      properties[statePathPropertyName] = {
        type: Array,
      };

      for (const [name, config] of Object.entries(configs)) {
        properties[name] = {
          ...config,
          statePath(state) {
            return ElementBase.getStateAtPath(
                state, this[statePathPropertyName] + '.' + name);
          },
        };
      }

      return properties;
    }

    static statePathReducer(reducer, opt_options) {
      return (state, action) => {
        if (!(action.statePath instanceof Array)) {
          throw new Error(`Invalid statePath in ${action} to ${reducer}`);
        }
        const branch = ElementBase.getStateAtPath(state, action.statePath);
        const value = reducer(branch, action);
        return ElementBase.setStateAtPath(
            state, action.statePath, value, opt_options);
      };
    }

    static updatingReducer(reducer) {
      return ElementBase.statePathReducer(reducer, {updateObject: true});
    }

    static register(subclass) {
      customElements.define(subclass.is, subclass);

      if (subclass.reducers) {
        for (const [name, reducer] of Object.entries(subclass.reducers)) {
          REDUCERS.set(`${subclass.is}.${name}`, reducer);
        }
      }
    }

    static getStateAtPath(state, path) {
      for (const name of path) {
        if (state === undefined) return undefined;
        state = state[name];
      }
      return state;
    }

    /**
     * @param {!Object|!Array} state
     * @param {!Array.<(string|number)>} path
     * @param {*} value
     * @param {!Object=} opt_options
     * @param {boolean} opt_options.updateObject
     */
    static setStateAtPath(state, path, value, opt_options) {
      if (!(path instanceof Array)) {
        throw new Error(`Invalid path ${path}`);
      }

      const isArray = state instanceof Array;
      const key = isArray ? parseInt(path[0]) : path[0];
      const existing = state[key];

      // First, clone state. See Rules for reducers above.
      state = isArray ? Array.from(state) : {...state};

      if (path.length !== 1) {
        // Recurse.
        value = ElementBase.setStateAtPath(
            existing, path.slice(1), value, opt_options);
      } else if (opt_options && opt_options.updateObject) {
        value = {
          ...existing,
          ...value,
        };
      }

      if (isArray) {
        state.splice(key, 1, value);
      } else {
        state[key] = value;
      }
      return state;
    }

    static updateObjectAtPath(state, path, delta) {
      return ElementBase.setStateAtPath(
          state, path, delta, {updateObject: true});
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
    setStateAtPath: (statePath, value) => async (dispatch, getState) => {
      if (!(statePath instanceof Array)) {
        throw new Error(`Invalid statePath ${statePath}`);
      }

      dispatch({
        type: 'element-base.setStateAtPath',
        statePath,
        value,
      });
    },

    updateObjectAtPath: (statePath, delta) => async (dispatch, getState) => {
      if (!(statePath instanceof Array)) {
        throw new Error(`Invalid statePath ${statePath}`);
      }

      dispatch({
        type: 'element-base.updateObjectAtPath',
        statePath,
        delta,
      });
    },
  };

  REDUCERS.set('element-base.setStateAtPath', ElementBase.statePathReducer(
      (state, action) => action.value));

  REDUCERS.set('element-base.updateObjectAtPath', ElementBase.updatingReducer(
      (state, action) => action.delta));

  return {
    ElementBase,
  };
});
