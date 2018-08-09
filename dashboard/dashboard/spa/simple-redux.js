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
  /**
   * Like Polymer.Path.set(), but returns a modified clone of root instead of
   * modifying root. In order to compute a new value from the existing value at
   * path efficiently, instead of calling Path.get() and then Path.set(),
   * `value` may be a callback that takes the existing value and returns
   * a new value.
   *
   * @param {!Object|!Array} root
   * @param {string|!Array} path
   * @param {*|function} value
   * @return {!Object|!Array}
   */
  window.setImmutable = (root, path, value) => {
    if (path === '') {
      path = [];
    } else if (typeof(path) === 'string') {
      path = path.split('.');
    }
    // Based on dot-prop-immutable:
    // https://github.com/debitoor/dot-prop-immutable/blob/master/index.js
    root = Array.isArray(root) ? [...root] : {...root};
    let node = root;
    const maxDepth = path.length - 1;
    for (let depth = 0; depth < maxDepth; ++depth) {
      const key = Array.isArray(node) ? parseInt(path[depth]) : path[depth];
      const obj = node[key];
      node[key] = Array.isArray(obj) ? [...obj] : {...obj};
      node = node[key];
    }
    const key = Array.isArray(node) ? parseInt(path[maxDepth]) : path[maxDepth];
    if (typeof value === 'function') {
      node[key] = value(node[key]);
    } else {
      node[key] = value;
    }
    return root;
  };

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
  const THUNK = Redux.applyMiddleware(store => next => action => {
    if (typeof action === 'function') {
      return action(store.dispatch, store.getState);
    }
    return next(action);
  });

  Redux.createSimpleStore = ({
    middleware,
    defaultState = {},
    devtools,
    useThunk = true} = {}) => {
    if (useThunk) {
      if (middleware) {
        middleware = Redux.compose(middleware, THUNK);
      } else {
        middleware = THUNK;
      }
    }
    if (window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__) {
      middleware = window.__REDUX_DEVTOOLS_EXTENSION_COMPOSE__(
          devtools)(middleware);
    }
    return Redux.createStore(rootReducer, defaultState, middleware);
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
      return window.setImmutable(rootState, action.statePath, state =>
        reducer(state, action, rootState));
    };
    Object.defineProperty(replacement, 'name', {value: reducer.name});
    return replacement;
  };

  window.deepFreeze = o => {
    Object.freeze(o);
    for (const [name, value] of Object.entries(o)) {
      if (typeof(value) !== 'object') continue;
      if (Object.isFrozen(value)) continue;
      if (value.__proto__ !== Object.prototype) continue;
      window.deepFreeze(value);
    }
  };

  /*
   * Can't figure out where a state change is coming from? It's possible that
   * your reducer accidentally modifies state instead of returning a new object.
   * Debug by wrapping your reducers using this in order to make Javascript
   * throw an exception when you try to modify state.
   * Warning! This incurs a significant performance penalty! Only use it for
   * debugging!
   */
  Redux.freezingReducer = reducer => {
    const replacement = (rootState, action) => {
      window.deepFreeze(rootState);
      return reducer(rootState, action);
    };
    Object.defineProperty(replacement, 'name', {value: reducer.name});
    return replacement;
  };

  /*
   * This wraps reducers with tr.b.Timing.mark(), which creates performance API
   * marks and measures and reports to Google Analytics if configured.
   */
  Redux.timeReducer = (category = 'reducer') => reducer => {
    const replacement = (...args) => {
      const mark = tr.b.Timing.mark(category, reducer.name);
      try {
        return reducer.apply(this, args);
      } finally {
        mark.end();
      }
    };
    Object.defineProperty(replacement, 'name', {value: reducer.name});
    return replacement;
  };

  Redux.DEFAULT_REDUCER_WRAPPERS = [
    Redux.timeReducer('reducer'),
    Redux.statePathReducer,
  ];

  /*
   * registerReducer() uses `reducer.name`, however, reducer names might not be
   * globally unique, so you might want to prefix them with a namespace like the
   * name of a web component.
   * This curries so it can be used with registerReducers().
   * This makes reducer.name immutable.
   *
   * Usage: Redux.renameReducer('FooElement.')(FooElement.reducers.frob);
   */
  Redux.renameReducer = prefix => reducer => {
    Object.defineProperty(reducer, 'name', {value: prefix + reducer.name});
    return reducer;
  };

  function wrap(wrapped, wrapper) {
    return wrapper(wrapped);
  }

  /*
   * Complex web components often have many reducers, so you want to put them in
   * a namespace like FooElement.reducers = {bar: (state, action)=>{}};
   * You probably want to prepare and register the reducers when you register
   * the web component.
   * Make sure that timeReducer is before freezingReducer so that the timing
   * doesn't include the overhead from freezingReducer. Make sure that
   * statePathReducer is last because it changes the function signature.
   *
   * Usage:
   * if (DEBUG) {
   *   Redux.DEFAULT_REDUCER_WRAPPERS.splice(1, 0, Redux.freezingReducer);
   * }
   * Redux.registerReducers(FooElement.reducers,
   * [Redux.renameReducer('FooElement.reducers.'),
   * ...Redux.DEFAULT_REDUCER_WRAPPERS]);
   */
  Redux.registerReducers = (obj, wrappers = Redux.DEFAULT_REDUCER_WRAPPERS) => {
    for (const [name, reducer] of Object.entries(obj)) {
      Redux.registerReducer(wrappers.reduce(wrap, reducer));
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
   * want to toggle them sometimes.
   *
   * Usage:
   * dispatch({type: 'TOGGLE', statePath: `${this.statePath}.isEnabled`});
   */
  Redux.registerReducer(Redux.statePathReducer(function TOGGLE(state) {
    return !state;
  }));
})();
