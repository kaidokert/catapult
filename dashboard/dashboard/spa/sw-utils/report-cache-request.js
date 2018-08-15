/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import Range from './range.js';
import { CacheRequestBase } from './cache-request-base.js';


export default class ReportCacheRequest extends CacheRequestBase {
  constructor(request) {
    super(request);
    const { searchParams } = new URL(request.url);

    const id = searchParams.get('id');
    if (!id) {
      throw new Error('ID is not specified for this report request!');
    }
    this.dbName = `report/${id}`;

    this.templateId = parseInt(id);
    if (isNaN(this.templateId)) {
      throw new Error('Template ID is not a real number!');
    }

    const modified = searchParams.get('modified');
    if (!modified) {
      throw new Error('Modified is not specified for this report request!');
    }
    this.modified = parseInt(modified);
    if (isNaN(this.modified)) {
      throw new Error(`Modified is not a valid number: ${modified}`);
    }

    const revisions = searchParams.get('revisions');
    if (!revisions) {
      throw new Error('Revisions is not specified for this report request!');
    }
    this.revisions = revisions.split(',');

    // Data can be stale if the template was modified after being stored on
    // IndexedDB. This value is modified in read() and later used in write().
    this.isStale = false;
  }

  get timingCategory() {
    return 'Reports';
  }

  get databaseName() {
    return this.dbName;
  }

  get databaseVersion() {
    return 1;
  }

  async upgradeDatabase(db) {
    if (db.oldVersion < 1) {
      db.createObjectStore('metadata');
      db.createObjectStore('reports');
    }
  }

  async read(db) {
    const transaction = db.transaction(['reports', 'metadata'], 'readonly');

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
    if (lastModified !== this.modified) {
      this.isStale = true;
      return;
    }

    const rows = await metadataPromises.rows;

    // Rows is undefined if no data has been cached yet.
    if (!Array.isArray(rows)) return;

    const reportsByRevision = await reportsPromise;

    // Check if there are no matching revisions
    if (Object.keys(reportsByRevision).length === 0) return;

    //
    const rowsResult = rows.map((row, rowIndex) => {
      const data = {};
      for (const revision of this.revisions) {
        if (!Array.isArray(reportsByRevision[revision])) continue;
        if (!reportsByRevision[revision][rowIndex]) continue;
        data[revision] = reportsByRevision[revision][rowIndex];
      }
      return {
        ...row,
        data,
      };
    });

    return {
      editable: await metadataPromises.editable,
      id: this.templateId,
      internal: await metadataPromises.internal,
      name: await metadataPromises.name,
      owners: await metadataPromises.owners,
      report: {
        rows: rowsResult,
        statistics: await metadataPromises.statistics,
      },
    };
  }

  async getReports_(transaction) {
    const timing = this.time('Read - Reports');
    const reportStore = transaction.objectStore('reports');

    const reportsByRevision = {};
    await Promise.all(this.revisions.map(async(revision) => {
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
    const metadataStore = transaction.objectStore('metadata');
    const result = await metadataStore.get(key);
    timing.end();
    return result;
  }

  async write(db, networkResults) {
    const { report: networkReport, ...metadata } = networkResults;
    const { rows: networkRows, statistics } = networkReport;

    // Store information about the timeseries
    const transaction = db.transaction(['reports', 'metadata'], 'readwrite');
    const reportStore = transaction.objectStore('reports');
    const metadataStore = transaction.objectStore('metadata');

    // Clear everything if the template changed.
    if (this.isStale) {
      await Promise.all([
        reportStore.clear(),
        metadataStore.clear(),
      ]);
    }

    // Go through each row from the network and separate the data into "rows"
    // and "reports".
    const rows = [];
    const reportsByRevision = {};

    for (let i = 0; i < networkRows.length; ++i) {
      const { data, ...row } = networkRows[i];
      rows.push(row);

      for (const [revision, report] of Object.entries(data)) {
        // Verify there is an array of reports for this revision.
        if (!Array.isArray(reportsByRevision[revision])) {
          reportsByRevision[revision] = [];
        }

        // Add this report to the corresponding row.
        reportsByRevision[revision][i] = report;
      }
    }

    // Store reportsByRevision in the "reports" object store.
    for (const [revision, reports] of Object.entries(reportsByRevision)) {
      reportStore.put(reports, revision);
    }

    // Store metadata separately in the "metadata" object store.
    metadataStore.put(rows, 'rows');
    metadataStore.put(statistics, 'statistics');
    metadataStore.put(this.modified, 'modified');

    for (const [key, value] of Object.entries(metadata)) {
      metadataStore.put(value, key);
    }

    // Finish the transaction
    const timing = this.time('Write - Queued Tasks');
    await transaction.complete;
    timing.end();
  }
}
