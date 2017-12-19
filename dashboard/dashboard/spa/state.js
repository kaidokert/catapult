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

  // Action creators MUST return an object with type containing a string name of
  // a reducer.
  // Action creators SHOULD contain all async code in the app.
  // Action creators MAY have side-effects.
  // Action creators MAY take any number of parameters.

  // TODO request this onload? templatize in a request handler?
  const DEFAULT_SECTION = {
    type: 'releasing-section',
    id: -1,
    source: {
      isFocused: false,
      inputValue: 'Chromeperf Public',
      selectedOptions: ['Chromeperf Public'],
      options: [
        'Chromeperf Public',
        'Loading',
        'Input',
        'Memory',
        'Battery',
      ],
    },
    isLoading: false,
    isOwner: Math.random() < 0.5,
    milestone: 64,
    isPreviousMilestone: true,
    isNextMilestone: false,
    tables: [
      {
        title: 'health-plan-clankium-phone',
        currentVersion: '517411-73a',
        referenceVersion: '508578-c23',
        rows: [
          {
            isFirstInCategory: true,
            rowCount: 4,
            category: 'Foreground',
            href: '#',
            name: 'Java Heap',
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Native Heap',
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Ashmem',
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Overall PSS',
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: true,
            rowCount: 4,
            category: 'Background',
            href: '#',
            name: 'Java Heap',
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Native Heap',
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Ashmem',
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Overall PSS',
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
        ],
      },
      {
        title: 'health-plan-clankium-low-end-phone',
        currentVersion: '517411-73a',
        referenceVersion: '508578-c23',
        rows: [
          {
            isFirstInCategory: true,
            rowCount: 4,
            category: 'Foreground',
            href: '#',
            name: 'Java Heap',
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Native Heap',
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Ashmem',
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Overall PSS',
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: true,
            rowCount: 4,
            category: 'Background',
            href: '#',
            name: 'Java Heap',
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Native Heap',
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Ashmem',
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
          {
            isFirstInCategory: false,
            href: '#',
            name: 'Overall PSS',
            testPath: [['system_health.memory_mobile'], ['nexus5'], ['PSS']],
            currentValue: 2,
            unit: tr.b.Unit.byName.sizeInBytes_smallerIsBetter,
            referenceValue: 1,
            percentDeltaValue: 1,
            percentDeltaUnit:
              tr.b.Unit.byName.normalizedPercentageDelta_smallerIsBetter,
            deltaValue: 1,
            deltaUnit: tr.b.Unit.byName.sizeInBytesDelta_smallerIsBetter,
          },
        ],
      },
    ],
  };

  // Maps from string "action type" to synchronous
  // function(!Object state, !Object action):!Object state.
  const REDUCERS = new Map();

  const DEFAULT_STATE = {
    sectionIds: [DEFAULT_SECTION.id],
    sectionsById: {
      [DEFAULT_SECTION.id]: DEFAULT_SECTION,
    },
    containsDefaultSection: true,
    closedSectionId: undefined,
    isExplainingFab: true,
  };

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
   * This is a base class for elements in this app that mixes together
   * Polymer.Element, Polymer-Redux, and some functions to help data-bindings in
   * elements perform minimal computation without computed properties.
   */
  class Element extends ReduxMixin(Polymer.Element) {
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

    static register(subclass) {
      customElements.define(subclass.is, subclass);
      for (const [name, reducer] of Object.entries(subclass.reducers)) {
        REDUCERS.set(`${subclass.is}.${name}`, reducer);
      }
    }
  }

  /**
   * This function helps reducers create a new Array based on an existing one
   * without modifying it.
   *
   * @param {!Array} arr
   * @param {Number} index
   * @param {!Object} delta
   * @returns {!Array}
   */
  function assignInArray(arr, index, delta) {
    return arr.slice(0, index).concat([
      {...arr[index], ...delta},
    ]).concat(arr.slice(index + 1));
  }

  /**
   * This function helps Section elements define their properties with
   * statePath.
   *
   * @param {!Object} configs
   * @returns {!Object}
   */
  function sectionProperties(configs) {
    const properties = {sectionId: Number};
    for (const [name, config] of Object.entries(configs)) {
      properties[name] = {
        ...config,
        statePath(state) {
          if (!state.sectionsById[this.sectionId]) return undefined;
          return state.sectionsById[this.sectionId][name];
        },
      };
    }
    return properties;
  }

  /**
   * This function helps Section elements register reducers that only modify
   * their own state.
   * @param {!Function(section, action):sectionDelta} reducer
   * @return {Function(state, action):state}
   */
  function sectionReducer(reducer) {
    return (state, action) => {
      if (typeof action.sectionId !== 'number') {
        throw new Error(`Invalid sectionId ${action.sectionId}`);
      }
      const section = state.sectionsById[action.sectionId];
      const delta = reducer(section, action);
      const sectionsById = {...state.sectionsById};
      sectionsById[action.sectionId] = {...section, ...delta};
      return {...state, sectionsById};
    };
  }

  function afterRender() {
    return new Promise(resolve => {
      Polymer.RenderStatus.afterNextRender({}, () => {
        resolve();
      });
    });
  }

  function beforeRender() {
    return new Promise(resolve => {
      Polymer.RenderStatus.beforeNextRender({}, () => {
        resolve();
      });
    });
  }

  async function measureInputLatency(groupName, functionName, event) {
    const mark = tr.b.Timing.mark(
        groupName, functionName,
        event.timeStamp || event.detail.sourceEvent.timeStamp);
    await afterRender();
    mark.end();
  }

  return {
    Element,
    afterRender,
    assignInArray,
    beforeRender,
    measureInputLatency,
    sectionProperties,
    sectionReducer,
  };
});
