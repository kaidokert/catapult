'use strict';

Vue.component('v-select', VueSelect.VueSelect);
const selectComponent = new Vue({
  el: '#app',
  data: {
    sampleArr: [],
    guidValue: null,
    selected_metric: null,
    selected_story: null,
    selected_diagnostic: null,
  },
  computed: {
    seen: {
      get() { return this.sampleArr.length > 0 ? true : false; },
      set() {}
    },
    //  compute the metrics; the user will choose one
    metrics() {
      const metricsNames = new Set();
      this.sampleArr.forEach(el => metricsNames.add(el.name));
      return Array.from(metricsNames);
    },

    //  compute the stories depending on the chosen metric
    stories() {
      const reqMetrics = this.sampleArr
          .filter(elem => elem.name === this.selected_metric);
      const storiesByGuid = [];
      reqMetrics.map(elem => storiesByGuid
          .push(this.guidValue.get(elem.diagnostics.stories)[0]));
      return Array.from(new Set(storiesByGuid));
    },
    //  compute all diagnostic elements; the final result will actually
    //  depend on the metric + story and this diagnostic;
    diagnostics() {
      if (this.selected_story !== null && this.selected_metric !== null) {
        const result = this.sampleArr
            .filter(value => value.name === this.selected_metric &&
                    this.guidValue
                        .get(value.diagnostics.stories)[0] ===
                        this.selected_story);
        const allDiagnostic = [];
        result.map(val => allDiagnostic.push(Object.keys(val.diagnostics)));
        return _.intersection.apply(this, allDiagnostic);
      }
    },
    //  compute the final result: metric + story + diagnostic
    //  the format for a specific diagnostic is:
    //  {key: diagnosticItem; value: sampleValues};
    //  for each (story + metric) item with the same diagnostic
    //  values -> all sampleValues will be collected
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
          const storyItem = this.guidValue.get(
              val.diagnostics[this.selected_diagnostic])[0];
          if (content.has(storyItem)) {
            const aux = content.get(storyItem);
            aux.concat(val.sampleValues);
            content.set(storyItem, aux);
          } else {
            content.set(storyItem, val.sampleValues);
          }
        }
        //  just for displaying data; will be removed
        //  it's not possible to manipulate a map in origin format
        const contentDisplay = [];
        for (const [key, value] of content.entries()) {
          const elem = { keyItem: key, valueItem: value };
          contentDisplay.push(elem);
        }
        return contentDisplay;
      }
    }
  }
});

//  just to make sure the user doesn't press any button before having
//  any relevant information
function visibleAll() {
  document.getElementById('storyBtn').style.visibility = 'visible';
  document.getElementById('storyTagsBtn').style.visibility = 'visible';
  document.getElementById('storysetRepeatsBtn').style.visibility = 'visible';
  document.getElementById('traceStartBtn').style.visibility = 'visible';
  document.getElementById('traceUrlsBtn').style.visibility = 'visible';
  document.getElementById('metricname').style.visibility = 'visible';
  document.getElementById('storyname').style.visibility = 'visible';
  document.getElementById('submit').style.visibility = 'visible';
  selectComponent.seen = true;
}
//  load the content of the file and further display the data
function readSingleFile(e) {
  const file = e.target.files[0];
  if (!file) {
    return;
  }
  const reader = new FileReader();
  reader.onload = function(e) {
    //  extract data from file and distribute it in some relevant structures
    const contents = extractData(e.target.result);
    // results for all guid-related; for now they are not
    // divided in 3 parts depending on the type
    // all results with sample-value-related
    const sampleArr = contents.sampleValueArray;
    //  map guid to value within the same structure
    const guidValueInfo = contents.guidValueInfo;

    //  the select-menu will use just this two structures
    selectComponent.sampleArr = sampleArr;
    selectComponent.guidValue = guidValueInfo;


    //  data is displayed in a default format
    displayContents(sampleArr, guidValueInfo);
    visibleAll();


    //  every button should be able to filter the information regarding
    //  one of the possibilities of choosing
    document.getElementById('storyBtn')
        .addEventListener('click', function() {
          displayContents(sampleArr, guidValueInfo, 'stories');
        }, false);
    document.getElementById('storyTagsBtn')
        .addEventListener('click', function() {
          displayContents(sampleArr, guidValueInfo, 'storyTags');
        }, false);
    document.getElementById('storysetRepeatsBtn')
        .addEventListener('click', function() {
          displayContents(sampleArr, guidValueInfo, 'storysetRepeats');
        }, false);
    document.getElementById('traceStartBtn')
        .addEventListener('click', function() {
          displayContents(sampleArr, guidValueInfo, 'traceStart');
        }, false);
    document.getElementById('traceUrlsBtn')
        .addEventListener('click', function() {
          displayContents(sampleArr, guidValueInfo, 'traceUrls');
        }, false);
  };
  reader.readAsText(file);
}
// extract all data and divide it in sampleValues related
// and guid related (later I'll may divide this in 3 parts
// depending on the type of guid )
function extractData(contents) {
  // populate guidValue with guidValue objects containing
  // guid and value from the same type of data
  const guidValueInfoMap = new Map();
  const result = [];
  const sampleValue = [];
  //  workaround for later
  const dateRangeMap = new Map();
  const other = [];
  //  extract every piece of data between <histogram-json> tags;
  //  all data is written between these tags
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
        dateRangeMap.set(e.guid, e.min);
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
//  create a single cell with data in the table
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
