'use strict';

import { addResult,
  append,
  newLine,
  changeStatus,
  randomString,
  randomNumber,
  startMark,
  endMark,
  getAverageMark,
} from './shared.js';


async function nestedOpen(line) {
  startMark('nested-open');
  const db = await idb.open(line, 1, upgradeDB => {
    switch (upgradeDB.oldVersion) {
      case 0:
        upgradeDB.createObjectStore('metadata');
        upgradeDB.createObjectStore('dataPoints');
    }
  });
  endMark('nested-open');
  return db;
}

async function nestedWrite(line) {
  startMark('nested-write');
  const db = await nestedOpen(line);
  const tx = db.transaction(['dataPoints', 'metadata'], 'readwrite');
  const dataStore = tx.objectStore('dataPoints');
  const metaStore = tx.objectStore('metadata');
  for (let i = 1; i <= 10000; i++) {
    const key = i;
    const value = {
      revision: i,
      value: randomNumber(),
    };
    dataStore.put(value, key);
  }
  metaStore.put('avg', 'units');
  metaStore.put(['revision', 'value'], 'columns');
  await tx.complete;
  endMark('nested-write');
}

async function nestedRead(line, start, end) {
  startMark('nested-read');
  startMark(`nested-read-${start}-${end}`);
  const db = await nestedOpen(line);
  const tx = db.transaction('dataPoints', 'readonly');
  const dataStore = tx.objectStore('dataPoints');

  const range = IDBKeyRange.bound(start, end);
  const results = [];
  dataStore.iterateCursor(range, cursor => {
    if (!cursor) return;
    results.push(cursor.value);
    cursor.continue();
  });
  await tx.complete;
  endMark(`nested-read-${start}-${end}`);
  endMark('nested-read');
}

async function runNested(start, end) {
  const line = randomString();
  startMark(`nested-${start}-${end}`);
  await nestedWrite(line);
  await nestedRead(line, start, end);
  endMark(`nested-${start}-${end}`);
}

async function flatOpen() {
  startMark('flat-open');
  const db = await idb.open('benchmark', 1, upgradeDB => {
    if (upgradeDB.oldVersion === 0) {
      const metaStore = upgradeDB.createObjectStore('metadata');
      metaStore.createIndex('line', 'line');

      const dataStore = upgradeDB.createObjectStore('dataPoints');
      dataStore.createIndex('line-revision', ['line', 'revision']);
    }
  });
  endMark('flat-open');
  return db;
}

async function flatWrite(db, line) {
  startMark('flat-write');
  const tx = db.transaction(['dataPoints', 'metadata'], 'readwrite');
  const dataStore = tx.objectStore('dataPoints');
  const metaStore = tx.objectStore('metadata');
  for (let i = 1; i <= 10000; i++) {
    const key = `${line}${i}`;
    const value = {
      line,
      revision: i,
      value: randomNumber(),
    };
    dataStore.put(value, key);
  }
  metaStore.put('avg', 'units');
  metaStore.put(['revision', 'value'], 'columns');
  await tx.complete;
  endMark('flat-write');
}

async function flatRead(db, line, start, end) {
  startMark('flat-read');
  startMark(`flat-read-${start}-${end}`);
  const tx = db.transaction('dataPoints', 'readonly');
  const dataStore = tx.objectStore('dataPoints');
  const index = dataStore.index('line-revision');
  const range = IDBKeyRange.bound([line, start], [line, end]);

  const results = [];
  index.iterateCursor(range, cursor => {
    if (!cursor) return;
    results.push(cursor.value);
    cursor.continue();
  });
  await tx.complete;

  endMark(`flat-read-${start}-${end}`);
  endMark('flat-read');
}

async function runFlat(start, end) {
  const line = randomString();
  startMark(`flat-${start}-${end}`);
  const db = await flatOpen();
  await flatWrite(db, line);
  await flatRead(db, line, start, end);
  endMark(`flat-${start}-${end}`);
}

// Run benchmarks
async function test({
  initial,
  max,
  step,
  samples = 5,
}) {
  changeStatus('Running...');

  const xAxis = [];
  const nestedResults = [];
  const flatResults = [];

  for (let i = initial; i <= max; i += step) {
    xAxis.push(i);

    for (let j = 1; j <= samples; j++) {
      changeStatus(`Running nested ${i}/10000 sample ${j}/${samples}...`);
      await runNested(0, i);
    }
    nestedResults.push(getAverageMark(`nested-read-0-${i}`));

    for (let j = 1; j <= samples; j++) {
      changeStatus(`Running flat ${i}/10000 sample ${j}/${samples}...`);
      await runFlat(0, i);
    }
    flatResults.push(getAverageMark(`flat-read-0-${i}`));
  }

  changeStatus('Done!');

  const colors = {
    blue: '#2196F3',
    green: '#4CAF50',
    yellow: '#FFEB3B',
    red: '#F44336',
  };

  const ctx = document.getElementById('chart');
  const chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: xAxis,
      datasets: [{
        label: 'flat',
        data: flatResults,
        backgroundColor: colors.green,
        borderColor: colors.green,
        fill: false,
      }, {
        label: 'nested',
        data: nestedResults,
        backgroundColor: colors.blue,
        borderColor: colors.blue,
        fill: false,
      }],
    },
    options: {
      responsive: true,
      title: {
        display: true,
        text: 'IndexedDB Internal Structure',
      },
      scales: {
        yAxes: [{
          display: true,
          scaleLabel: {
            display: true,
            labelString: 'Average time per read (ms)',
          },
        }],
        xAxes: [{
          display: true,
          scaleLabel: {
            display: true,
            labelString: 'Read size',
          },
        }],
      },
      legend: {
        position: 'bottom',
      },
    },
  });
}

test({
  initial: 1000,
  max: 10000,
  step: 1000,
});
