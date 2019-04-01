/* Copyright 2019 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  class DetailsTable extends cp.ElementBase {
    observeConfig_() {
      if (!this.revisionRanges || this.revisionRanges.length === 0) return;

      this.debounce('load', () => {
        this.dispatch('load', this.statePath);
      }, Polymer.Async.microTask);
    }
  }

  DetailsTable.State = {
    isLoading: options => false,
    lineDescriptors: options => options.lineDescriptors || [],
    minRevision: options => options.minRevision || 0,
    maxRevision: options => options.maxRevision || Number.MAX_SAFE_INTEGER,
    revisionRanges: options => options.revisionRanges || [],
    commonLinkRows: options => [],
    bodies: options => [],
  };

  DetailsTable.properties = cp.buildProperties(
      'state', DetailsTable.State);
  DetailsTable.buildState = options => cp.buildState(
      DetailsTable.State, options);
  DetailsTable.observers = [
    'observeConfig_(lineDescriptors, revisionRanges)',
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

  async function* wrapTimeseriesReader(
      batches, fetchDescriptor, revisionRanges, receiveCallback) {
    // This generator does not yield any results to BatchIterator.
    // This generator only adds more generators from wrapDetailsReader, which
    // will yield. However, those generators do not yield results. Instead,
    // results are collated via receiveCallback.
    const request = new cp.TimeseriesRequest(fetchDescriptor);
    let timeseries;
    for await (timeseries of request.reader()) {
      // Wait for final data.
    }
    console.log(fetchDescriptor, timeseries);

    for (const [rangeIndex, revisionRange] of cp.enumerate(revisionRanges)) {
      fetchDescriptor = {
        ...fetchDescriptor,
        levelOfDetail: cp.LEVEL_OF_DETAIL.DETAILS,
        ...DetailsTable.matchRange(revisionRange, timeseries),
      };
      batches.add(wrapDetailsReader(
          fetchDescriptor, rangeIndex, receiveCallback));
    }
  }

  DetailsTable.matchRange = (range, timeseries) => {
    // Return {minRevision, maxRevision} to fetch in order to get the data
    // points within revisionRange (or the previous available point if that's
    // empty) plus one data point before revisionRange as a reference.

    let maxIndex = tr.b.findLowIndexInSortedArray(
        timeseries, d => d.revision, range.max);
    // Now, timeseries[maxIndex].revision >= range.max

    if (maxIndex > 0) {
      // Get the data point *before* range.max, not after it.
      maxIndex -= 1;
    }

    let minIndex = tr.b.findLowIndexInSortedArray(
        timeseries, d => d.revision, range.min);
    // Now, timeseries[minIndex].revision >= range.min

    while (minIndex > 0 && maxIndex < minIndex) {
      // Prevent minRevision > maxRevision.
      minIndex -= 1;
    }

    // Get the reference data point.
    if (minIndex > 0) minIndex -= 1;

    const minRevision = timeseries[minIndex].revision;
    const maxRevision = timeseries[maxIndex].revision;
    return {minRevision, maxRevision};
  };

  async function* wrapDetailsReader(
      fetchDescriptor, rangeIndex, receiveCallback) {
    const request = new cp.TimeseriesRequest(fetchDescriptor);
    for await (const timeseries of request.reader()) {
      receiveCallback(rangeIndex, timeseries);
      yield {/* Pump BatchIterator. See timeseriesesByLine. */};
    }
  }

  // Each lineDescriptor may require data from one or more fetchDescriptors.
  // Fetch one or more fetchDescriptors per line, batch the readers, collate the
  // data.
  // Yields {errors, timeseriesesByLine: [
  //   {lineDescriptor, timeseriesesByRange: [{range, timeserieses}]},
  // ]}.
  async function* generateTimeseries(
      lineDescriptors, minRevision, maxRevision, revisionRanges) {
    const timeseriesesByLine = [];
    const batches = new cp.BatchIterator([]);

    for (const lineDescriptor of lineDescriptors) {
      const fetchDescriptors = cp.ChartTimeseries.createFetchDescriptors(
          lineDescriptor, cp.LEVEL_OF_DETAIL.XY);
      const timeseriesesByRange = new Array(revisionRanges.length);
      timeseriesesByLine.push({lineDescriptor, timeseriesesByRange});

      for (const [rangeIndex, range] of cp.enumerate(revisionRanges)) {
        const timeserieses = new Array(fetchDescriptors.length);
        timeseriesesByRange[rangeIndex] = {range, timeserieses};
      }

      for (const [fetchIndex, fetchDescriptor] of cp.enumerate(
          fetchDescriptors)) {
        function receive(rangeIndex, timeseries) {
          timeseriesesByRange[rangeIndex].timeserieses[fetchIndex] = timeseries;
        }

        fetchDescriptor.minRevision = minRevision;
        fetchDescriptor.maxRevision = maxRevision;
        batches.add(wrapTimeseriesReader(
            batches, fetchDescriptor, revisionRanges, receive));
      }
    }

    // Use BatchIterator only to batch result *events*, not the results
    // themselves. Manually collate results above to keep track of which line
    // and request go with each timeseries.

    for await (const {results, errors} of batches) {
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

      const generator = generateTimeseries(
          state.lineDescriptors,
          state.minRevision, state.maxRevision,
          state.revisionRanges);
      for await (const {timeseriesesByLine, errors} of generator) {
        state = Polymer.Path.get(getState(), statePath);
        if (!state || state.started !== started) return;

        dispatch({
          type: DetailsTable.reducers.receiveData.name,
          statePath,
          timeseriesesByLine,
        });
      }

      dispatch({type: DetailsTable.reducers.doneLoading.name, statePath});
    },
  };

  function setCell(map, label, columnCount, columnIndex, value) {
    if (!map.has(label)) map.set(label, new Array(columnCount));
    map.get(label)[columnIndex] = value;
  }

  function buildBody({lineDescriptor, timeseriesesByRange}) {
    const descriptorParts = [
      lineDescriptor.suites.join('\n'),
      lineDescriptor.measurement,
      lineDescriptor.bots.join('\n'),
      lineDescriptor.cases.join('\n'),
      lineDescriptor.buildType,
    ];

    const color = 'TODO';

    const scalarRowsByLabel = new Map();
    const linkRowsByLabel = new Map();
    const columnCount = timeseriesesByRange.length;
    for (const [columnIndex, {range, timeserieses}] of cp.enumerate(
        timeseriesesByRange)) {
      const merged = [];
      for (const [x, datum] of new cp.TimeseriesMerger(timeserieses)) {
        merged.push(datum);
      }

      // Now also merge all but the reference data point.
      const reference = (merged.length > 1) ? merged.shift() : {};
      const cellDatum = merged.shift();
      for (const datum of merged) {
        cp.TimeseriesMerger.mergeData(cellDatum, datum);
      }

      console.log(descriptorParts, range.min, range.max, reference, cellDatum);

      setCell(linkRowsByLabel, 'revision', columnCount, columnIndex, {
        href: 'http://crrev.com/' + range.min + '..' + range.max,
        label: range.min + '..' + range.max,
      });
    }

    const scalarRows = [...scalarRowsByLabel.keys()].sort().map(label => {
      return {label, cells: scalarRowsByLabel.get(label) || []};
    });
    const linkRows = [...linkRowsByLabel.keys()].sort().map(label => {
      return {label, cells: linkRowsByLabel.get(label) || []};
    });

    return {color, descriptorParts, scalarRows, linkRows};
  }

  DetailsTable.reducers = {
    startLoading: (state, {started}, rootState) => {
      return {
        ...state,
        isLoading: true,
        started,
        commonLinkRows: [],
        bodies: [],
      };
    },

    receiveData: (state, {timeseriesesByLine}, rootState) => {
      console.log(timeseriesesByLine);
      const bodies = timeseriesesByLine.map(buildBody);

      // Factor common linkRows out to share above the bodies.
      const commonLinkRows = [];

      return {...state, commonLinkRows, bodies};
    },

    doneLoading: (state, action, rootState) => {
      return {...state, isLoading: false};
    },
  };

  cp.ElementBase.register(DetailsTable);
  return {DetailsTable};
});
