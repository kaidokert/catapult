/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

/*
This file adds a few things that Redux forgot.
Without this, you'd need to compose middleware such as thunk and devtools, put
all your reducers in a single giant function, and call Redux.createStore().
With this, you can just call Redux.createSimpleStore(). It composes thunk and
devtools by default, allows you to modularize small reducer functions, and
prepare and register whole namespaces of reducer functions at once.
*/

(() => {
  // Maps from string action type to synchronous
  // function(!Object state, !Object action):!Object state.
  const REDUCERS = new Map();

  function rootReducer(state, action) {
    if (state === undefined) state = {};
    const reducer = REDUCERS.get(action.type);
    if (reducer === undefined) return state;
    return reducer(state, action);
  }

  // This is all that is needed from redux-thunk to enable asynchronous action
  // creators.
  // https://tur-nr.github.io/polymer-redux/docs#async-actions
  const THUNK = ({dispatch, getState}) => next => action => {
    if (typeof action === 'function') {
      return action(dispatch, getState);
    }
    try {
      return next(action);
    } catch (error) {
      const state = getState();
      // eslint-disable-next-line no-console
      console.error(error, action, state);
      return state;
    }
  };

  const CREATE_STORE = Redux.createStore;
  Redux.createSimpleStore = ({
    middleware = undefined,
    defaultState = {},
    devtools = {},
    useThunk = true} = {}) => {
    if (useThunk) {
      middleware = Redux.compose(middleware, THUNK);
    }
    if (window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__) {
      middleware = window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__(
          devtools)(middleware);
    }
    return CREATE_STORE(rootReducer, defaultState, middleware);
  };

  /*
   * Redux requires `action.type` to be a string and expects your reducer
   * function to switch on it, but we often want to modularize reducers into
   * separate functions.
   *
   * Usage:
   * function foo(state, action) { return {...state, ...}; }
   * Redux.registerReducer(foo);
   * dispatch({type: foo.name, ...});
   */
  Redux.registerReducer = reducer => REDUCERS.set(reducer.name, reducer);

  /*
   * State trees can get to be quite large and complicated.
   * Web components should not need to know exactly where their state is in the
   * global state tree. They should only say where their children's states are
   * relative to their own. Their reducers should not need to understand the
   * shape of the entire state tree in order to manage their own state.
   * This helper function wraps a reducer function so that web components can
   * pass their statePath in dispatched action objects, and let the wrapped
   * reducer functions focus on the business logic.
   *
   * Usage: Redux.registerReducer(Redux.statePathReducer(
   *   function foo(state, action) { return {...state, ...changes}; }));
   * dispatch({type: 'foo', statePath: this.statePath})
   */
  Redux.statePathReducer = reducer => {
    const replacement = (rootState, action) => {
      if (!action.statePath) return reducer(rootState, action, rootState);
      try {
        return Polymer.Path.setImmutable(rootState, action.statePath, state =>
          reducer(state, action, rootState));
      } catch (error) {
        // eslint-disable-next-line no-console
        console.error(reducer.name, error, action, rootState);
        return rootState;
      }
    };
    Object.defineProperty(replacement, 'name', {value: reducer.name});
    return replacement;
  };

  Object.deepFreeze = o => {
    Object.freeze(o);
    for (const [name, value] of Object.entries(o)) {
      if (typeof(value) !== 'object') continue;
      if (Object.isFrozen(value)) continue;
      if (value.__proto__ !== Object.prototype) continue;
      Object.deepFreeze(value);
    }
  };

  /*
   * Can't figure out where a state change is coming from? It's possible that
   * your reducer accidentally modifies state instead of returning a new object.
   * Debug by wrapping your reducers using this in order to make Javascript
   * throw an exception when you try to modify state.
   * Warning! This incurs a significant performance penalty!
   */
  Redux.freezingReducer = reducer => {
    const replacement = (rootState, action) => {
      rootState = Object.deepFreeze(rootState);
      return reducer(rootState, action);
    };
    Object.defineProperty(replacement, 'name', {value: reducer.name});
    return replacement;
  };

  /*
   * This wraps reducers with tr.b.Timing.mark(), which creates performance API
   * marks and measures and reports to Google Analytics if configured.
   */
  Redux.timeReducer = (reducer, category = 'reducer') => {
    const replacement = () => {
      const mark = tr.b.Timing.mark(category, reducer.name);
      try {
        return reducer.apply(this, arguments);
      } finally {
        mark.end();
      }
    };
    Object.defineProperty(replacement, 'name', {value: reducer.name});
    return replacement;
  };

  /*
   * Complex web components often have many reducers, so you want to put them in
   * a namespace like FooElement.reducers = {bar: (state, action)=>{}};
   * You probably want to prepare and register the reducers when you register
   * the web component.
   *
   * Usage: Redux.prepareReducers(FooElement, {
   *   prefix: 'FooElement.reducers.', freeze: IS_DEBUG});
   */
  Redux.prepareReducers = (obj, {
    prefix,
    time = true, category,
    freeze = false,
    statePath = true,
    register = true} = {}) => {
    for (const [name, original] of Object.entries(obj)) {
      if (prefix) {
        Object.defineProperty(original, 'name', {value: prefix + name});
      }
      let reducer = original;
      // Time before freeze and statePath so that the timing doesn't include the
      // overhead from those wrappers, it will just measure your code.
      if (time) reducer = Redux.timeReducer(reducer, category);
      if (freeze) reducer = Redux.freezingReducer(reducer);
      if (statePath) reducer = Redux.statePathReducer(reducer);
      if (register) Redux.registerReducer(reducer);
    }
  };

  /*
   * Dispatching a reducer usually re-renders the state to DOM.
   * However, sometimes you may want to compose reducers in different ways
   * without re-rendering in between each one. This reducer can be used to chain
   * independent reducers.
   *
   * Usage: dispatch({type: 'CHAIN', actions: [
   * {type: 'foo', statePath: 'x.0'}, {type: 'bar', statePath: 'y.1'}]})
   */
  Redux.registerReducer(function CHAIN(rootState, {actions}) {
    for (const action of actions) {
      rootState = REDUCERS.get(action.type)(rootState, action);
    }
    return rootState;
  });

  /*
   * You probably have objects in your state tree, and sometimes you just want
   * to modify a property or two without registering a separate reducer just for
   * that.
   *
   * Usage:
   * dispatch({type: 'UPDATE', statePath: this.statePath, delta: {title}});
   */
  Redux.registerReducer(Redux.statePathReducer(function UPDATE(state, {delta}) {
    return {...state, ...delta};
  }));

  /*
   * You probably have booleans somewhere in your state tree, and you probably
   * want to flip them sometimes.
   *
   * Usage: dispatch({type: 'FLIP', statePath: `${this.statePath}.isEnabled`});
   */
  Redux.registerReducer(Redux.statePathReducer(function FLIP(state) {
    return !state;
  }));
})();
