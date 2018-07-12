'use strict';

// Benchmark utility functions
export function addResult(result, element = 'div') {
  const results = document.getElementById('results');
  const entry = document.createElement(element);
  entry.textContent = result;
  results.appendChild(entry);
}

export function append(result) {
  addResult(result, 'span');
}

export function newLine() {
  addResult('');
}

export function changeStatus(status) {
  document.getElementById('status').textContent = status;
}

const chance = new Chance();

export function randomString(options) {
  return chance.string({
    length: 20,
    ...options,
  });
}

export function randomNumber(options) {
  return chance.floating(options);
}

export function startMark(name) {
  performance.mark(`${name}-start`);
}

export function endMark(name) {
  performance.mark(`${name}-end`);
  performance.measure(name, `${name}-start`, `${name}-end`);
}

export function getLatestMark(name) {
  const measures = performance.getEntriesByName(name);
  if (measures.length === 0) return null;
  return measures[measures.length - 1].duration;
}

export function getAverageMark(name) {
  const measures = performance.getEntriesByName(name);
  return measures.reduce(
      (total, measure) => total + (measure.duration / measures.length),
      0
  );
}

export function getAllMarks(name) {
  const measures = performance.getEntriesByName(name);
  return measures.map(measure => measure.duration);
}

performance.getAverageMark = getAverageMark;
