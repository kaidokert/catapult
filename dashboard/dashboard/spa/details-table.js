/* Copyright 2019 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  // Sort hidden rows after rows with visible labels.
  const HIDE_ROW_PREFIX = String.fromCharCode('z'.charCodeAt(0) + 1).repeat(3);

  const MARKDOWN_LINK_REGEX = /^\[([^\]]+)\]\(([^\)]+)\)/;

  class DetailsTable extends cp.ElementBase {
    observeConfig_() {
      if (!this.revisionRanges || this.revisionRanges.length === 0) return;

      this.debounce('load', () => {
        this.dispatch('load', this.statePath);
      }, Polymer.Async.microTask);
    }

    showRowLabel_(label) {
      return label && !label.startsWith(HIDE_ROW_PREFIX);
    }

    hideEmpty_(isLoading, bodies) {
      return !isLoading || !this.isEmpty_(bodies);
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
        if (!state || state.started !== started) break;

        dispatch({
          type: DetailsTable.reducers.receiveData.name,
          statePath,
          timeseriesesByLine,
        });
      }

      dispatch({type: DetailsTable.reducers.doneLoading.name, statePath});
    },
  };

  // Build a table map.
  function setCell(map, key, columnCount, columnIndex, value) {
    if (!map.has(key)) map.set(key, new Array(columnCount));
    map.get(key)[columnIndex] = value;
  }

  // Merge timeserieses and format the detailed data as links and scalars.
  function buildCell(setLink, setScalar, timeserieses) {
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

    console.log(reference, cellDatum);

    for (const stat of ['avg', 'std', 'min', 'max', 'sum']) {
      if (cellDatum[stat] === undefined) continue;
      setScalar(stat, cellDatum[stat], cellDatum.unit);
    }
    if (cellDatum.count !== undefined) {
      setScalar('count', cellDatum.count, tr.b.Unit.byName.count);
    }

    for (const [rName, r2] of Object.entries(cellDatum.revisions)) {
      // Abbreviate git hashes.
      let label = (r2.length > 30) ? r2.substr(0, 7) : r2;

      let r1;
      if (reference && reference.revisions && reference.revisions[rName]) {
        r1 = reference.revisions[rName];
        label = ((r1.length > 30) ? r1.substr(0, 7) : r1) + ' - ' + label;
      }

      const {name, url} = cp.revisionUrl(rName, r1, r2);
      if (!name) continue;
      setLink(name, url, label);
    }

    for (const [key, value] of Object.entries(cellDatum.annotations || {})) {
      if (!value) continue;

      if (tr.b.isUrl(value)) {
        let label = key;
        if (label === 'a_tracing_uri') label = 'sample trace';
        setLink(HIDE_ROW_PREFIX + key, value, label);
        continue;
      }

      const match = value.match(MARKDOWN_LINK_REGEX);
      if (match && match[1] && match[2]) {
        setLink(HIDE_ROW_PREFIX + key, match[2], match[1]);
        continue;
      }
    }

    setLink('Upload timestamp', '', tr.b.formatDate(cellDatum.timestamp));
  }

  // Build an array of strings to display the parts of lineDescriptor that are
  // not common to all of this details-table's lineDescriptors.
  function getDescriptorParts(lineDescriptor, descriptorFlags) {
    const descriptorParts = [];
    if (descriptorFlags.suite) {
      descriptorParts.push(lineDescriptor.suites.join('\n'));
    }
    if (descriptorFlags.measurement) {
      descriptorParts.push(lineDescriptor.measurement);
    }
    if (descriptorFlags.bot) {
      descriptorParts.push(lineDescriptor.bots.join('\n'));
    }
    if (descriptorFlags.cases) {
      descriptorParts.push(lineDescriptor.cases.join('\n'));
    }
    if (descriptorFlags.buildType) {
      descriptorParts.push(lineDescriptor.buildType);
    }
    return descriptorParts;
  }

  // Convert Map<label, cells> to [{label, cells}].
  function collectRowsByLabel(rowsByLabel) {
    return [...rowsByLabel.keys()].sort().map(label => {
      return {label, cells: rowsByLabel.get(label) || []};
    });
  }

  // Build a table body {descriptorParts, scalarRows, linkRows} to display the
  // detailed data in timeseriesesByRange.
  function buildBody({lineDescriptor, timeseriesesByRange}, descriptorFlags) {
    const descriptorParts = getDescriptorParts(lineDescriptor, descriptorFlags);
    const color = 'TODO';

    const scalarRowsByLabel = new Map();
    const linkRowsByLabel = new Map();
    const columnCount = timeseriesesByRange.length;
    for (const [columnIndex, {range, timeserieses}] of cp.enumerate(
        timeseriesesByRange)) {
      console.log(descriptorParts, range.min, range.max);
      const setLink = (rowLabel, href, linkLabel) => setCell(
          linkRowsByLabel, rowLabel, columnCount, columnIndex, {
            href,
            label: linkLabel,
          });
      const setScalar = (rowLabel, value, unit) => setCell(
        scalarRowsByLabel, rowLabel, columnCount, columnIndex, {value, unit});
      buildCell(setLink, setScalar, timeserieses);
    }
    const scalarRows = collectRowsByLabel(scalarRowsByLabel);
    const linkRows = collectRowsByLabel(linkRowsByLabel);
    return {color, descriptorParts, scalarRows, linkRows};
  }

  DetailsTable.descriptorFlags = lineDescriptors => {
    // Return an object containing flags indicating whether to show parts of
    // lineDescriptors in descriptorParts.
    let suite = false;
    let measurement = false;
    let bot = false;
    let cases = false;
    let buildType = false;
    const firstSuites = lineDescriptors[0].suites.join('\n');
    const firstBots = lineDescriptors[0].bots.join('\n');
    const firstCases = lineDescriptors[0].cases.join('\n');
    for (const other of lineDescriptors.slice(1)) {
      if (!suite && other.suites.join('\n') !== firstSuites) {
        suite = true;
      }
      if (!measurement &&
          other.measurement !== lineDescriptors[0].measurement) {
        measurement = true;
      }
      if (!bot && other.bots.join('\n') !== firstBots) {
        bot = true;
      }
      if (!cases && other.cases.join('\n') !== firstCases) {
        cases = true;
      }
      if (!buildType && other.buildType !== lineDescriptors[0].buildType) {
        buildType = true;
      }
    }
    return {suite, measurement, bot, cases, buildType};
  };

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
      const descriptorFlags = DetailsTable.descriptorFlags(
          state.lineDescriptors);
      const bodies = timeseriesesByLine.map(body =>
        buildBody(body, descriptorFlags));
      const commonLinkRows = DetailsTable.extractCommonLinkRows(bodies);
      return {...state, commonLinkRows, bodies};
    },

    doneLoading: (state, action, rootState) => {
      return {...state, isLoading: false};
    },
  };

  DetailsTable.extractCommonLinkRows = bodies => {
    // Factor common linkRows out to share above the bodies.
    const commonLinkRows = [];
    if (bodies.length <= 1) return commonLinkRows;

    for (const linkRow of bodies[0].linkRows) {
      let isCommon = true;
      for (const body of bodies.slice(1)) {
        let isFound = false;
        for (const otherLinkRow of body.linkRows) {
          if (otherLinkRow.label !== linkRow.label) continue;

          isFound = true;
          for (const [index, cell] of cp.enumerate(linkRow.cells)) {
            if (cell.href !== otherLinkRow.cells[index].href ||
                cell.label !== otherLinkRow.cells[index].label) {
              isCommon = false;
              break;
            }
          }
          if (!isCommon) break;
        }
        if (!isFound) isCommon = false;
        if (!isCommon) break;
      }

      if (isFound && isCommon) {
        commonLinkRows.push(linkRow);
        for (const body of bodies) {
          body.linkRows = body.linkRows.filter(test =>
            test.label !== linkRow.label);
        }
      }
    }
    return commonLinkRows;
  }

  cp.ElementBase.register(DetailsTable);
  return {DetailsTable};
});
