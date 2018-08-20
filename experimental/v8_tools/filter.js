'use strict';
const MiB = 1024 * 1024;
Vue.component('v-select', VueSelect.VueSelect);

const menu = new Vue({
  el: '#menu',
  data: {
    sampleArr: null,
    guidValueInfo: null,

    browser: null,
    subprocess: null,
    probe: null,
    component: null,
    size: null,
    metricNames: null,

    browserOptions: [],
    subprocessOptions: [],
    probeOptions: [],

    componentObject: null,
    sizeObject: null,

    subcomponent: null,
    subcomponent_: null,


  },

  computed: {
    //  Compute size options depending on the type of probe.
    sizeOptions() {
      if (this.sizeObject !== null) {
        if (this.probe === 'reported_by_chrome') {
          return this.sizeObject.sizeChrome;
        }
        return this.sizeObject.sizeOs;
      }
      return undefined;
    },
    //  The components are different depending on the type of probe.
    componentOptions() {
      if (this.componentObject !== null) {
        if (this.probe === 'reported_by_chrome') {
          const component = [];
          for (const [key, value] of this.componentObject
              .componentByChrome.entries()) {
            component.push(key);
          }
          return component;
        }
        const component = [];
        for (const [key, value] of this.componentObject
            .componentByOs.entries()) {
          component.push(key);
        }
        return component;
      }
      return undefined;
    },

    //  Compute the options for the first subcomponent depending on the probes.
    //  When the user chooses a component, it might be a hierarchical one.
    firstSubcompOptions() {
      if (this.component !== null) {
        if (this.probe === 'reported_by_chrome') {
          if (this.componentObject.componentByChrome.
              get(this.component) !== undefined) {
            const map = this.componentObject
                .componentByChrome.get(this.component);
            const array = [];
            for (const [key, value] of map.entries()) {
              array.push(key);
            }
            return array;
          }
          return undefined;
        }
        return this.componentObject.componentByOs.get(this.component);
      }
      return undefined;
    },

    //  In case when the component is from Chrome, the hierarchy might have more
    //  levels.
    secondSubcompOptions() {
      if (this.probe === 'reported_by_chrome' && this.subcomponent !== null) {
        const map = this.componentObject.componentByChrome.get(this.component);
        return map.get(this.subcomponent);
      }
      return undefined;
    },

    seen() {
      return this.component !== null;
    },
    seen_() {
      return this.subcomponent !== null;
    }
  },
  watch: {
    probe() {
      this.component = null;
      this.subcomponent = null;
      this.subcomponent_ = null;
      this.size = null;
    },

    component() {
      this.subcomponent = null;
      this.subcomponent_ = null;
    },

    subcomponent() {
      this.subcomponent_ = null;
    },

  },
  methods: {
    //  Build the available metrics upon the chosen items.
    //  The method applies an intersection for all of them and
    //  return the result as a collection of metrics that matched.
    apply() {
      const metrics = [];
      for (const name of this.metricNames) {
        if (this.browser !== null && name.includes(this.browser) &&
          this.subprocess !== null && name.includes(this.subprocess) &&
          this.component !== null && name.includes(this.component) &&
          this.size !== null && name.includes(this.size) &&
          this.probe !== null && name.includes(this.probe)) {
          if (this.subcomponent === null) {
            metrics.push(name);
          } else {
            if (name.includes(this.subcomponent)) {
              if (this.subcomponent_ === null) {
                metrics.push(name);
              } else {
                if (name.includes(this.subcomponent_)) {
                  metrics.push(name);
                }
              }
            }
          }
        }
      }
      if (_.uniq(metrics).length === 0) {
        alert('No metrics found');
      } else {
        alert('You can pick a metric from drop-down');
        app.parsedMetrics = _.uniq(metrics);
      }
    }
  }
});

//  A row from the default table.
class TableRow {
  constructor(id, metric, averageSampleValues) {
    this.id = id;
    this.metric = metric;
    this.averageSampleValues = averageSampleValues;
  }
}

//  A row after expanding a specific metric. This includes
//  all the stories from that metric plus the sample values
//  in the initial form, not the average.
class StoryRow {
  constructor(story, sample) {
    this.story = story;
    this.sample = sample;
  }
}

function average(arr) {
  return _.reduce(arr, function(memo, num) {
    return memo + num;
  }, 0) / arr.length;
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
    const metricAverage = new Map();
    for (const e of sampleArr) {
      if (metricAverage.has(e.name)) {
        const aux = metricAverage.get(e.name);
        aux.push(average(e.sampleValues));
        metricAverage.set(e.name, aux);
      } else {
        metricAverage.set(e.name, [average(e.sampleValues)]);
      }
    }

    //  The content for the default table: with name
    //  of the mtric, the average value of the sample values
    //  plus an id. The latest is used to expand the row.
    // It may disappear later.
    const tableElems = [];
    let id = 1;
    for (const [key, value] of metricAverage.entries()) {
      tableElems.push(
          new TableRow(id++, key, average(value))
      );
    }
    app.gridData = tableElems;
    app.sampleArr = sampleArr;
    app.guidValue = guidValueInfo;

    let metricNames = [];
    sampleArr.map(e => metricNames.push(e.name));
    metricNames = _.uniq(metricNames);

    const result = parseAllMetrics(metricNames);
    menu.sampelArr = sampleArr;
    menu.guidValueInfo = guidValueInfo;

    menu.browserOptions = result.browsers;
    menu.subprocessOptions = result.subprocesses;
    menu.probeOptions = result.probes;

    menu.componentObject = result.components;
    menu.sizeObject = result.sizes;

    menu.metricNames = result.names;
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
      sampleValue.push(e);
    } else {
      if (e.type === 'GenericSet') {
        guidValueInfoMap.set(e.guid, e.values);
      } else if (e.type === 'DateRange') {
        guidValueInfoMap.set(e.guid, e.min);
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
