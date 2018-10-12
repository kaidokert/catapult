/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import Range from './range.js';
import {
  CacheRequestBase, READONLY, READWRITE, jsonResponse,
} from './cache-request-base.js';
import ResultChannelSender from './result-channel-sender.js';

const STORE_REPORTS = 'reports';
const STORE_METADATA = 'metadata';
const STORES = [STORE_REPORTS, STORE_METADATA];

export default class ReportCacheRequest extends CacheRequestBase {
  constructor(fetchEvent) {
    super(fetchEvent);
    const {searchParams} = new URL(fetchEvent.request.url);

    const id = searchParams.get('id');
    if (!id) throw new Error('ID is not specified for this report request!');

    this.templateId_ = parseInt(id);
    if (isNaN(this.templateId_)) {
      throw new Error('Template ID is not a real number!');
    }

    const modified = searchParams.get('modified');
    if (!modified) {
      throw new Error('Modified is not specified for this report request!');
    }
    this.modified_ = parseInt(modified);
    if (isNaN(this.modified_)) {
      throw new Error(`Modified is not a valid number: ${modified}`);
    }

    const revisions = searchParams.get('revisions');
    if (!revisions) {
      throw new Error('Revisions is not specified for this report request!');
    }
    this.revisions_ = revisions.split(',');

    // Data can be stale if the template was modified after being stored on
    // IndexedDB. This value is modified in read() and later used in write().
    this.isTemplateDifferent_ = false;
  }

  respond() {
    this.fetchEvent.respondWith(this.responsePromise.then(jsonResponse));
    const sender = new ResultChannelSender(this.fetchEvent.request.url);
    this.fetchEvent.waitUntil(sender.send(this.generateResults()));
  }

  async* generateResults() {
    const otherRequest = await this.findInProgressRequest(async other => (
      (other.templateId_ === this.templateId_) &&
      (other.revisions_.join(',') === this.revisions_.join(','))));
    if (otherRequest) {
      // Be sure to call onComplete() to remove `this` from IN_PROGRESS_REQUESTS
      // so that `otherRequest.generateResults()` doesn't await
      // `this.generateResults()`.
      this.onComplete();
      this.readNetworkPromise = otherRequest.readNetworkPromise;
    } else {
      this.readNetworkPromise = this.readNetwork_();
    }

    const readDatabasePromise = this.readDatabase_().then(result => {
      return {result, source: 'database'};
    });
    const readNetworkPromise = this.readNetworkPromise.then(result => {
      return {result, source: 'network'};
    });
    const winner = Promise.race([readDatabasePromise, readNetworkPromise]);
    if (winner.source === 'database' && winner.result) yield winner.result;
    const networkResult = await this.readNetworkPromise;
    yield networkResult;
    this.scheduleWrite(networkResult);
  }

  async readDatabase_() {
    const timing = this.time('Cache');
    const database = await this.databasePromise;
    const reponse = await this.read(database);

    if (response) {
      timing.end();
    } else {
      timing.remove();
    }

    return response;
  }

  async writeDatabase(networkResults) {
    const database = await this.databasePromise;
    const timing = this.time('Write');
    const results = await this.write(database, networkResults);
    timing.end();
    return results;
  }

  async readNetwork_() {
    let timing = this.time('Network');
    const response = await fetch(this.fetchEvent.request);
    timing.end();

    timing = this.time('Parse JSON');
    const json = await response.json();
    timing.end();

    return json;
  }

  get databaseName() {
    return ReportCacheRequest.databaseName({id: this.templateId_});
  }

  get databaseVersion() {
    return 1;
  }

  async upgradeDatabase(db) {
    if (db.oldVersion < 1) {
      db.createObjectStore(STORE_REPORTS);
      db.createObjectStore(STORE_METADATA);
    }
  }

  async read(db) {
    const transaction = db.transaction(STORES, READONLY);

    // Start all asynchronous actions at once then "await" only the results
    // needed.
    const reportsPromise = this.getReports_(transaction);
    const metadataPromises = {
      editable: this.getMetadata_(transaction, 'editable'),
      internal: this.getMetadata_(transaction, 'internal'),
      modified: this.getMetadata_(transaction, 'modified'),
      name: this.getMetadata_(transaction, 'name'),
      owners: this.getMetadata_(transaction, 'owners'),
      rows: this.getMetadata_(transaction, 'rows'),
      statistics: this.getMetadata_(transaction, 'statistics'),
    };

    // Check the "modified" query parameter to verify that the template was not
    // modified after storing the data on IndexedDB. Returns true if the data is
    // stale and needs to be rewritten; otherwise, false.
    const lastModified = await metadataPromises.modified;
    if (typeof lastModified !== 'number') return;
    if (lastModified !== this.modified_) {
      this.isTemplateDifferent_ = true;
      return;
    }

    const rows = await metadataPromises.rows;

    // Rows is undefined when no data has been cached yet.
    if (!Array.isArray(rows)) return;

    const reportsByRevision = await reportsPromise;

    // Check if there are no matching revisions
    if (Object.keys(reportsByRevision).length === 0) return;

    return {
      editable: await metadataPromises.editable,
      id: this.templateId_,
      internal: await metadataPromises.internal,
      name: await metadataPromises.name,
      owners: await metadataPromises.owners,
      report: {
        rows: this.mergeRowsWithReports_(rows, reportsByRevision),
        statistics: await metadataPromises.statistics,
      },
    };
  }

  // Merge row metadata with report data indexed by revision.
  mergeRowsWithReports_(rows, reportsByRevision) {
    return rows.map((row, rowIndex) => {
      const data = {};
      for (const revision of this.revisions_) {
        if (!Array.isArray(reportsByRevision[revision])) continue;
        if (!reportsByRevision[revision][rowIndex]) continue;
        data[revision] = reportsByRevision[revision][rowIndex];
      }
      return {
        ...row,
        data,
      };
    });
  }

  async getReports_(transaction) {
    const timing = this.time('Read - Reports');
    const reportStore = transaction.objectStore(STORE_REPORTS);

    const reportsByRevision = {};
    await Promise.all(this.revisions_.map(async(revision) => {
      const reports = await reportStore.get(revision);
      if (reports) {
        reportsByRevision[revision] = reports;
      }
    }));

    timing.end();
    return reportsByRevision;
  }

  async getMetadata_(transaction, key) {
    const timing = this.time('Read - Metadata');
    const metadataStore = transaction.objectStore(STORE_METADATA);
    const result = await metadataStore.get(key);
    timing.end();
    return result;
  }

  async write(db, networkResults) {
    const {report: networkReport, ...metadata} = networkResults;
    const {rows: networkRows, statistics} = networkReport;

    const transaction = db.transaction(STORES, READWRITE);
    await Promise.all([
      this.writeReports_(transaction, networkResults),
      this.writeMetadata_(transaction, networkResults),
    ]);

    const timing = this.time('Write - Queued Tasks');
    await transaction.complete;
    timing.end();
  }

  async writeReports_(transaction, networkResults) {
    const reportStore = transaction.objectStore(STORE_REPORTS);

    // When the report template changes, reports may pertain to different
    // benchmarks.
    if (this.isTemplateDifferent_) {
      await reportStore.clear();
    }

    // Organize reports by revision to optimize for reading by revision.
    const reportsByRevision = getReportsByRevision(networkResults.report.rows);

    // Store reportsByRevision in the "reports" object store.
    for (const [revision, reports] of Object.entries(reportsByRevision)) {
      reportStore.put(reports, revision);
    }
  }

  async writeMetadata_(transaction, networkResults) {
    const metadataStore = transaction.objectStore(STORE_METADATA);

    // When the report template changes, any portion of the metadata can change.
    if (this.isTemplateDifferent_) {
      await metadataStore.clear();
    }

    const {report: networkReport, ...metadata} = networkResults;
    const {rows: networkRows, statistics} = networkReport;

    // Store everything in "rows" but "data"; that belongs in the "reports"
    // store, which is handled by `writeReports_`.
    const rows = networkRows.map(({data: _, ...row}) => row);

    metadataStore.put(rows, 'rows');
    metadataStore.put(statistics, 'statistics');
    metadataStore.put(this.modified_, 'modified');

    for (const [key, value] of Object.entries(metadata)) {
      metadataStore.put(value, key);
    }
  }
}

ReportCacheRequest.databaseName = (options) => `report/${options.id}`;

function getReportsByRevision(networkRows) {
  const reportsByRevision = {};

  for (let i = 0; i < networkRows.length; ++i) {
    const {data} = networkRows[i];

    for (const [revision, report] of Object.entries(data)) {
      // Verify there is an array of reports for this revision.
      if (!Array.isArray(reportsByRevision[revision])) {
        reportsByRevision[revision] = [];
      }

      // Add this report to the corresponding row.
      reportsByRevision[revision][i] = report;
    }
  }

  return reportsByRevision;
}
