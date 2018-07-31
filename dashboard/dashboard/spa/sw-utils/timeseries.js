/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import Range from './range.js';
import { IDBRace } from './race.js';
import { getColumnsByLevelOfDetail } from './level-of-detail.js';


export default class TimeseriesRace extends IDBRace {
  constructor(request) {
    super(request);
    const { searchParams } = new URL(request.url);

    this.statistic = searchParams.get('statistic');
    if (!this.statistic) {
      throw new Error('Statistic was not specified to TimeseriesRace');
    }

    this.levelOfDetail = searchParams.get('level_of_detail');
    if (!this.levelOfDetail) {
      throw new Error('Level Of Detail was not specified to TimeseriesRace');
    }

    this.columns = getColumnsByLevelOfDetail(this.levelOfDetail,
        this.statistic);

    const maxRevision = searchParams.get('max_revision');
    this.maxRevision = parseInt(maxRevision) || undefined;

    const minRevision = searchParams.get('min_revision');
    this.minRevision = parseInt(minRevision) || undefined;

    const testSuite = searchParams.get('test_suite') || '';
    const measurement = searchParams.get('measurement') || '';
    const bot = searchParams.get('bot') || '';
    const testCase = searchParams.get('test_case') || '';
    const buildType = searchParams.get('build_type') || '';
    this.key = `ts/${testSuite}/${measurement}/${bot}/${testCase}/${buildType}`;
  }

  get markCategory() {
    return 'Timeseries';
  }

  get url() {
    const url = new URL(this.request.url);
    url.searchParams.delete('level_of_detail');
    // url.searchParams.delete('columns');
    // url.searchParams.set('columns', this.columns);
    return url;
  }

  get databaseName() {
    return this.key;
  }

  get databaseVersion() {
    return 1;
  }

  async upgradeDatabase(db) {
    if (db.oldVersion < 1) {
      db.createObjectStore('dataPoints');
      db.createObjectStore('metadata');
      db.createObjectStore('ranges');
    }
  }

  async read(db) {
    const transaction = db.transaction(
        ['ranges', 'dataPoints', 'metadata'],
        'readonly'
    );

    const dataPointsPromise = this._getDataPoints(transaction);
    const [
      improvementDirection,
      units,
      ranges,
    ] = await Promise.all([
      this._getMetadata(transaction, 'improvement_direction'),
      this._getMetadata(transaction, 'units'),
      this._getRanges(transaction),
    ]);

    //
    // Ranges
    //

    if (!ranges) {
      // Nothing has been cached for this level-of-detail yet.
      return;
    }

    const requestedRange = Range.fromExplicitRange(this.minRevision,
        this.maxRevision);

    if (!requestedRange.isEmpty) {
      // Determine if any cached data ranges intersect with the requested range.
      const rangeIndex = ranges
          .map(range => Range.fromDict(range))
          .findIndex(range => {
            const intersection = range.findIntersection(requestedRange);
            return !intersection.isEmpty;
          });

      if (rangeIndex === -1) {
        // IndexedDB does not contain any relevant data for the requested range.
        return;
      }
    }

    //
    // Datapoints
    //

    const dataPoints = await dataPointsPromise;

    // Denormalize requested columns to an array with the same order as
    // requested.
    const mark = this.mark('Read - Denormalize');
    const denormalizedDatapoints = [];
    for (const dataPoint of dataPoints) {
      const result = [];
      for (const column of this.columns) {
        result.push(dataPoint[column]);
      }
      denormalizedDatapoints.push(result);
    }
    mark.end();

    return {
      improvement_direction: improvementDirection,
      units,
      data: denormalizedDatapoints,
    };
  }

  async _getMetadata(transaction, key) {
    const mark = this.mark('Read - Metadata');
    const metadataStore = transaction.objectStore('metadata');
    const result = await metadataStore.get(key);
    mark.end();
    return result;
  }

  async _getRanges(transaction) {
    const mark = this.mark('Read - Ranges');
    const rangeStore = transaction.objectStore('ranges');
    const ranges = await rangeStore.get(this.levelOfDetail);
    mark.end();
    return ranges;
  }

  async _getDataPoints(transaction) {
    const mark = this.mark('Read - Datapoints');
    const dataStore = transaction.objectStore('dataPoints');
    if (!this.minRevision || !this.maxRevision) {
      const dataPoints = await dataStore.getAll();
      return dataPoints;
    }

    const dataPoints = [];
    const range = IDBKeyRange.bound(this.minRevision, this.maxRevision);
    dataStore.iterateCursor(range, cursor => {
      if (!cursor) return;
      dataPoints.push(cursor.value);
      cursor.continue();
    });

    await transaction.complete;
    mark.end();
    return dataPoints;
  }

  async write(db, networkResults) {
    const { data, ...metadata } = networkResults;

    // Check for error in response
    if (metadata.error) {
      return;
    }

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
    //     [statistic]: 42
    //   }
    let mark = this.mark('Write - Normalize');

    const namedDatapoints = (data || []).map(datapoint =>
      this.columns.reduce(
          (prev, name, index) =>
            Object.assign(prev, { [name]: datapoint[index] }),
          {}
      )
    );

    mark.end();

    // Store timeseries as objects indexed by revision.
    mark = this.mark('Write - Merge datapoints');

    for (const datapoint of namedDatapoints) {
      // Merge with existing data
      const prev = await dataStore.get(datapoint.revision);
      const next = Object.assign({}, prev, datapoint);

      // IndexedDB should be fast enough to "get" for every data point. A
      // notable experiment might be to "getAll" and find by revision. We can
      // then compare performance between "get" and "getAll".

      dataStore.put(next, datapoint.revision);
    }

    mark.end();

    if (namedDatapoints.length === 0) {
      // No timeseries data to write.
      return;
    }

    // Update the range of data we contain in the "ranges" object store.
    const first = namedDatapoints[0] || {};
    const last = namedDatapoints[namedDatapoints.length - 1] || {};

    const min = this.minRevision ||
      first.revision ||
      undefined;

    const max = this.maxRevision ||
      last.revision ||
      undefined;

    if (min || max) {
      const currRange = Range.fromExplicitRange(min, max);
      const prevRangesRaw = await rangeStore.get(this.levelOfDetail) || [];
      const prevRanges = prevRangesRaw.map(Range.fromDict);

      const nextRanges = currRange
          .mergeIntoArray(prevRanges)
          .map(range => range.toJSON());

      rangeStore.put(nextRanges, this.levelOfDetail);
    } else {
      new Error('Min/max cannot be found; unable to update ranges');
    }

    // Store metadata separately in the "metadata" object store.
    for (const key of Object.keys(metadata)) {
      metadataStore.put(metadata[key], key);
    }

    // Finish the transaction
    mark = this.mark('Write - Queued Tasks');
    await transaction.complete;
    mark.end();
  }
}

