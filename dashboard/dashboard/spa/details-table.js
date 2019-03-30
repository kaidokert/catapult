/* Copyright 2019 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class DetailsTable extends cp.ElementBase {
    observeConfig_() {
      this.debounce('load', () => {
        this.dispatch('load', this.statePath);
      }, Polymer.Async.microTask);
    }
  }

  DetailsTable.State = {
    isLoading: options => false,
    lines: options => options.lines || [],
    revisionRanges: options => options.revisionRanges || [],
    columns: options => [],
    commonLinkRows: options => [],
    bodies: options => [],
  };

  DetailsTable.properties = cp.buildProperties(
      'state', DetailsTable.State);
  DetailsTable.buildState = options => cp.buildState(
      DetailsTable.State, options);
  DetailsTable.observers = [
    'observeConfig_(lines, brushRevisions)',
  ];

  // Remove empty elements.
  function filterTimeseriesesByLine(timeseriesesByLine) {
    const result = [];
    for (const {lineDescriptor, timeseriesesByRange} of timeseriesesByLine) {
      const filteredTimeseriesesByRange = [];
      for (const {range, timeserieses} of timeseriesesByRange) {
        const filteredTimeserieses = timeserieses.filter(ts => ts);
        if (filteredTimeserieses.length === 0) continue;
        filteredTimeseriesesByRange.push({
          range,
          timeserieses: filteredTimeserieses,
        });
      }
      if (filteredTimeseriesesByRange.length === 0) continue;
      result.push({
        lineDescriptor,
        timeseriesesByRange: filteredTimeseriesesByRange,
      });
    }
    return result;
  }

  // Each lineDescriptor may require data from one or more fetchDescriptors.
  // Fetch one or more fetchDescriptors per line, batch the readers, collate the
  // data.
  // Yields {timeseriesesByLine: [{lineDescriptor, timeserieses}], errors}.
  async function* generateTimeseries(
      lineDescriptors, revisionRanges, levelOfDetail) {
    const readers = [];
    const timeseriesesByLine = [];

    for (const lineDescriptor of lineDescriptors) {
      const fetchDescriptors = ChartTimeseries.createFetchDescriptors(
          lineDescriptor, levelOfDetail);
      const timeseriesesByRange = new Array(revisionRanges.length);
      timeseriesesByLine.push({lineDescriptor, timeseriesesByRange});
      for (let rangeIndex = 0; rangeIndex < revisionRanges.length;
        ++rangeIndex) {
        const range = revisionRanges[rangeIndex];
        const timeserieses = new Array(fetchDescriptors.length);
        timeseriesesByRange[rangeIndex] = {range, timeserieses};

        for (let fetchIndex = 0; fetchIndex < fetchDescriptors.length;
          ++fetchIndex) {
          readers.push((async function* () {
            const request = new cp.TimeseriesRequest({
              ...fetchDescriptors[fetchIndex],
              ...range,
            });

            for await (const timeseries of request.reader()) {
              // Replace any previous timeseries from this reader.
              // TimeseriesCacheRequest merges results progressively.
              timeserieses[fetchIndex] = timeseries;
              yield {/* Pump BatchIterator. See timeseriesesByLine. */};
            }
          })());
        }
      }
    }

    // Use BatchIterator only to batch result *events*, not the results
    // themselves. Manually collate results above to keep track of which line
    // and request go with each timeseries.

    for await (const {results, errors} of new cp.BatchIterator(readers)) {
      const filtered = filterTimeseriesesByLine(timeseriesesByLine);
      yield {timeseriesesByLine: filtered, errors};
    }
  }

  DetailsTable.actions = {
    load: statePath => async(dispatch, getState) => {
      let state = Polymer.Path.get(getState(), statePath);
      if (!state) return;

      const started = performance.now();
      dispatch({
        type: DetailsTable.reducers.startLoading.name,
        statePath,
        started,
      });

      const generator = cp.ChartTimeseries.generateTimeseries(
          state.lines.map(line => line.descriptor),
          state.revisionRanges,
          cp.LEVEL_OF_DETAIL.HISTOGRAMS);
      for await (const {timeseriesesByLine, errors} of generator) {
        state = Polymer.Path.get(getState(), statePath);
        if (!state || state.started !== started) {
          // This chart is no longer in the redux store.
          return;
        }

        dispatch({
          type: DetailsTable.reducers.receiveData.name,
          statePath,
          timeseriesesByLine,
        });
      }

      dispatch({type: DetailsTable.reducers.doneLoading.name, statePath});
    },
  };

  DetailsTable.reducers = {
    startLoading: (state, {started}, rootState) => {
      return {
        ...state,
        isLoading: true,
        started,
        columns: [],
        commonLinkRows: [],
        bodies: [],
      };
    },

    receiveData: (state, {timeseriesesByLine}, rootState) => {
      const columns = [];
      const commonLinkRows = [];
      const bodies = [];

      const cells = state.lines.map(line => state.revisionRanges.map(r => []));

      for (const [rangeIndex, revisionRange] of cp.enumerate(
          state.revisionRanges)) {
        const range = tr.b.math.Range.fromExplicitRange(
            revisionRange.minRevision, revisionRange.maxRevision);

        let actualRange = new tr.b.math.Range();
        for (const [lineIndex, line] of cp.enumerate(state.lines)) {
          if (!range.intersectsExplicitRangeInclusive(
              line.data[0].datum.revision,
              line.data[line.data.length - 1].datum.revision)) {
            break;
          }

          let startIndex = tr.b.findLowIndexInSortedArray(line.data, d =>
            d.datum.revision, range.min);

          while (startIndex > 0 && line.data[startIndex].datum.revision >=
            range.min) {
            --startIndex;
          }

          let endIndex = startIndex;
          while (endIndex < line.data.length - 1 &&
                 line.data[endIndex + 1].datum.revision < range.max) {
            ++endIndex;
          }

          cells[lineIndex][rangeIndex] = line.data.slice(
              startIndex, endIndex + 1);

          actualRange.min = line.data[startIndex - 1].datum.revision + 1;
          actualRange.max = line.data[endIndex].datum.revision;
        }

        if (actualRange.isEmpty) actualRange = range;
        columns.push(`${actualRange.min}-${actualRange.max}`);
      }

      for (const line of state.lines) {
        const descriptorParts = [
          line.descriptor.suites.join('\n'),
          line.descriptor.measurement,
          line.descriptor.bots.join('\n'),
          line.descriptor.cases.join('\n'),
          line.descriptor.buildType,
        ];
        const scalarRows = [];
        const linkRows = [];
        bodies.push({
          color: line.color,
          descriptorParts,
          scalarRows,
          linkRows,
        });
      }

      return {...state, columns, commonLinkRows, bodies};
    },

    doneLoading: (state, action, rootState) => {
      return {...state, isLoading: false};
    },
  };

  cp.ElementBase.register(DetailsTable);
  return {DetailsTable};
});
