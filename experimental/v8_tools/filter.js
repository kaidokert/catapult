'use strict';
const BENCHMARK_OPTIONS = ['Memory', 'Duration'];
const MiB = 1024 * 1024;
Vue.component('v-select', VueSelect.VueSelect);

const menu = new Vue({
  el: '#menu',
  data: {
    sampleArr: null,
    guidValueInfo: null,

    chosenBenchmark: null,

    firstElement: null,
    secondElement: null,
    thirdElement: null,
    fourthElement: null,
    fifthElement: null,
    sixthElement: null,

    metricNames: null,

    browserOptions: [],
    subprocessOptions: [],

    componentMap: null,
    sizeMap: null,

    allLabels: [],
    testResults: [],
    referenceColumn: '',
    significanceTester: new MetricSignificance(),

    durationComponents: null
  },

  computed: {
    //  Depending on the file type, the selection for
    //  benchmarkOptions might be either memory or
    //  duration.
    benchmarkOptions() {
      if (!_.isEmpty(this.durationComponents) &&
          this.browserOptions.length !== 0) {
        return BENCHMARK_OPTIONS;
      }
      if (!_.isEmpty(this.durationComponents)) {
        return [BENCHMARK_OPTIONS[1]];
      }
      if (this.browserOptions.length !== 0) {
        return [BENCHMARK_OPTIONS[0]];
      }
      return undefined;
    },

    //  Memory benchmark should have more select boxes so
    //  we keep track checking if it is any memory metric.
    seenMetricsTree() {
      return this.chosenBenchmark === BENCHMARK_OPTIONS[0] ? true : false;
    },

    //  First select box might be either a browser option
    //  (for memory metrics) or a first level component in
    //  duration benchmark hierarchy.
    optionsFirstElement() {
      if (this.chosenBenchmark === null) {
        return undefined;
      }
      if (this.chosenBenchmark === BENCHMARK_OPTIONS[1]) {
        if (this.durationComponents === null) {
          return undefined;
        }
        return Object.getOwnPropertyNames(this.durationComponents);
      }
      return this.browserOptions;
    },

    //  Second select box might be either a subprocess
    //  (for memory metrics) or a second level component
    //  in duration benchmark hierarchy.
    optionsSecondElement() {
      if (this.chosenBenchmark === null) {
        return undefined;
      }
      if (this.chosenBenchmark === BENCHMARK_OPTIONS[1]) {
        if (this.durationComponents === null ||
          this.firstElement === null) {
          return undefined;
        }
        return Object.getOwnPropertyNames(this
            .durationComponents[this.firstElement]);
      }
      return this.subprocessOptions;
    },

    //  Third select box might be either a size (for memory
    //  metrics) or a third level component in duration metrics
    //  hierarchy.
    optionsThirdElement() {
      if (this.chosenBenchmark === null) {
        return undefined;
      }
      if (this.chosenBenchmark === BENCHMARK_OPTIONS[1]) {
        if (this.durationComponents === null ||
          this.firstElement === null ||
          this.secondElement === null) {
          return undefined;
        }
        return Object.getOwnPropertyNames(this
            .durationComponents[this
                .firstElement][this
                .secondElement]);
      }
      return this.sizeOptions;
    },

    optionsFourthElement() {
      if (this.chosenBenchmark === null) {
        return undefined;
      }
      if (this.chosenBenchmark === BENCHMARK_OPTIONS[1]) {
        if (this.durationComponents === null ||
          this.firstElement === null ||
          this.secondElement === null ||
          this.thirdElement === null) {
          return undefined;
        }
        return Object.getOwnPropertyNames(this
            .durationComponents[this
                .firstElement][this
                .secondElement][this
                .thirdElement]);
      }
      return this.componentsOptions;
    },

    optionsFifthElement() {
      if (this.chosenBenchmark === null) {
        return undefined;
      }
      if (this.chosenBenchmark === BENCHMARK_OPTIONS[1]) {
        if (this.durationComponents === null ||
          this.firstElement === null ||
          this.secondElement === null ||
          this.thirdElement === null ||
          this.fourthElement === null) {
          return undefined;
        }
        return Object.getOwnPropertyNames(this
            .durationComponents[this
                .firstElement][this
                .secondElement][this
                .thirdElement][this
                .fourthElement]);
      }
      return this.firstSubcompOptions;
    },

    optionsSixthElement() {
      if (this.chosenBenchmark === null) {
        return undefined;
      }
      if (this.chosenBenchmark === BENCHMARK_OPTIONS[1]) {
        return undefined;
      }
      return this.secondSubcompOptions;
    },

    //  Compute size options. The user will be provided with all
    //  sizes and the probe will be auto detected from it.
    sizeOptions() {
      if (this.chosenBenchmark === BENCHMARK_OPTIONS[1]) {
        return undefined;
      }
      if (this.sizeMap === null) {
        return undefined;
      }
      let sizes = [];
      for (const [key, value] of this.sizeMap.entries()) {
        sizes = sizes.concat(value);
      }
      return sizes;
    },

    //  The components are different depending on the type of probe.
    //  The probe is auto detected depending on the chosen size.
    //  Then the user is provided with the first level of components.
    componentsOptions() {
      if (this.chosenBenchmark === BENCHMARK_OPTIONS[1]) {
        return undefined;
      }
      if (this.componentMap === null || this.thirdElement === null) {
        return undefined;
      }
      for (const [key, value] of this.sizeMap.entries()) {
        if (value.includes(this.thirdElement)) {
          this.probe = key;
        }
      }
      const components = [];
      for (const [key, value] of this.componentMap.get(this.probe).entries()) {
        components.push(key);
      }
      return components;
    },

    //  Compute the options for the first subcomponent depending on the probes.
    //  When the user chooses a component, it might be a hierarchical one.
    firstSubcompOptions() {
      if (this.chosenBenchmark === BENCHMARK_OPTIONS[1]) {
        return undefined;
      }
      if (this.fourthElement === null) {
        return undefined;
      }
      const subcomponent = [];
      for (const [key, value] of this
          .componentMap.get(this.probe).get(this.fourthElement).entries()) {
        subcomponent.push(key);
      }
      return subcomponent;
    },

    //  In case when the component is from Chrome,
    //  the hierarchy might have more levels.
    secondSubcompOptions() {
      if (this.chosenBenchmark === BENCHMARK_OPTIONS[1]) {
        return undefined;
      }
      if (this.fifthElement === null) {
        return undefined;
      }
      const subcomponent = [];
      for (const [key, value] of this
          .componentMap
          .get(this.probe)
          .get(this.fourthElement)
          .get(this.fifthElement).entries()) {
        subcomponent.push(key);
      }
      return subcomponent;
    }
  },
  watch: {
    //  When the top level benchmark type is changed
    //  all other options are aborted.
    chosenBenchmark() {
      this.firstElement = null;
      this.secondElement = null;
      this.thirdElement = null;
      this.fourthElement = null;
      this.fifthElement = null;
      this.sixthElement = null;
    },

    thirdElement() {
      this.fourthElement = null;
      this.fifthElement = null;
      this.sixthElement = null;
    },

    fourthElement() {
      this.fifthElement = null;
      this.sixthElement = null;
    },

    fifthElement() {
      this.sixthElement = null;
    },

    referenceColumn() {
      if (this.referenceColumn === null) {
        this.testResults = [];
        return;
      }
      this.significanceTester.referenceColumn = this.referenceColumn;
      this.testResults = this.significanceTester.mostSignificant();
    }

  },
  methods: {
    //  Build the available metrics upon the chosen items.
    //  The method applies an intersection for all of them and
    //  return the result as a collection of metrics that matched.
    //  Also the metric that exactly matches the menu selected items
    //  will be the first one in array and the first row in table.
    apply() {
      if (this.chosenBenchmark === null) {
        return undefined;
      }
      let metrics = this.metricNames;
      if (this.chosenBenchmark === BENCHMARK_OPTIONS[0]) {
        if (this.firstElement !== null) {
          metrics = metrics.filter(name => name
              .includes(this.firstElement));
        }
      } else {
        if (this.firstElement !== null) {
          metrics = metrics.filter(name => name
              .startsWith(this.firstElement));
        }
      }
      if (this.secondElement !== null) {
        metrics = metrics.filter(name => name
            .includes(this.secondElement));
      }
      if (this.thirdElement !== null) {
        metrics = metrics.filter(name => name
            .includes(this.thirdElement));
      }
      if (this.fourthElement !== null) {
        metrics = metrics.filter(name => name
            .includes(this.fourthElement));
      }
      if (this.fifthElement !== null) {
        metrics = metrics.filter(name => name
            .includes(this.fifthElement));
      }
      if (this.sixthElement !== null) {
        metrics = metrics.filter(name => name
            .includes(this.sixthElement));
      }
      if (this.probe !== null && this.probe !== undefined) {
        metrics = metrics.filter(name => name
            .includes(this.probe));
      }

      if (_.uniq(metrics).length === 0) {
        alert('No metrics found');
      } else {
        metrics = _.uniq(metrics);
        app.parsedMetrics = metrics;
      }
    },

    /**
     * Splits a memory metric into it's heirarchical data and
     * assigns this heirarchy information into the relavent fields
     * of the menu. It also updates the table to display only the
     * given metric.
     * @param {string} metricName The name of the metric to be split.
     */
    async splitMemoryMetric(metricName) {
      if (!metricName.startsWith('memory')) {
        throw new Error('Expected a memory metric');
      }
      const parts = metricName.split(':');
      const heirarchyInformation = {
        browser: 1,
        process: 2,
        probe: 3,
        componentStart: 4,
        // Metrics have a variable number of subcomponents
        // (.e.g, a metric which is an aggregate over subcomponents will
        // have one less subcomponent field than it's sub-metrics).
        // Therefore, the end of the subcomponents field and
        // location of the size field must be calculated dynamically.
        componentsEnd: parts.length - 2,
        size: parts.length - 1,
      };
      // Assigning to these fields updates the corresponding select
      // menu in the UI.
      this.firstElement = parts[heirarchyInformation.browser];
      this.secondElement = parts[heirarchyInformation.process];
      this.probe = parts[heirarchyInformation.probe];
      this.thirdElement = parts[heirarchyInformation.size];
      // The size watcher sets 'this.component' to null so we must wait for the
      // DOM to be updated. Then the size watcher is called before assigning
      // to 'this.component' and so it is not overwritten with null.
      await this.$nextTick();
      this.fourthElement = parts[heirarchyInformation.componentStart];
      const start = heirarchyInformation.componentStart;
      const end = heirarchyInformation.componentsEnd;
      for (let i = start + 1; i <= end; i++) {
        const subcomponent = i - heirarchyInformation.componentStart;
        switch (subcomponent) {
          case 1: {
            // See above comment (component watcher sets subcomponent to null).
            await this.$nextTick();
            this.fifthElement = parts[i];
            break;
          }
          case 2: {
            // See above comment
            // (subcomponent watcher sets subsubcomponent to null).
            await this.$nextTick();
            this.sixthElement = parts[i];
            break;
          }
          default: throw new Error('Unexpected number of subcomponents.');
        }
      }
      app.parsedMetrics = [metricName];
    },
  }
});

function average(arr) {
  return _.reduce(arr, function(memo, num) {
    return memo + num;
  }, 0) / arr.length;
}

//  This function returns an object containing:
//  all the names of labels plus a map like this:
//  map: [metric_name] -> [map: [lable] -> sampleValue],
//  where the lable is each name of all sub-labels
//  and sampleValue is the average for a specific
//  metric across stories with a specific label.
function getMetricStoriesLabelsToValuesMap(sampleArr, guidValueInfo) {
  const newDiagnostics = new Set();
  const metricToDiagnosticValuesMap = new Map();
  for (const elem of sampleArr) {
    const currentDiagnostic = guidValueInfo.
        get(elem.diagnostics.labels);
    if (currentDiagnostic === undefined) {
      continue;
    }
    newDiagnostics.add(currentDiagnostic);

    if (!metricToDiagnosticValuesMap.has(elem.name)) {
      const map = new Map();
      map.set(currentDiagnostic, [average(elem.sampleValues)]);
      metricToDiagnosticValuesMap.set(elem.name, map);
    } else {
      const map = metricToDiagnosticValuesMap.get(elem.name);
      if (map.has(currentDiagnostic)) {
        const array = map.get(currentDiagnostic);
        array.push(average(elem.sampleValues));
        map.set(currentDiagnostic, array);
        metricToDiagnosticValuesMap.set(elem.name, map);
      } else {
        map.set(currentDiagnostic, [average(elem.sampleValues)]);
        metricToDiagnosticValuesMap.set(elem.name, map);
      }
    }
  }
  return {
    labelNames: Array.from(newDiagnostics),
    mapLabelToValues: metricToDiagnosticValuesMap
  };
}

function fromBytesToMiB(value) {
  return (value / MiB).toFixed(5);
}


//   Load the content of the file and further display the data.
function readSingleFile(e) {
  const file = e.target.files[0];
  if (!file) {
    return;
  }
  //  Extract data from file and distribute it in some relevant structures:
  //  results for all guid-related( for now they are not
  //  divided in 3 parts depending on the type ) and
  //  all results with sample-value-related and
  //  map guid to value within the same structure
  const reader = new FileReader();
  reader.onload = function(e) {
    const contents = extractData(e.target.result);
    const sampleArr = contents.sampleValueArray;
    const guidValueInfo = contents.guidValueInfo;
    const allLabels = new Set();
    for (const e of sampleArr) {
      // This version of the tool focuses on analysing memory
      // metrics, which contain a slightly different structure
      // to the non-memory metrics.
      if (e.name.startsWith('memory')) {
        const { name, sampleValues, diagnostics } = e;
        const { labels, stories } = diagnostics;
        const label = guidValueInfo.get(labels)[0];
        allLabels.add(label);
        const story = guidValueInfo.get(stories)[0];
        menu.significanceTester.add(name, label, story, sampleValues);
      }
    }
    menu.allLabels = Array.from(allLabels);
    let metricNames = [];
    sampleArr.map(e => metricNames.push(e.name));
    metricNames = _.uniq(metricNames);


    //  The content for the default table: with name
    //  of the metric, the average value of the sample values
    //  plus an id. The latest is used to expand the row.
    //  It may disappear later.
    const tableElems = [];
    let id = 1;
    for (const name of metricNames) {
      tableElems.push({
        id: id++,
        metric: name
      });
    }

    const labelsResult = getMetricStoriesLabelsToValuesMap(
        sampleArr, guidValueInfo);
    const columnsForChosenDiagnostic = labelsResult.labelNames;
    const metricToDiagnosticValuesMap = labelsResult.mapLabelToValues;
    for (const elem of tableElems) {
      if (metricToDiagnosticValuesMap.get(elem.metric) === undefined) {
        continue;
      }
      for (const diagnostic of columnsForChosenDiagnostic) {
        if (!metricToDiagnosticValuesMap.get(elem.metric).has(diagnostic)) {
          continue;
        }
        elem[diagnostic] = fromBytesToMiB(average(metricToDiagnosticValuesMap
            .get(elem.metric).get(diagnostic)));
      }
    }

    app.gridData = tableElems;
    app.defaultGridData = tableElems;
    app.sampleArr = sampleArr;
    app.guidValue = guidValueInfo;
    app.columnsForChosenDiagnostic = columnsForChosenDiagnostic;

    const result = parseAllMetrics(metricNames);
    menu.sampelArr = sampleArr;
    menu.guidValueInfo = guidValueInfo;

    menu.browserOptions = result.browsers;
    menu.subprocessOptions = result.subprocesses;
    menu.componentMap = result.components;
    menu.sizeMap = result.sizes;
    menu.metricNames = result.names;

    menu.durationComponents = result.duration;
  };
  reader.readAsText(file);
}

function extractData(contents) {
  /*
   *  Populate guidValue with guidValue objects containing
   *  guid and value from the same type of data.
   */
  const guidValueInfoMap = new Map();
  const result = [];
  const sampleValue = [];
  const dateRangeMap = new Map();
  const other = [];
  /*
   *  Extract every piece of data between <histogram-json> tags;
   *  all data is written between these tags
   */
  const reg = /<histogram-json>(.*?)<\/histogram-json>/g;
  let m = reg.exec(contents);
  while (m !== null) {
    result.push(m[1]);
    m = reg.exec(contents);
  }
  for (const element of result) {
    const e = JSON.parse(element);
    if (e.hasOwnProperty('sampleValues')) {
      const elem = {
        name: e.name,
        sampleValues: e.sampleValues,
        unit: e.unit,
        guid: e.guid,
        diagnostics: {}
      };
      if (e.diagnostics === undefined || e.diagnostics === null) {
        continue;
      }
      if (e.diagnostics.hasOwnProperty('traceUrls')) {
        elem.diagnostics.traceUrls = e.diagnostics.traceUrls;
      }
      if (e.diagnostics.hasOwnProperty('labels')) {
        elem.diagnostics.labels = e.diagnostics.labels;
      } else {
        elem.diagnostics.labels = e.diagnostics.benchmarkStart;
      }
      if (e.diagnostics.hasOwnProperty('stories')) {
        elem.diagnostics.stories = e.diagnostics.stories;
      }
      if (e.diagnostics.hasOwnProperty('storysetRepeats')) {
        elem.diagnostics.storysetRepeats = e.diagnostics.storysetRepeats;
      }
      sampleValue.push(elem);
    } else {
      if (e.type === 'GenericSet') {
        if (typeof e.values !== 'number') {
          //  Here it can be either a number or a string.
          guidValueInfoMap.set(e.guid, e.values[0]);
        } else {
          guidValueInfoMap.set(e.guid, e.values);
        }
      } else if (e.type === 'DateRange') {
        if (typeof e.min !== 'number') {
          // Here it can be either a number or a string.
          guidValueInfoMap.set(e.guid, e.min[0]);
        } else {
          guidValueInfoMap.set(e.guid, e.min);
        }
      } else {
        other.push(e);
      }
    }
  }
  return {
    guidValueInfo: guidValueInfoMap,
    guidMinInfo: dateRangeMap,
    otherTypes: other,
    sampleValueArray: sampleValue
  };
}
document.getElementById('file-input')
    .addEventListener('change', readSingleFile, false);
