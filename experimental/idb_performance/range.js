'use strict';

// --- idb

async function runIDB(timeseries, metadata) {
  const dbName = Math.random().toString(36).substring(7);
  const start = new Date();

  const db = await idb.open('range benchmark', 1, upgradeDB => {
    switch (upgradeDB.oldVersion) {
      case 0:
        upgradeDB.createObjectStore('metadata');
        upgradeDB.createObjectStore('dataPoints');
    }
  });

  // Store information about the timeseries
  const transaction = db.transaction(
      ['dataPoints', 'metadata'],
      'readwrite'
  );

  const dataStore = transaction.objectStore('dataPoints');
  const metadataStore = transaction.objectStore('metadata');

  // Store timeseries indexed by r_commit_pos (preferred) or revision.
  // Take the response and map each unnamed column to its cooresponding
  // name in the QueryParams.
  for (const datapoint of (timeseries || [])) {
    const namedDatapoint = this.columns_.reduce(
        (prev, name, index) =>
          Object.assign(prev, { [name]: datapoint[index] }),
        {}
    );

    const pos = namedDatapoint.r_commit_pos || namedDatapoint.revision;
    const key = `${dbName}@${pos}`;

    // Merge with existing data
    // Note: IndexedDB should be fast enough to "get" for every key. A
    // notable experiment might be to "getAll" and find by key. We can
    // then compare performance between "get" and "getAll" solutions.
    const prev = await dataStore.get(key);
    const next = Object.assign({}, prev, namedDatapoint);

    dataStore.put(next, key);
  }

  // Store metadata separately in the "metadata" object store.
  for (const key of Object.keys(metadata)) {
    metadataStore.put(metadata[key], key);
  }

  // Store the columns available for data points in the "metadata" object
  // store. This is helpful to keep track of LOD.
  const nextColumns = [...new Set([
    ...prevColumns,
    ...this.columns_,
  ])];

  metadataStore.put(nextColumns, 'columns');

  // Finish the transaction
  await transaction.complete;

  const diff = new Date() - start;
  return diff;
}

// --- native

function runNative() {
  const dbName = Math.random().toString(36).substring(7);
  const start = new Date();

  return new Promise((resolve, reject) => {
    const request = window.indexedDB.open(dbName, 1);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      switch (event.oldVersion) {
        case 0:
          db.createObjectStore('metadata');
          db.createObjectStore('dataPoints');
      }
    };
    request.onerror = reject;
    request.onsuccess = () => {
      const diff = new Date() - start;
      resolve(diff);
    };
  });
}

// Run benchmarks
async function testMethod(method, connections) {
  const promises = [];
  for (let i = 0; i < connections; i++) {
    promises.push(method());
  }
  const diffs = await Promise.all(promises);
  const avg = diffs.reduce((prev, curr) => prev + (curr / diffs.length), 0);
  return avg;
}

async function testOpen(initial, max, step) {
  changeStatus('Running...');

  append(`Approach`);
  for (let i = initial; i <= max; i += step) {
    append(`,${i}`);
  }
  newLine();

  append(`idb`);
  for (let i = initial; i <= max; i += step) {
    const result = await testMethod(runIDB, i);
    append(`,${result}`);
  }
  newLine();

  append(`native`);
  for (let i = initial; i <= max; i += step) {
    const result = await testMethod(runNative, i);
    append(`,${result}`);
  }
  newLine();

  changeStatus('Done!');
}

async function test() {
  await testOpen(1, 50, 3);
}

