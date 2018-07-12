/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';
tr.exportTo('cp', () => {
  /*
   * Main entry point: actions.load(fetchDescriptor, refStatePath) returns
   * {unit: tr.b.Unit, data: [(tr.v.Histogram|cp.FastHistogram)]}
   *
   * A lineDescriptor describes a single line in the chart-base.
   * A lineDescriptor must specify
   *  * at least one testSuite
   *  * at least one bot
   *  * exactly one measurement
   *  * exactly one statistic
   *  * zero or more testCases
   *  * buildType (enum 'test' or 'reference')
   * When multiple testSuites, bots, or testCases are specified, the timeseries
   * are merged using RunningStatistics.merge().
   *
   * In order to load the data for a lineDescriptor, one or more
   * fetchDescriptors are generated for /api/timeseries2. See
   * Timeseries2Handler.
   * A fetchDescriptor contains a single testPath, columns, and optionally
   * minRev, maxRev, minTimestampMs, and maxTimestampMs.
   * Requests return timeseries, which are transformed into FastHistograms and
   * stored on the root state in the following cache structure:
   *
   * {
   *   ...rootState,
   *   timeseries: {
   *     $cacheKey: {
   *       references: [$statePath],
   *       unit: tr.b.Unit,
   *       data: [(FastHistogram|Histogram)],
   *       ranges: {
   *         xy: [tr.b.math.Range],
   *         annotations: [tr.b.math.Range],
   *         histogram: [tr.b.math.Range],
   *       },
   *       requests: {
   *         xy: [
   *           {minRev, maxRev, minTimestampMs, maxTimestampMs, request},
   *         ],
   *         annotations: [...],
   *         histogram: [...],
   *       },
   *     },
   *   },
   * }
   *
   * While a Request is in-flight, it's in the corresponding range in |ranges|.
   * When a Request completes, it's |request| is undefined, but the range
   * remains in Ranges to indicate that its data is stored in
   * timeseries[testPath].data.
   *
   * Requests are cached separately by service-worker.js, so timeseries data
   * can only contain the data that is currently in use by chart-timeseries
   * and pivot-cell elements, as recorded by timeseries[testPath].references,
   * which is a list of statePaths pointing to chart-timeseries and pivot-cell
   * elements' states.
   *
   * The output of this big machine is chart-base.lines[].data.
   */

  const PRIORITY = {
    // Requests with priority=PREFETCH are not directly blocking the user, so
    // they can wait until either
    // 0. a user gesture increases their priority (e.g. opening a sparkline
    //    tab), or
    // 1. the priority queue is empty, or
    // 2. they are canceled.
    PREFETCH: 1,

    // Additional priorities may be added to support, for example, guessing
    // which PREFETCH requests are more or less likely to become USER requests,
    // or prioritizing requests for earlier sections over requests for sections
    // that are lower on the page.  Priority numbers won't be serialized
    // anywhere, so they can be changed when those features are added, so
    // there's no need to leave room between constants.

    // Requests with priority=USER are directly blocking the user, so always
    // pass them directly to the network.
    USER: 2,
  };

  const LEVEL_OF_DETAIL = {
    // Minimaps only need the (x, y) coordinates to draw the line.
    // FastHistograms contain only r_commit_pos and the needed statistic.
    // Fetches /api/timeseries2/testpath&columns=r_commit_pos,value
    XY: 'xy',

    // chart-pair.chartLayout can draw its lines using XY FastHistograms
    // while asynchronously fetching annotations (e.g.  alerts)
    // for a given revision range for tooltips and icons.
    // If an extant request overlaps a new request, then the new request can
    // fetch the difference and await the extant request.
    // Fetches /api/timeseries2/testpath&min_rev&max_rev&columns=revision,alert
    ANNOTATIONS: 'annotations',

    // pivot-table in chart-section and pivot-section need the full real
    // Histogram with all its statistics and diagnostics and samples.
    // chart-section will also request the full Histogram for the last point in
    // each timeseries in order to get its RelatedNameMaps.
    // Real Histograms contain full RunningStatistics, all diagnostics, all
    // samples. Request single Histograms at a time, even if the user brushes a
    // large range.
    // Fetches /api/histogram/testpath?rev
    HISTOGRAM: 'histogram',
  };

  // Supports XY and ANNOTATIONS levels of detail.
  // [Re]implements only the Histogram functionality needed for those levels.
  // Can be merged with real Histograms.
  class FastHistogram {
    constructor() {
      this.diagnostics = new tr.v.d.DiagnosticMap();
      // TODO use tr.b.math.RunningStatistic
      this.running = {count: 0, avg: 0, std: 0};
    }

    addHistogram(other) {
      this.diagnostics.addDiagnostics(other.diagnostics);
      const deltaMean = this.running.avg - other.running.avg;
      this.running.avg = ((this.running.avg * this.running.count) +
                          (other.running.avg * other.running.count)) /
                         (this.running.count + other.running.count);
      const thisVar = this.running.std * this.running.std;
      const otherVar = other.running.std * other.running.std;
      const thisCount = this.running.count;
      this.running.count += other.running.count;
      this.running.std = Math.sqrt(thisVar + otherVar + (
        thisCount * other.running.count * deltaMean * deltaMean /
        this.running.count));
    }
  }

  FastHistogram.fromRow = (dict, fetchDescriptor, conversionFactor) => {
    const hist = new FastHistogram();
    let commitPos = dict.r_commit_pos;
    if (commitPos === null || commitPos === undefined) {
      commitPos = dict.revision;
    }
    if (commitPos !== null && commitPos !== undefined) {
      hist.diagnostics.set(
          tr.v.d.RESERVED_NAMES.CHROMIUM_COMMIT_POSITIONS,
          new tr.v.d.GenericSet([parseInt(commitPos)]));
    }

    if (dict.timestamp) {
      hist.diagnostics.set(
          tr.v.d.RESERVED_NAMES.UPLOAD_TIMESTAMP,
          new tr.v.d.DateRange(new Date(dict.timestamp) - 0));
    }
    if (dict.value !== undefined) {
      hist.running[fetchDescriptor.statistic] = dict.value * conversionFactor;
    }
    if (dict.d_avg !== undefined) {
      hist.running.avg = dict.d_avg * conversionFactor;
    }
    if (dict.error !== undefined) {
      hist.running.std = dict.error * conversionFactor;
    }
    hist.running.count = 1;
    return hist;
  };

  class TimeseriesRequest extends cp.RequestBase {
    /*
     * type options = {
     *   testSuite: any,
     *   measurement: any,
     *   bot: any,
     *   testCase: any,
     *   statistic: any,
     *   buildType: any,
     *
     *   // Commit revision range
     *   minRevision?: any,
     *   maxRevision?: any,
     *
     *   // Timestamp range
     *   minTimestamp?: any,
     *   maxTimestamp?: any,
     * }
     */
    constructor(options) {
      super(options);
      this.measurement_ = options.measurement;
      this.queryParams_ = new URLSearchParams();
      this.queryParams_.set('testSuite', options.testSuite);
      this.queryParams_.set('measurement', options.measurement);
      this.queryParams_.set('bot', options.bot);

      if (options.testCase) {
        this.queryParams_.set('testCase', options.testCase);
      }

      this.queryParams_.set('statistic', options.statistic);

      if (options.buildType) {
        this.queryParams_.set('buildType', options.buildType);
      }

      this.queryParams_.set('columns', options.columns.join(','));

      if (options.minRevision) {
        this.queryParams_.set('minRevision', options.minRevision);
      }
      if (options.maxRevision) {
        this.queryParams_.set('maxRevision', options.maxRevision);
      }
      if (options.minTimestamp) {
        this.queryParams_.set('minTimestamp', options.minTimestamp);
      }
      if (options.maxTimestamp) {
        this.queryParams_.set('maxTimestamp', options.maxTimestamp);
      }
    }

    get url_() {
      return `/api/timeseries2?${this.queryParams_}`;
    }

    async localhostResponse_() {
      let units = 'unitlessNumber';
      if (this.measurement_.startsWith('memory:')) {
        units = 'sizeInBytes_smallerIsBetter';
      }
      if (this.measurement_.startsWith('cpu:') ||
          this.measurement_.startsWith('loading') ||
          this.measurement_.startsWith('startup')) {
        units = 'ms_smallerIsBetter';
      }
      if (this.measurement_.startsWith('power')) {
        units = 'W_smallerIsBetter';
      }
      const timeseries = [];
      const sequenceLength = 100;
      const nowMs = new Date() - 0;
      for (let i = 0; i < sequenceLength; i += 1) {
        // revision, r_commit_pos, timestamp, value
        timeseries.push([
          i * 100,
          i,
          nowMs - ((sequenceLength - i - 1) * (2592105834 / 50)),
          parseInt(100 * Math.random()),
        ]);
      }
      return {timeseries, units};
    }
  }

  function columnsByLevelOfDetail(level) {
    switch (level) {
      case LEVEL_OF_DETAIL.XY:
        // TODO(Sam): Remove r_commit_pos everywhere

        // Question(Sam): Specifying columns to the API doesn't seem to work.
        // It always returns revision, r_commit_pos, timestamp, and value.
        // return ['revision', 'value'];
        return ['revision', 'r_commit_pos', 'timestamp', 'value'];
      case LEVEL_OF_DETAIL.ANNOTATIONS:
        return ['revision', 'alert', 'diagnostics', 'revisions'];
      default:
        throw new Error(`${level} is not a valid Level Of Detail`);
    }
  }

  // TODO(Sam): Create a base class for iterative retrieval of cached data.
  // Most of the functionality defined in CacheBase is either being overridden
  // or not used.
  class TimeseriesCache extends cp.CacheBase {
    constructor(options, dispatch, getState) {
      super(options, dispatch, getState);
      this.fetchDescriptor_ = this.options_.fetchDescriptor;
      this.refStatePath_ = this.options_.refStatePath;

      const {
        minRevision,
        maxRevision,
      } = Polymer.Path.get(getState(), this.refStatePath_);

      this.minRevision_ = minRevision;
      this.maxRevision_ = maxRevision;

      // TODO(Sam): Change columns based on the level of detail
      this.columns_ = columnsByLevelOfDetail(LEVEL_OF_DETAIL.XY);

      // TODO(Sam): Allow for level of detail to be specified through options
      this.levelOfDetail_ = LEVEL_OF_DETAIL.XY;
    }

    get cacheStatePath_() {
      return 'timeseries';
    }

    computeCacheKey_() {
      const cacheKey = [
        this.fetchDescriptor_.testSuite,
        this.fetchDescriptor_.measurement,
        this.fetchDescriptor_.bot,
        this.fetchDescriptor_.testCase,
        this.fetchDescriptor_.buildType,
      ].join('/').replace(/\./g, '_');

      // Open a connection to an IndexedDB database of this timeseries request.
      // If it does not exist, create it.
      this.dbPromise = idb.open(cacheKey, 1, upgradeDB => {
        if (upgradeDB.oldVersion === 0) {
          upgradeDB.createObjectStore('dataPoints');
          upgradeDB.createObjectStore('metadata');
          upgradeDB.createObjectStore('ranges');
        }
      });

      return cacheKey;
    }

    get isInCache_() {
      const entry = this.rootState_.timeseries[this.cacheKey_];

      if (!entry) {
        // The requested timeseries data has not been retrieved yet.
        return false;
      }

      const ranges = entry.ranges[this.levelOfDetail_];

      if (!Array.isArray(ranges)) {
        // This
        console.warn('Undefined ranges', entry, this.levelOfDetail_);
        return false;
      }

      const requestedRange = tr.b.math.Range.fromExplicitRange(
          this.minRevision_, this.maxRevision_);

      const rangeIndex = ranges.findIndex(range =>
        range.containsRangeInclusive(requestedRange)
      );

      if (rangeIndex === -1) {
        // The requested range of data cannot be found in a contiguous chunk.
        return false;
      }

      return true;
    }

    async readFromCache_() {
      let entry = this.rootState_.timeseries[this.cacheKey_];
      // TODO levelOfDetail, revision/timestamp ranges
      await Promise.all(entry.requests[LEVEL_OF_DETAIL.XY].map(
          rangeRequest => rangeRequest.completion
      ));
      this.rootState_ = this.getState_();
      entry = this.rootState_.timeseries[this.cacheKey_];
      return {
        unit: entry.unit,
        data: entry.data
      };
    }

    createRequest_() {
      /*
       * type options = {
       *   testSuite: any,
       *   measurement: any,
       *   bot: any,
       *   testCase: any,
       *   statistic: any,
       *   buildType: any,
       *
       *   // Commit revision range
       *   minRevision?: any,
       *   maxRevision?: any,
       *
       *   // Timestamp range
       *   minTimestamp?: any,
       *   maxTimestamp?: any,
       * }
       */
      return new TimeseriesRequest({
        testSuite: this.fetchDescriptor_.testSuite,
        measurement: this.fetchDescriptor_.measurement,
        bot: this.fetchDescriptor_.bot,
        testCase: this.fetchDescriptor_.testCase,
        statistic: this.fetchDescriptor_.statistic,
        buildType: this.fetchDescriptor_.buildType,

        columns: this.columns_,

        minRevision: this.minRevision_,
        maxRevision: this.maxRevision_,
      });
    }

    onStartRequest_(request, completion) {
      this.dispatch_({
        type: TimeseriesCache.reducers.request.typeName,
        fetchDescriptor: this.fetchDescriptor_,
        cacheKey: this.cacheKey_,
        refStatePath: this.refStatePath_,
        request,
        completion,
      });
      this.rootState_ = this.getState_();
    }

    onFinishRequest_(result) {
      const timeseries = result.timeseries || [];

      // Find min and max revision
      let minRevision = this.minRevision_;
      if (timeseries.length && !minRevision) {
        const first = timeseries[0] || {};
        minRevision = first.revision || parseInt(first.r_commit_pos);
      }

      let maxRevision = this.maxRevision_;
      if (timeseries.length && !maxRevision) {
        const last = timeseries[timeseries.length - 1] || {};
        maxRevision = last.revision || parseInt(last.r_commit_pos);
      }

      // Tell the Redux store the response is ready
      this.dispatch_({
        type: TimeseriesCache.reducers.receive.typeName,
        fetchDescriptor: this.fetchDescriptor_,
        cacheKey: this.cacheKey_,
        columns: this.columns_,
        timeseries,
        units: result.units,
        minRevision,
        maxRevision,
      });
      this.rootState_ = this.getState_();
    }

    // Read any existing data from IndexedDB.
    async readFromIDB_() {
      const openMark = tr.b.Timing.mark('IndexedDB', 'read#openDatabase');
      const db = await this.dbPromise;
      openMark.end();

      const transaction = db.transaction(
          ['ranges', 'dataPoints', 'metadata'],
          'readonly'
      );

      const rangeStore = transaction.objectStore('ranges');
      const dataStore = transaction.objectStore('dataPoints');
      const metadataStore = transaction.objectStore('metadata');

      //
      // Ranges
      //
      const rangeMark = tr.b.Timing.mark('IndexedDB', 'read#ranges');
      const cachedRanges = await rangeStore.get(this.levelOfDetail_);
      rangeMark.end();

      if (!cachedRanges) {
        // Nothing has been cached for this level-of-detail yet.
        return;
      }

      const requestedRange = tr.b.math.Range.fromExplicitRange(
          this.minRevision_, this.maxRevision_);

      // Determine if any cached data ranges intersect with the requested range.
      const rangeIndex = cachedRanges
          .map(range => tr.b.math.Range.fromDict(range))
          .findIndex(range => {
            const intersection = range.findIntersection(requestedRange);
            return !intersection.isEmpty;
          });

      if (rangeIndex === -1) {
        // IndexedDB does not contain any relevant data for the requested range.
        return;
      }

      //
      // Metadata
      // Take out all metadata for this line.
      //
      const metadataMark = tr.b.Timing.mark('IndexedDB', 'read#metadata');
      const columns = await metadataStore.get('columns');
      const units = await metadataStore.get('units');
      metadataMark.end();

      if (!columns || !units) {
        // Timeseries does not exist in cache.
        return;
      }

      // Check that the cached version contains all the columns we need for
      // the requested level-of-detail (LOD).
      for (const column of this.columns_) {
        if (!columns.includes(column)) {
          // We need to fetch more data from the network. The cache is no
          // help in this scenario.
          return;
        }
      }

      //
      // Datapoints
      // All is good, so let's retrieve the data we have!
      //
      const dataMark = tr.b.Timing.mark('IndexedDB', 'read#datapoints');
      let dataPoints = [];
      let minRevision = this.minRevision_;
      let maxRevision = this.maxRevision_;

      if (minRevision && maxRevision) {
        const range = IDBKeyRange.bound(minRevision, maxRevision);
        dataStore.iterateCursor(range, cursor => {
          if (!cursor) return;
          dataPoints.push(cursor.value);
          cursor.continue();
        });
        await transaction.complete;
      } else {
        dataPoints = await dataStore.getAll() || [];

        const first = dataPoints[0] || {};
        const last = dataPoints[dataPoints.length - 1] || {};

        minRevision = first.revision || parseInt(first.r_commit_pos);
        maxRevision = last.revision || parseInt(last.r_commit_pos);
      }
      dataMark.end();

      // Denormalize requested columns to an array with the same order as
      // requested.
      const denormalizeMark = tr.b.Timing.mark('IndexedDB', 'read#denormalize');
      const timeseries = [];
      for (const dataPoint of dataPoints) {
        const result = [];
        for (const column of this.columns_) {
          result.push(dataPoint[column]);
        }
        timeseries.push(result);
      }
      denormalizeMark.end();

      return { timeseries, units, minRevision, maxRevision };
    }

    async writeToIDB_({ timeseries, ...metadata }) {
      // Check for error in response
      if (metadata.error) {
        return;
      }

      // Store the result in IndexedDB
      const db = await this.dbPromise;

      // Store information about the timeseries
      const transaction = db.transaction(
          ['dataPoints', 'metadata', 'ranges'],
          'readwrite'
      );

      const dataStore = transaction.objectStore('dataPoints');
      const metadataStore = transaction.objectStore('metadata');
      const rangeStore = transaction.objectStore('ranges');

      // Map each unnamed column to its cooresponding name in the QueryParams.
      // Results in an object with key/value pairs representing column/value
      // pairs. Each datapoint will have a structure similar to the following:
      //   {
      //     revision: 12345,
      //     r_commit_pos: "12345",
      //     value: 42
      //   }
      const namedDatapoints = (timeseries || []).map(datapoint =>
        this.columns_.reduce(
            (prev, name, index) =>
              Object.assign(prev, { [name]: datapoint[index] }),
            {}
        )
      );

      // Store timeseries as objects indexed by r_commit_pos (preferred) or
      // revision.
      for (const datapoint of namedDatapoints) {
        const key = datapoint.revision || parseInt(datapoint.r_commit_pos);

        // Merge with existing data
        // Note(Sam): IndexedDB should be fast enough to "get" for every key.
        // A notable experiment might be to "getAll" and find by key. We can
        // then compare performance between "get" and "getAll".
        const prev = await dataStore.get(key);
        const next = Object.assign({}, prev, datapoint);

        dataStore.put(next, key);
      }

      // Update the range of data we contain in the "ranges" object store.
      if (namedDatapoints.length === 0) {
        throw new Error('No timeseries data to write');
      }

      const first = namedDatapoints[0] || {};
      const last = namedDatapoints[namedDatapoints.length - 1] || {};

      const min = this.minRevision_ ||
        first.revision ||
        parseInt(first.r_commit_pos) ||
        undefined;

      const max = this.maxRevision_ ||
        last.revision ||
        parseInt(last.r_commit_pos) ||
        undefined;

      if (min || max) {
        const currRange = tr.b.math.Range.fromExplicitRange(min, max);
        const prevRangesRaw = await rangeStore.get(this.levelOfDetail_) || [];
        const prevRanges = prevRangesRaw.map(range =>
          tr.b.math.Range.fromDict({ ...range, isEmpty: false })
        );

        const nextRanges = currRange
            .mergeIntoArray(prevRanges)
            .map(range => range.toJSON());

        rangeStore.put(nextRanges, this.levelOfDetail_);
      } else {
        // Timeseries is empty
        new Error('Min/max cannot be found; unable to update ranges');
      }

      // Store metadata separately in the "metadata" object store.
      for (const key of Object.keys(metadata)) {
        metadataStore.put(metadata[key], key);
      }

      // Store the columns available for data points in the "metadata" object
      // store. This is helpful to keep track of LOD.
      // TODO(sbalana): Test when LOD is implemented
      // TODO(sbalana): Push for the spread operator. Greatly needed here.
      const prevColumns = await metadataStore.get('columns') || [];
      const nextColumns = [...new Set([
        ...prevColumns,
        ...this.columns_,
      ])];

      metadataStore.put(nextColumns, 'columns');

      // Finish the transaction
      await transaction.complete;
    }

    async* reader() {
      this.ensureCacheState_();
      this.cacheKey_ = this.computeCacheKey_();

      // Check if we already have all the data in Redux
      if (this.isInCache_) {
        yield this.readFromCache_();
        return;
      }

      const request = this.createRequest_();

      // Start a race between IndexedDB and the network. The winner gets to
      // yield their result first. The loser will yield their result second.

      const cache = (async() => {
        const response = await this.readFromIDB_();
        if (response) {
          this.onFinishRequest_(response);
        }
        return {
          name: 'IndexedDB',
          result: response ? await this.readFromCache_() : null,
        };
      })();

      // Note(Sam): This following (not implemented) call might be neccessary to
      // create an animated, dashed line.
      // this.onStartCacheRequest_(request);

      const network = (async() => {
        const response = await request.response;
        this.onFinishRequest_(response);
        this.writeToIDB_(response); // don't wait for write to finish
        return {
          name: 'Network',
          result: await this.readFromCache_(),
        };
      })();

      this.onStartRequest_(request, network);

      // Start the race
      const winner = await Promise.race([cache, network]);

      // Check for results
      if (winner.result) {
        yield winner.result;
      }

      // Wait for the loser
      let loserMark;
      let loser;
      switch (winner.name) {
        case 'IndexedDB':
          loserMark = tr.b.Timing.mark('IndexedDB', 'write#loser#network');
          loser = await network;
          yield loser.result;
          break;

        case 'Network':
          loserMark = tr.b.Timing.mark('IndexedDB', 'write#loser#network');
          loser = await cache;
          if (loser.result) {
            yield loser.result;
          }
          break;

        default:
          throw new Error(`${winner.name} should not be in the race`);
      }
      loserMark.end();
    }
  }

  function csvRow(columns, cells) {
    const dict = {};
    for (let i = 0; i < columns.length; ++i) {
      dict[columns[i]] = cells[i];
    }
    return dict;
  }

  TimeseriesCache.reducers = {
    /*
     * type action = {
     *   request: any,
     *   cacheKey: string,
     *   refStatePath: string,
     *   fetchDescriptor: any,
     *   completion: Promise<any>,
     * }
     */
    request: (rootState, action) => {
      // Store action.request in
      // rootState.timeseries[cacheKey].requests[levelOfDetail]

      let timeseries;
      if (rootState.timeseries) {
        timeseries = rootState.timeseries[action.cacheKey];
      }

      const references = [action.refStatePath];
      let requests;
      if (timeseries) {
        references.push(...timeseries.references);
        requests = {...timeseries.requests};
        requests[action.fetchDescriptor.levelOfDetail] = [
          ...requests[action.fetchDescriptor.levelOfDetail],
        ];
      } else {
        requests = {
          [LEVEL_OF_DETAIL.XY]: [],
          [LEVEL_OF_DETAIL.ANNOTATIONS]: [],
          [LEVEL_OF_DETAIL.HISTOGRAM]: [],
        };
      }

      requests[action.fetchDescriptor.levelOfDetail].push({
        request: action.request,
        completion: action.completion,

        // Question(Sam): Where/what is `shouldFetch`?
        // Some of these might be undefined. shouldFetch will need to handle
        // that. reducers.receive will populate all of them.
        minRev: action.fetchDescriptor.minRev,
        maxRev: action.fetchDescriptor.maxRev,
        minTimestampMs: action.fetchDescriptor.minTimestampMs,
        maxTimestampMs: action.fetchDescriptor.maxTimestampMs,
      });

      const ranges = Object.keys(LEVEL_OF_DETAIL).reduce((prev, curr) => {
        return {
          ...prev,
          [LEVEL_OF_DETAIL[curr]]: [],
        };
      }, {});

      return {
        ...rootState,
        timeseries: {
          ...rootState.timeseries,
          [action.cacheKey]: {
            ...timeseries,
            references,
            requests,
            data: [],
            ranges,
            unit: tr.b.Unit.byName.unitlessNumber,
          },
        },
      };
    },

    /*
     * type action = {
     *   fetchDescriptor: any,
     *   cacheKey: string,
     *   columns: [string],
     *   timeseries: [any],
     *   units: string,
     *   minRevision?: number,
     *   maxRevision?: number,
     * };
     */
    receive: (rootState, action) => {
      let unit = tr.b.Unit.byJSONName[action.units];
      let conversionFactor = 1;
      if (!unit) {
        const info = tr.v.LEGACY_UNIT_INFO.get(action.units);
        if (info) {
          conversionFactor = info.conversionFactor || 1;
          unit = tr.b.Unit.byName[info.name];
        } else {
          unit = tr.b.Unit.byName.unitlessNumber;
        }
      }

      const data = (action.timeseries || []).map(row =>
        FastHistogram.fromRow(
            csvRow(action.columns, row),
            action.fetchDescriptor,
            conversionFactor
        )
      );

      const entry = rootState.timeseries[action.cacheKey];
      const {
        levelOfDetail,
        minRev, // undefined
        maxRev, // undefined
        minTimestampMs, // undefined
        maxTimestampMs, // undefined
      } = action.fetchDescriptor;

      // Update ranges
      const rangeReceived = tr.b.math.Range.fromExplicitRange(
          action.minRevision, action.maxRevision);

      const currRanges = entry.ranges[levelOfDetail];
      const nextRanges = rangeReceived.mergeIntoArray(currRanges);

      // Update requests
      const rangeRequests = entry.requests[levelOfDetail].map(rangeRequest => {
        if (rangeRequest.minRev !== minRev ||
            rangeRequest.maxRev !== maxRev ||
            rangeRequest.minTimestampMs !== minTimestampMs ||
            rangeRequest.maxTimestampMs !== maxTimestampMs) {
          return rangeRequest;
        }
        return {
          ...rangeRequest,
          request: undefined,
          completion: undefined,
        };
      });

      return {
        ...rootState,
        timeseries: {
          ...rootState.timeseries,
          [action.cacheKey]: {
            ...entry,
            requests: {
              ...entry.requests,
              [levelOfDetail]: rangeRequests,
            },
            ranges: {
              ...entry.ranges,
              [levelOfDetail]: nextRanges,
            },
            unit,
            data,
          }
        },
      };
    },
  };

  cp.ElementBase.registerReducers(TimeseriesCache);

  const TimeseriesReader = ({ dispatch, getState, ...options }) =>
    new TimeseriesCache(options, dispatch, getState).reader();

  return {
    FastHistogram,
    LEVEL_OF_DETAIL,
    TimeseriesReader,
  };
});
