/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import Range from './range.js';
import {CacheRequestBase, READONLY, READWRITE} from './cache-request-base.js';

/**
 * Timeseries are stored in IndexedDB to optimize the speed of ranged reading.
 * Here is the structure in TypeScript:
 *
 *   type TimeseriesDatabase = {
 *     // Data is optimized for range queries
 *     data: {
 *       [revision: number]: Datum
 *     },
 *
 *     // Maintain the ranges of available data
 *     ranges: [Range],
 *
 *     // Miscellaneous data that doesn't change for each datum
 *     metadata: {
 *       improvement_direction: number,
 *       units: string
 *     }
 *   }
 *
 *   type Datum = {
 *     revision: number,
 *     timestamp?: Date,
 *     [statistic: string]: number
 *   }
 *
 *   type Range = [number, number]
 *
 */

// Constants for the database structure
const STORE_DATA = 'data';
const STORE_METADATA = 'metadata';
const STORE_RANGES = 'ranges';
const STORES = [STORE_DATA, STORE_METADATA, STORE_RANGES];

export default class TimeseriesCacheRequest extends CacheRequestBase {
  constructor(fetchEvent) {
    super(fetchEvent);
    const {searchParams} = new URL(fetchEvent.request.url);

    this.statistic_ = searchParams.get('statistic');
    if (!this.statistic_) {
      throw new Error('Statistic was not specified');
    }

    const columns = searchParams.get('columns');
    if (!columns) {
      throw new Error('Columns was not specified');
    }
    this.columns_ = columns.split(',');

    this.maxRevision_ = parseInt(searchParams.get('max_revision')) || undefined;
    this.minRevision_ = parseInt(searchParams.get('min_revision')) || undefined;
    this.revisionRange_ = Range.fromExplicitRange(
        this.minRevision_ || 0, this.maxRevision_ || Number.MAX_SAFE_INTEGER);

    this.testSuite_ = searchParams.get('test_suite') || '';
    this.measurement_ = searchParams.get('measurement') || '';
    this.bot_ = searchParams.get('bot') || '';
    this.testCase_ = searchParams.get('test_case') || '';
    this.buildType_ = searchParams.get('build_type') || '';
  }

  get timingCategory() {
    return 'Timeseries';
  }

  get databaseName() {
    return TimeseriesCacheRequest.databaseName({
      testSuite: this.testSuite_,
      measurement: this.measurement_,
      bot: this.bot_,
      testCase: this.testCase_,
      buildType: this.buildType_,
    });
  }

  get databaseVersion() {
    return 1;
  }

  async upgradeDatabase(db) {
    if (db.oldVersion < 1) {
      db.createObjectStore(STORE_DATA);
      db.createObjectStore(STORE_METADATA);
      db.createObjectStore(STORE_RANGES);
    }
  }

  get raceCacheAndNetwork_() {
    return async function* () {
      const cacheResult = await this.readCache_();
      let missingRanges = [this.revisionRange_];
      if (cacheResult.result && cacheResult.result.data) {
        yield cacheResult;
        // TODO
        missingRanges = Range.findDifference(
            this.revisionRange_, cacheResult.result.availableRangeByCol);
      }
      // TODO if a col is available for revisionRange_, then don't fetch that col
      // TODO if all cols are available for some subrange, then don't fetch that range

      const networkPromises = missingRanges.map((range, index) =>
        this.readNetwork_(range).then(result => {
          return {result, index};
        }));
      while (networkPromises.length) {
        const {result, index} = Promise.race(networkPromises);
        networkPromises.splice(index, 1);
        if (result) yield result;
      }
      CacheRequestBase.writer.enqueue(() => this.writeIDB_(res.result));
    };
  }

  async readNetwork_(range) {
    const params = {
      test_suite: this.testSuite_,
      measurement: this.measurement_,
      bot: this.bot_,
      build_type: this.buildType_,
      columns: this.columns_.join(','),
    };
    if (range.min) params.min_revision = range.min;
    if (range.max < Number.MAX_SAFE_INTEGER) params.max_revision = range.max;
    if (this.testCase_) params.test_case = this.testCase_
    let url = new URL(this.fetchEvent.request.url);
    url = url.origin + url.pathname + '?' + new URLSearchParams(params);
    const response = await this.timePromise('Network', fetch(url, {
      method: this.fetchEvent.request.method,
      headers: this.fetchEvent.request.headers,
    }));
    const json = await this.timePromise('Parse JSON', response.json());
    return {
      name: 'Network',
      result: json,
    };
  }

  async read(db) {
    const transaction = db.transaction(STORES, READONLY);

    const dataPointsPromise = this.getDataPoints_(transaction);
    const [
      improvementDirection,
      units,
      rangesByCol,
    ] = await Promise.all([
      this.getMetadata_(transaction, 'improvement_direction'),
      this.getMetadata_(transaction, 'units'),
      this.getRanges_(transaction),
    ]);

    const availableRangeByCol = this.getAvailableRangeByCol_(rangesByCol);
    if (availableRangeByCol.size === 0) return;
    return {
      availableRangeByCol,
      improvement_direction: improvementDirection,
      units,
      data: this.denormalize_(await dataPointsPromise),
    };
  }

  getAvailableRangeByCol_(rangesByCol) {
    const availableRangeByCol = new Map();
    if (!rangesByCol) return availableRangeByCol;
    for (const [col, rangeDicts] of rangesByCol) {
      // TODO read whatever data is available, fetch whatever isn't
      for (const rangeDict of rangeDicts) {
        const range = Range.fromDict(rangeDict);
        const intersection = range.findIntersection(this.revisionRange_);
        if (!intersection.isEmpty) {
          availableRangeByCol.set(col, intersection);
          break;
        }
      }
    }
    return availableRangeByCol;
  }

  /**
   * Denormalize converts the object result from IndexedDB into a tuple with the
   * order specified by the HTTP request's "columns" search parameter.
   *
   * Data point:
   *
   *   {
   *     revision: 564174,
   *     timestamp: "2018-06-05T00:24:35.140250",
   *     avg: 2322.302789,
   *   }
   *
   * Tuple w/ headers ['revision', 'timestamp', 'avg']:
   *
   *   [564174, "2018-06-05T00:24:35.140250", 2322.302789]
   *
   */
  denormalize_(dataPoints) {
    const timing = this.time('Read - Denormalize');

    const denormalizedDatapoints = [];
    for (const dataPoint of dataPoints) {
      const result = [];
      for (const column of this.columns_) {
        result.push(dataPoint[column]);
      }
      denormalizedDatapoints.push(result);
    }

    timing.end();
    return denormalizedDatapoints;
  }

  async getMetadata_(transaction, key) {
    const store = transaction.objectStore(STORE_METADATA);
    return await this.timePromise('Read - Metadata', store.get(key));
  }

  async getRanges_(transaction) {
    const rangeStore = transaction.objectStore(STORE_RANGES);
    const promises = [];
    for (const col of this.columns_) {
      if (col === 'revision') continue;
      promises.push(rangeStore.get(col).then(ranges => [col, ranges]));
    }
    const timing = this.time('Read - Ranges');
    const rangesByCol = await Promise.all(promises);
    timing.end();
    return new Map(rangesByCol);
  }

  async getDataPoints_(transaction) {
    const timing = this.time('Read - Datapoints');
    const dataStore = transaction.objectStore(STORE_DATA);
    if (!this.minRevision_ && !this.maxRevision_) {
      const dataPoints = await dataStore.getAll();
      return dataPoints;
    }

    const dataPoints = [];
    dataStore.iterateCursor(this.range_, cursor => {
      if (!cursor) return;
      dataPoints.push(cursor.value);
      cursor.continue();
    });

    await transaction.complete;
    timing.end();
    return dataPoints;
  }

  get range_() {
    if (this.minRevision_ && this.maxRevision_) {
      return IDBKeyRange.bound(this.minRevision_, this.maxRevision_);
    }
    if (this.minRevision_ && !this.maxRevision_) {
      return IDBKeyRange.lowerBound(this.minRevision_);
    }
    if (!this.minRevision_ && this.maxRevision_) {
      return IDBKeyRange.upperBound(this.maxRevision_);
    }
  }

  async write(db, networkResults) {
    const {data: networkData, ...metadata} = networkResults;

    if (metadata.error) return;
    if (!Array.isArray(networkData) || networkData.length === 0) return;

    const data = this.normalize_(networkData);

    const transaction = db.transaction(STORES, READWRITE);
    await Promise.all([
      this.writeData_(transaction, data),
      this.writeRanges_(transaction, data),
    ]);
    this.writeMetadata_(transaction, metadata);
    await this.timePromise('Write - Queued Tasks', transaction.complete);
  }

  /**
   * Normalize maps each unnamed column to its cooresponding name in the
   * QueryParams. Returns an object with key/value pairs representing
   * column/value pairs. Each datapoint will have a structure similar to the
   * following:
   *   {
   *     revision: 12345,
   *     [statistic]: 42
   *   }
   */
  normalize_(networkData) {
    const timing = this.time('Write - Normalize');

    const data = (networkData || []).map(datum => {
      const normalizedDatum = {};
      for (let i = 0; i < this.columns_.length; ++i) {
        normalizedDatum[this.columns_[i]] = datum[i];
      }
      return normalizedDatum;
    });

    timing.end();
    return data;
  }

  async writeData_(transaction, data) {
    const timing = this.time('Write - Data');
    const dataStore = transaction.objectStore(STORE_DATA);
    for (const datum of data) {
      // Merge with existing data
      const prev = await dataStore.get(datum.revision);
      const next = Object.assign({}, prev, datum);
      dataStore.put(next, datum.revision);
    }
    timing.end();
  }

  async writeRanges_(transaction, data) {
    const firstDatum = data[0] || {};
    const lastDatum = data[data.length - 1] || {};
    const min = this.minRevision_ || firstDatum.revision || undefined;
    const max = this.maxRevision_ || lastDatum.revision || undefined;
    if (!min && !max) {
      throw new Error('Min/max cannot be found; unable to update ranges');
    }
    const rangeStore = transaction.objectStore(STORE_RANGES);
    const currRange = Range.fromExplicitRange(min, max);
    const timing = this.time('Write - Ranges');
    await Promise.all(this.columns_.filter(col => col !== 'revision').map(
        async col => {
          const prevRangesRaw = (await rangeStore.get(col)) || [];
          const prevRanges = prevRangesRaw.map(Range.fromDict);
          const newRanges = currRange.mergeIntoArray(prevRanges);
          rangeStore.put(newRanges.map(range => range.toJSON()), col);
        }));
    timing.end();
  }

  writeMetadata_(transaction, metadata) {
    const metadataStore = transaction.objectStore(STORE_METADATA);

    for (const [key, value] of Object.entries(metadata)) {
      metadataStore.put(value, key);
    }
  }
}

/**
 * type options = {
 *   timeseries: string,
 *   testSuite: string,
 *   measurement: string,
 *   bot: string,
 *   testCase?: string,
 *   buildType?: string,
 * }
 */
TimeseriesCacheRequest.databaseName = ({
  timeseries,
  testSuite,
  measurement,
  bot,
  testCase = '',
  buildType = ''}) => (
  `timeseries/${testSuite}/${measurement}/${bot}/${testCase}/${buildType}`
);
