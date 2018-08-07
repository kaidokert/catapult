'use strict';
const MiB = 1024 * 1024;
Vue.component('v-select', VueSelect.VueSelect);

//  Vue component for drop-down menu; here the metrics,
//  stories and diagnostics are chosen through selection
const app = new Vue({
  el: '#app',
  data: {
    sampleArr: [],
    guidValue: null,
    selected_metric: null,
    selected_story: null,
    selected_diagnostic: null,
    graph: null
  },

  //  Draw a plot depending on the target value.
  methods: {
    plot() {
      this.graph.xAxis('Data Points')
          .yAxis('Memory used (MiB)')
          .title(this.selected_story)
          .addData(JSON.parse(JSON.stringify((this.target))))
          .plotCumulativeFrequency();
    }
  },

  computed: {
    seen() {
      return this.sampleArr.length > 0 ? true : false;
    },
    //  Compute the metrics; the user will choose one.
    metrics() {
      const metricsNames = [];
      this.sampleArr.forEach(el => metricsNames.push(el.name));
      return _.uniq(metricsNames);
    },

    //  Compute the stories depending on the chosen metric.
    stories() {
      const reqMetrics = this.sampleArr
          .filter(elem => elem.name === this.selected_metric);
      const storiesByGuid = [];
      reqMetrics.map(elem => storiesByGuid
          .push(this.guidValue.get(elem.diagnostics.stories)[0]));
      return Array.from(new Set(storiesByGuid));
    },
    //  Compute all diagnostic elements; the final result will actually
    //  depend on the metric + story and this diagnostic.
    diagnostics() {
      if (this.selected_story !== null && this.selected_metric !== null) {
        const result = this.sampleArr
            .filter(value => value.name === this.selected_metric &&
                    this.guidValue
                        .get(value.diagnostics.stories)[0] ===
                        this.selected_story);
        const allDiagnostic = [];
        result.map(val => allDiagnostic.push(Object.keys(val.diagnostics)));
        return _.union.apply(this, allDiagnostic);
      }
    },

    //  Compute the final result: metric + story + diagnostic;
    //  the format for a specific diagnostic is:
    //  {key: diagnosticItem; value: sampleValues};
    //  For each (story + metric) item with the same diagnostic
    //  value will be collected all sample values.

    target() {
      if (this.selected_story !== null &&
        this.selected_metric !== null &&
        this.selected_diagnostic !== null) {
        const result = this.sampleArr
            .filter(value => value.name === this.selected_metric &&
                    this.guidValue
                        .get(value.diagnostics.stories)[0] ===
                        this.selected_story);

        const content = new Map();

        for (const val of result) {
          const storyEl = this.guidValue.get(
              val.diagnostics[this.selected_diagnostic]);
          if (storyEl === undefined) {
            continue;
          }
          let storyItem = '';
          if (typeof storyEl === 'number') {
            storyItem = storyEl;
          } else {
            storyItem = storyEl[0];
          }
          if (content.has(storyItem)) {
            const aux = content.get(storyItem);
            content.set(storyItem, aux.concat(val.sampleValues));
          } else {
            content.set(storyItem, val.sampleValues);
          }
        }

        //  Just for displaying data; will be removed.
        //  It's not possible to manipulate a map in origin format.
        const contentKeys = [];
        const contentVal = [];
        for (const [key, value] of content.entries()) {
          value.map(value => +((value / MiB).toFixed(5)));
          contentKeys.push(key);
          contentVal.push(value);
        }
        const obj = _.object(contentKeys, contentVal);
        return obj;
      }
      return undefined;
    }
  },
  watch: {
    //  Whenever a new metric/story/diagnostic is chosen
    //  this fucntion will run for drawing a new type of plot.
    target() {
      if (this.graph === null) {
        this.graph = new GraphData();
        this.plot();
      } else {
        this.graph.plotter_.remove();
        this.graph = new GraphData();
        this.plot();
      }
    }
  }
});

//  Register a new component for displaying data
//  in a table.
Vue.component('data-table', {
  template: '#table-template',
  props: {
    data: Array,
    columns: Array,
    filterKey: String
  },
  data() {
    const sort = {};
    this.columns.forEach(function(key) {
      sort[key] = 1;
    });
    return {
      sortKey: '',
      sortOrders: sort
    };
  },
  computed: {
    filteredData() {
      const sortKey = this.sortKey;
      const filterKey = this.filterKey && this.filterKey.toLowerCase();
      const order = this.sortOrders[sortKey] || 1;
      let data = this.data;
      if (filterKey) {
        data = data.filter(function(row) {
          return Object.keys(row).some(function(key) {
            return String(row[key]).toLowerCase().indexOf(filterKey) > -1;
          });
        });
      }
      if (sortKey) {
        data = data.slice().sort(function(a, b) {
          a = a[sortKey];
          b = b[sortKey];
          if (a === b) {
            return 0;
          }
          if (a > b) {
            return 1 * ord;
          }
          return -1 * ord;
        });
      }
      return data;
    }
  },
  filters: {
    capitalize(str) {
      return str.charAt(0).toUpperCase() + str.slice(1);
    }
  },
  methods: {
    sortBy(key) {
      this.sortKey = key;
      this.sortOrders[key] = this.sortOrders[key] * -1;
    }
  }
});

const display_ = new Vue({
  el: '#table',
  data: {
    searchQuery: '',
    gridColumns: ['metric', 'story', 'sampleValues'],
    gridData: []
  },
  computed: {
    seen() {
      return this.gridData.length > 0 ? true : false;
    }
  }
});

class element {
  constructor(metric, story, sampleValues) {
    this.metric = metric;
    this.story = story;
    this.sampleValues = sampleValues;
  }
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

    const tableElems = [];
    sampleArr.map(val => tableElems.push(
        new element(val.name, guidValueInfo.get(
            val.diagnostics.stories
        )[0],
        val.sampleValues)
    ));
    display_.gridData = tableElems;
    app.sampleArr = sampleArr;
    app.guidValue = guidValueInfo;
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
  // for (const [key, value] of guidValueInfoMap.entries()) {
  //   console.log(`${key} ${value}`);
  // }
  // console.log(other);
  return {
    guidValueInfo: guidValueInfoMap,
    guidMinInfo: dateRangeMap,
    otherTypes: other,
    sampleValueArray: sampleValue
  };
}

function createCell(content, row) {
  const cell = document.createElement('td');
  const cellText = document.createTextNode(content);
  cell.appendChild(cellText);
  row.appendChild(cell);
}

function displayContents(sampleArr, guidValueInfo, fieldFilter) {
  // get the reference by the Id
  const body = document.getElementById('sample-values');
  // creates a <table> element and a <tbody> element
  const tbl = document.createElement('table');
  const tblBody = document.createElement('tbody');

  //  just to check if this block is meant for
  //  a specific action: the one after the text boxes were filled
  if (fieldFilter === undefined) {
    // creating all cells for titles for heanding
    const r = document.createElement('tr');
    createCell('Name', r);
    createCell('Sample Values', r);
    createCell('Stories', r);
    createCell('StoryTags', r);
    createCell('StorySetRepeats', r);
    createCell('TraceStart', r);
    createCell('TraceUrls', r);
    tblBody.appendChild(r);

    for (const e of sampleArr) {
      // creates a table row
      const row = document.createElement('tr');
      createCell(`${e.name}`, row);
      createCell(`${e.sampleValues}`, row);
      createCell(`${e.diagnostics.stories}`, row);
      createCell(`${e.diagnostics.storyTags}`, row);
      createCell(`${e.diagnostics.storysetRepeats}`, row);
      createCell(`${e.diagnostics.traceStart}`, row);
      createCell(`${e.diagnostics.traceUrls}`, row);
      tblBody.appendChild(row);
    }

    // put the <tbody> in the <table>
    tbl.appendChild(tblBody);
    // appends <table> into <body>
    body.appendChild(tbl);
    // sets the border attribute of tbl to 1;
    tbl.setAttribute('border', '1');
  } else {
  //  this array contains:
  // mathchedSampleValueGuid objects which contains values from
  // SampleArr and the coresponding value from guidValueInfo map
  // depending on this: guid == field
    const r = document.createElement('tr');
    createCell('Name', r);
    createCell('Sample Value', r);
    createCell(`${fieldFilter}`, r);
    createCell(`Matched value for ${fieldFilter}`, r);
    tblBody.appendChild(r);

    for (const e of sampleArr) {
    // creates a table row
      const row = document.createElement('tr');
      // Create a <td> element and a text node, make the text
      // node the contents of the <td>, and put the <td> at
      // the end of the table row
      createCell(`${e.name}`, row);
      createCell(`${e.sampleValues}`, row);
      createCell(`${e.diagnostics[fieldFilter]}`, row);
      createCell(`${guidValueInfo.get(e.diagnostics[fieldFilter])}`, row);
      // add the row to the end of the table body
      tblBody.appendChild(row);
    }
    // put the <tbody> in the <table>
    tbl.appendChild(tblBody);
    // appends <table> into <body>
    body.replaceChild(tbl, body.childNodes[0]);
    // sets the border attribute of tbl to 1;
    tbl.setAttribute('border', '1');
  }
}
document.getElementById('file-input')
    .addEventListener('change', readSingleFile, false);
