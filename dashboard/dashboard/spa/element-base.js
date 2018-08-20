/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

tr.exportTo('cp', () => {
  const ReduxMixin = PolymerRedux(Redux.createSimpleStore());

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

    isEqual_() {
      const test = arguments[0];
      for (const arg of Array.from(arguments).slice(1)) {
        if (arg !== test) return false;
      }
      return true;
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
      return this._len(seq) > 1;
    }

    isEmpty_(seq) {
      return this._len(seq) === 0;
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
  }

  /*
   * Returns a Polymer properties descriptor object.
   *
   * Usage:
   * const FooState = {
   *   abc: options => options.abc || 0,
   *   def: {reflectToAttribute: true, value: options => options.def || [],},
   * };
   * FooElement.properties = ElementBase.buildProperties('state', FooState);
   * FooElement.buildState = options =>
   *   ElementBase.buildState(FooState, options);
   */
  ElementBase.buildProperties = (statePropertyName, configs) => {
    const statePathPropertyName = statePropertyName + 'Path';
    const properties = {
      [statePathPropertyName]: {type: String},
      [statePropertyName]: {
        readOnly: true,
        statePath(state) {
          const statePath = this[statePathPropertyName];
          if (statePath === undefined) return {};
          return Polymer.Path.get(state, statePath) || {};
        },
      },
    };
    for (const [name, config] of Object.entries(configs)) {
      if (name === statePathPropertyName || name === statePropertyName) {
        throw new Error('Invalid property name: ' + name);
      }
      properties[name] = {
        readOnly: true,
        computed: `${statePropertyName}.${name}`,
      };
      if (typeof(config) === 'object') {
        for (const [paramName, paramValue] of Object.entries(config)) {
          if (paramName === 'value') continue;
          properties[paramName] = paramValue;
        }
      }
    }
    return properties;
  };

  /*
   * Returns a new object with the same shape as `configs` but with values taken
   * from `options`.
   * See ElementBase.buildProperties for description of `configs`.
   */
  ElementBase.buildState = (configs, options) => {
    const state = {};
    for (const [name, config] of Object.entries(configs)) {
      switch (typeof(config)) {
        case 'object':
          state[name] = config.value(options);
          break;
        case 'function':
          state[name] = config(options);
          break;
        default:
          throw new Error('Invalid property config: ' + config);
      }
    }
    return state;
  };

  ElementBase.register = subclass => {
    subclass.is = Polymer.CaseMap.camelToDashCase(subclass.name).substr(1);
    customElements.define(subclass.is, subclass);
    Redux.registerReducers(subclass);
  };

  return {
    ElementBase,
  };
});
