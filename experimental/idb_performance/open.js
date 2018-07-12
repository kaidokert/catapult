'use strict';

import {
  addResult,
  append,
  newLine,
  changeStatus,
  randomString,
  startMark,
  endMark,
  getAverageMark,
} from './shared.js';


async function runIDB() {
  const dbName = randomString();
  startMark('idb');

  await idb.open(dbName, 1, upgradeDB => {
    switch (upgradeDB.oldVersion) {
      case 0:
        upgradeDB.createObjectStore('metadata');
        upgradeDB.createObjectStore('dataPoints');
    }
  });

  endMark('idb');
}

function runNative() {
  const dbName = randomString();
  startMark('native');
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
      endMark('native');
      resolve();
    };
  });
}

// Run benchmarks
async function testMethod(name, method, connections) {
  startMark(`${name}-parallel-${connections}`);
  const promises = [];
  for (let i = 0; i < connections; i++) {
    promises.push(method());
  }
  await Promise.all(promises);
  endMark(`${name}-parallel-${connections}`);
}

async function test({
  initial,
  max,
  step,
  samples = 5,
}) {
  const xAxis = [];
  const idbResults = [];
  const nativeResults = [];

  for (let i = initial; i <= max; i += step) {
    changeStatus(`Running ${i} parallel connections...`);
    xAxis.push(i);

    for (let j = 1; j <= samples; j++) {
      changeStatus(`Running ${i} parallel connections... idb sample ${j}`);
      await testMethod('idb', runIDB, i);
    }
    idbResults.push(getAverageMark(`idb-parallel-${i}`));

    for (let j = 1; j <= samples; j++) {
      changeStatus(`Running ${i} parallel connections... native sample ${j}`);
      await testMethod('native', runNative, i);
    }
    nativeResults.push(getAverageMark(`native-parallel-${i}`));
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
        label: 'idb',
        data: idbResults,
        backgroundColor: colors.green,
        borderColor: colors.green,
        fill: false,
      }, {
        label: 'native',
        data: nativeResults,
        backgroundColor: colors.blue,
        borderColor: colors.blue,
        fill: false,
      }],
    },
    options: {
      responsive: true,
      title: {
        display: true,
        text: 'Opening database connections',
      },
      scales: {
        yAxes: [{
          display: true,
          scaleLabel: {
            display: true,
            labelString: 'Average time per connection (ms)',
          },
        }],
        xAxes: [{
          display: true,
          scaleLabel: {
            display: true,
            labelString: 'Parallel connections',
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
  initial: 1,
  max: 50,
  step: 5,
});
