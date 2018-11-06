/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class TimeseriesDescriptor extends cp.ElementBase {
    ready() {
      super.ready();
      this.dispatch('ready', this.statePath);
    }

    dispatchMatrixChange_() {
      this.dispatchEvent(new CustomEvent('matrix-change', {
        bubbles: true,
        composed: true,
        detail: TimeseriesDescriptor.getParameterMatrix(
            this.suite, this.measurement, this.bot, this.case),
      }));
    }

    async onSuiteSelect_(event) {
      await this.dispatch('describeSuites', this.statePath);
      this.dispatchMatrixChange_();
    }

    async onMeasurementSelect_(event) {
      this.dispatchMatrixChange_();
    }

    async onBotSelect_(event) {
      this.dispatchMatrixChange_();
    }

    async onCaseSelect_(event) {
      this.dispatchMatrixChange_();
    }

    async onSuiteAggregateChange_(event) {
      this.dispatch(Redux.TOGGLE(`${this.statePath}.suite.isAggregated`));
      this.dispatchMatrixChange_();
    }

    async onBotAggregateChange_(event) {
      this.dispatch(Redux.TOGGLE(`${this.statePath}.bot.isAggregated`));
      this.dispatchMatrixChange_();
    }

    async onCaseAggregateChange_(event) {
      this.dispatch(Redux.TOGGLE(`${this.statePath}.case.isAggregated`));
      this.dispatchMatrixChange_();
    }
  }

  TimeseriesDescriptor.State = {
    suite: options => {
      return {
        isAggregated: options.suite.isAggregated !== false,
        ...cp.MenuInput.buildState(options.suite),
      };
    },
    measurement: options => {
      return {
        ...cp.MenuInput.buildState(options.measurement),
      };
    },
    bot: options => {
      return {
        isAggregated: options.bot.isAggregated !== false,
        ...cp.MenuInput.buildState(options.bot),
      };
    },
    case: options => {
      return {
        isAggregated: options.case.isAggregated !== false,
        ...cp.MenuInput.buildState(options.case),
        ...cp.TagFilter.buildState(options.case.tags),
      };
    },
  };

  TimeseriesDescriptor.buildState = options => cp.buildState(
      TimeseriesDescriptor.State, options);

  TimeseriesDescriptor.properties = {
    ...cp.buildProperties('state', TimeseriesDescriptor.State),
  };

  TimeseriesDescriptor.actions = {
    ready: statePath => async(dispatch, getState) => {
      const request = new cp.TestSuitesRequest({});
      const suites = await request.response;
      dispatch({
        type: TimeseriesDescriptor.reducers.receiveTestSuites.name,
        statePath,
        suites,
      });
    },

    describeSuites: statePath => async(dispatch, getState) => {
      const mergedDescriptor = {
        measurements: new Set(),
        bots: new Set(),
        cases: new Set(),
        caseTags: new Map(),
      };
      let state = Polymer.Path.get(getState(), statePath);
      if (state.suite.selectedOptions.length === 0) {
        dispatch({
          type: ChartSection.reducers.receiveDescriptor.name,
          statePath,
          descriptor: mergedDescriptor,
        });
        dispatch({
          type: ChartSection.reducers.finalizeParameters.name,
          statePath,
        });
        return;
      }

      // Test suite descriptors might already be in local memory, or it might
      // take the backend up to a minute to compute them, or it might take a
      // couple of seconds to serve them from memcache, so fetch them in
      // parallel.
      const suites = new Set(state.suite.selectedOptions);
      const descriptors = state.suite.selectedOptions.map(suite =>
        new cp.DescribeRequest({suite}).response);
      for await (const {results, errors} of new cp.BatchIterator(descriptors)) {
        state = Polymer.Path.get(getState(), statePath);
        if (!state.suite || !tr.b.setsEqual(
            suites, new Set(state.suite.selectedOptions))) {
          // The user changed the set of selected suites, so stop handling
          // the old set of suites. The new set of suites will be
          // handled by a new dispatch of this action creator.
          return;
        }
        // TODO display errors
        for (const descriptor of results) {
          if (!descriptor) continue;
          cp.DescribeRequest.mergeDescriptor(mergedDescriptor, descriptor);
        }
        dispatch({
          type: ChartSection.reducers.receiveDescriptor.name,
          statePath,
          descriptor: mergedDescriptor,
        });
      }
      dispatch({
        type: ChartSection.reducers.finalizeParameters.name,
        statePath,
      });

      state = Polymer.Path.get(getState(), statePath);

      if (state.measurement.selectedOptions.length === 0) {
        cp.MenuInput.actions.focus(`${statePath}.measurement`)(
            dispatch, getState);
      }
    },
  };

  TimeseriesDescriptor.reducers = {
    receiveTestSuites: (state, {suites}, rootState) => {
      const suite = TimeseriesDescriptor.State.suite({suite: {
        isAggregated: state.suite.isAggregated,
        options: suites,
      }});
      return {state, suite};
    },

    receiveDescriptor: (state, {descriptor}, rootState) => {
      state = {...state};

      state.measurement = {
        ...state.measurement,
        optionValues: descriptor.measurements,
        options: cp.OptionGroup.groupValues(descriptor.measurements),
        label: `Measurements (${descriptor.measurements.size})`,
      };

      const botOptions = cp.OptionGroup.groupValues(descriptor.bots);
      state.bot = {
        ...state.bot,
        optionValues: descriptor.bots,
        options: botOptions.map(option => {
          return {...option, isExpanded: true};
        }),
        label: `Bots (${descriptor.bots.size})`,
      };

      const caseOptions = [];
      if (descriptor.cases.size) {
        caseOptions.push({
          label: `All test cases`,
          isExpanded: true,
          options: cp.OptionGroup.groupValues(descriptor.cases),
        });
      }

      state.case = cp.ChartParameter.reducers.tagFilter({
        ...state.case,
        optionValues: descriptor.cases,
        options: caseOptions,
        label: `Test cases (${descriptor.cases.size})`,
        tags: {
          ...state.case.tags,
          map: descriptor.caseTags,
          optionValues: new Set(descriptor.caseTags.keys()),
          options: cp.OptionGroup.groupValues(descriptor.caseTags.keys()),
        },
      });

      return state;
    },

    finalizeParameters: (state, action, rootState) => {
      state = {...state};
      state.measurement = {...state.measurement};
      if (state.measurement.optionValues.size === 1) {
        state.measurement.selectedOptions = [...state.measurement.optionValues];
      } else {
        state.measurement.selectedOptions =
          state.measurement.selectedOptions.filter(
              m => state.measurement.optionValues.has(m));
      }

      state.bot = {...state.bot};
      if ((state.bot.optionValues.size === 1) ||
          ((state.bot.selectedOptions.length === 1) &&
           (state.bot.selectedOptions[0] === '*'))) {
        state.bot.selectedOptions = [...state.bot.optionValues];
      } else {
        state.bot.selectedOptions = state.bot.selectedOptions.filter(b =>
          state.bot.optionValues.has(b));
      }

      state.case = {
        ...state.case,
        selectedOptions: state.case.selectedOptions.filter(t =>
          state.case.optionValues.has(t)),
      };

      return state;
    },
  };

  TimeseriesDescriptor.getParameterMatrix = state => {
    // Aggregated parameters look like [[a, b, c]].
    // Unaggregated parameters look like [[a], [b], [c]].
    let suiteses = state.suite.selectedOptions;
    if (state.suite.isAggregated) {
      suiteses = [suiteses];
    } else {
      suiteses = suiteses.map(suite => [suite]);
    }

    let botses = state.bot.selectedOptions;
    if (state.bot.isAggregated) {
      botses = [botses];
    } else {
      botses = botses.map(bot => [bot]);
    }

    let caseses = state.case.selectedOptions.filter(x => x);
    if (state.case.isAggregated) {
      caseses = [caseses];
    } else {
      caseses = caseses.map(c => [c]);
    }
    if (caseses.length === 0) caseses.push([]);

    const measurements = state.measurement.selectedOptions;
    return {suiteses, measurements, botses, caseses};
  };

  cp.ElementBase.register(TimeseriesDescriptor);
  return {TimeseriesDescriptor};
});
