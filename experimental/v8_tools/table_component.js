'use strict';
//  Register the table component for displaying data.
//  This is a child for the app Vue instance, so it might
//  access some of the app's fields.
Vue.component('data-table', {
  template: '#table-template',
  props: {
    data: Array,
    columns: Array,
    filterKey: String,
    additional: Array,
    plot: String
  },
  mounted() {
    // TODO(anthonyalridge): Should also update table state.
    // TODO(anthonyalridge): Create route back to bar plots.
    const jumpToStory = (story) => {
      // TODO(anthonyalridge): This should be a field on one of the vue
      // components (or may not in fact be needed at all)
      // once the row based diagnostic selection is removed.
      const activeDiagnostic = 'labels';
      this.markedTableStories = [story];
      this.setCheckBoxes(false, 'checkbox-story');
      app.plotSingleMetric(
          this.markedTableMetrics[0],
          story,
          activeDiagnostic,
          this.markedTableDiagnostics,
          'Cumulative frequency plot');
    };
    app.$on('bar_clicked', jumpToStory);
  },
  data() {
    const sort = {};
    this.columns.forEach(function(key) {
      sort[key] = 1;
    });
    return {
      sortKey: '',
      sortOrders: sort,
      openedMetric: [],
      openedStory: [],
      storiesEntries: null,
      metric: null,
      story: null,
      diagnostic: 'storysetRepeats',
      selected_diagnostics: [],
      markedTableMetrics: [],
      markedTableStories: [],
      markedTableDiagnostics: []
    };
  },
  computed: {
    //  Filter data from one column.
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
          return (a === b ? 0 : a > b ? 1 : -1) * order;
        });
      }
      return data;
    },

    //  All storySetRepeats must be visible just after the user
    //  has already chosen a specific diagnostic and all the
    //  options for that one are now available.
    seen_diagnostics() {
      return this.diagnostics_options.length > 0 ? true : false;
    },

    //  Compute all the options for the main diagnostic.
    //  Depending on the GUID of that diagnostic, the value can be
    //  a string, a number or undefined.
    diagnostics_options() {
      if (this.story === null ||
      this.metric === null ||
      this.diagnostic === null) {
        return undefined;
      }
      const sampleArr = this.$parent.sampleArr;
      const guidValue = this.$parent.guidValue;
      const result = sampleArr
          .filter(value => value.name === this.metric.metric &&
                  guidValue
                      .get(value.diagnostics.stories) ===
                      this.story.story);
      const content = [];
      for (const val of result) {
        let diagnosticItem = guidValue.get(
            val.diagnostics[this.diagnostic]);
        if (diagnosticItem === undefined) {
          continue;
        }
        if (typeof diagnosticItem === 'number') {
          diagnosticItem = diagnosticItem.toString();
        }
        content.push(diagnosticItem);
      }
      return _.uniq(content);
    }
  },

  //  Capitalize the objects field names.
  filters: {
    capitalize(str) {
      if (str === undefined) {
        return undefined;
      }
      if (typeof str === 'number') {
        return str.toString();
      }
      return str.charAt(0).toUpperCase() + str.slice(1);
    }
  },

  methods: {

    setCheckBoxes(booleanValue, className) {
      const checkboxes = document.getElementsByClassName(className);
      Array.prototype.map.call(checkboxes, function(checkbox) {
        checkbox.checked = booleanValue;
      });
      if (className === 'checkbox-head' && booleanValue === false) {
        this.markedTableDiagnostics = [];
      }
    },
    //  Sort by key where the key is a title head in table.
    sortBy(key) {
      this.sortKey = key;
      this.sortOrders[key] = this.sortOrders[key] * -1;
    },

    //  Remove all the selected items from the array.
    //  Especially for the cases when the user changes the mind and select
    //  another high level diagnostic and the selected sub-diagnostics
    //  will not be usefull anymore.
    empty() {
      this.selected_diagnostics = [];
    },

    //  Compute all the sample values depending on a single
    //  metric for each stories and for multiple sub-diagnostics.
    getSampleByStoryBySubdiagnostics(name, sampleArr, guidValue, globalDiag) {
      const diagValues = new Map();
      for (const e of sampleArr) {
        if (e.name !== name) {
          continue;
        }
        const nameOfStory = guidValue.get(e.diagnostics.stories);
        if (nameOfStory === undefined) {
          continue;
        }
        const diagnostic = guidValue.
            get(e.diagnostics[globalDiag]);
        if (diagnostic === undefined) {
          continue;
        }
        if (!diagValues.has(nameOfStory)) {
          const map = new Map();
          map.set(diagnostic, [average(e.sampleValues)]);
          diagValues.set(nameOfStory, map);
        } else {
          const map = diagValues.get(nameOfStory);
          if (!map.has(diagnostic)) {
            map.set(diagnostic, [average(e.sampleValues)]);
            diagValues.set(nameOfStory, map);
          } else {
            const array = map.get(diagnostic);
            array.push(average(e.sampleValues));
            map.set(diagnostic, array);
            diagValues.set(nameOfStory, map);
          }
        }
      }
      return diagValues;
    },

    getStoriesByMetric(entry, sampleArr, guidValue) {
      const stories = [];
      for (const e of sampleArr) {
        if (e.name !== entry) {
          continue;
        }
        const nameOfStory = guidValue.get(e.diagnostics.stories);
        if (nameOfStory === undefined) {
          continue;
        }
        stories.push(nameOfStory);
      }
      return _.uniq(stories);
    },

    //  This method will be called when the user clicks a specific
    //  'row in table' = 'metric' and we have to provide the stories for that.
    //  Also all the previous choices must be removed.
    toggleMetric(entry) {
      const index = this.openedMetric.indexOf(entry.id);
      if (index > -1) {
        this.openedMetric.splice(index, 1);
      } else {
        this.openedMetric.push(entry.id);
      }
      const sampleArr = this.$parent.sampleArr;
      const guidValue = this.$parent.guidValue;
      const addCol = this.$parent.columnsForChosenDiagnostic;
      const storiesEntries = [];

      const stories = this
          .getStoriesByMetric(entry.metric, sampleArr, guidValue);
      for (const key of stories) {
        storiesEntries.push({
          story: key
        });
      }
      if (addCol !== null) {
        const diagValues = this
            .getSampleByStoryBySubdiagnostics(entry.metric,
                sampleArr, guidValue, 'labels');
        for (const e of storiesEntries) {
          for (const diag of addCol) {
            e[diag] = fromBytesToMiB(average(diagValues
                .get(e.story).get(diag)));
          }
        }
      }
      this.setCheckBoxes(true, 'checkbox-head');
      this.storiesEntries = storiesEntries;
      this.metric = entry;
      this.empty();
      this.markedTableDiagnostics = this.$parent.columnsForChosenDiagnostic;
      this.markedTableStories = this
          .getStoriesByMetric(entry.metric, sampleArr, guidValue);
    },

    //  This method will be called when the user clicks a specific
    //  story row and we have to compute all the available diagnostics.
    //  Also all the previous choices regarding a diagnostic must be removed.
    toggleStory(story) {
      const index = this.openedStory.indexOf(story.story);
      if (index > -1) {
        this.openedStory.splice(index, 1);
      } else {
        this.openedStory.push(story.story);
      }
      const sampleArr = this.$parent.sampleArr;
      const guidValue = this.$parent.guidValue;
      const result = sampleArr
          .filter(value => value.name === this.metric.metric &&
              guidValue
                  .get(value.diagnostics.stories) ===
                  story.story);
      const allDiagnostic = [];
      result.map(val => allDiagnostic.push(Object.keys(val.diagnostics)));
      this.story = story;
      app.plotSingleMetricWithAllSubdiagnostics(this.metric.metric,
          this.story.story, this.diagnostic);
      this.empty();
      this.setCheckBoxes(false, 'checkbox-head');
    },

    createPlot() {
      let plot = 'Cumulative frequency plot';
      if (this.plot !== undefined && this.plot !== null) {
        plot = this.plot;
      }
      let story = this.story;
      if (this.markedTableStories.length === 1) {
        story = this.markedTableStories[0];
      } else {
        story = story.story;
      }
      let diagnostic = this.diagnostic;
      let diagnostics = [];
      if (this.markedTableDiagnostics.length !== 0) {
        diagnostic = 'labels';
        diagnostics = this.markedTableDiagnostics;
      } else if (this.selected_diagnostics.length !== 0) {
        diagnostics = this.selected_diagnostics;
      } else {
        diagnostics = this.diagnostics_options;
      }
      app.plotSingleMetric(this
          .metric.metric,
      story,
      diagnostic,
      diagnostics,
      plot);
    },

    //  When the user pick a new metric for further analysis
    //  this one has to be stored. If this is already stored
    //  this means that the action is the reverse one: unpick.
    pickTableMetric(entry) {
      if (this.markedTableMetrics.includes(entry.metric)) {
        this.markedTableMetrics.splice(
            this.markedTableMetrics.indexOf(entry.metric), 1);
      } else {
        this.markedTableMetrics.push(entry.metric);
      }
    },

    //  Whenever the user pick a new metric for further analysis
    //  this one has to be stored. If it is already stored,
    //  this means that the user actually unpicked it.
    pickTableStory(entry) {
      if (this.markedTableStories.includes(entry.story)) {
        this.markedTableStories.splice(
            this.markedTableStories.indexOf(entry.story), 1);
      } else {
        this.markedTableStories.push(entry.story);
      }
    },

    //  The same for pickTableMetric and pickTableStory.
    pickHeadTable(title) {
      if (this.markedTableDiagnostics.includes(title)) {
        this.markedTableDiagnostics.splice(
            this.markedTableDiagnostics.indexOf(title), 1);
      } else {
        this.markedTableDiagnostics.push(title);
      }
      this.selected_diagnostics = [];
    },

    getDataForBarChart(sampleArr, guidValue, diagnostics, stories, metric) {
      const map = this
          .getSampleByStoryBySubdiagnostics(metric,
              sampleArr, guidValue, 'labels');
      const data = {};
      for (const e of diagnostics) {
        const obj = {};
        for (const story of stories) {
          obj[story] = map.get(story).get(e);
        }
        data[e] = obj;
      }
      return data;
    },

    //  Draw a bar chart when multiple stories are selected
    //  from a single metric and multiple sub-diagnostics are
    //  selected from a a single main diagnostic.
    plotMultipleStoriesMultipleDiag() {
      if (this.markedTableDiagnostics.length !== 0) {
        const sampleArr = this.$parent.sampleArr;
        const guidValue = this.$parent.guidValue;
        const data = this
            .getDataForBarChart(sampleArr, guidValue,
                this.markedTableDiagnostics,
                this.markedTableStories, this.metric.metric);
        app.plotBarChart(data);
      }
    },

    //  When the user selects a specific row from the table
    //  this does not mean that it is the only one metric
    //  with that name, so we have to extract all available
    //  metrics from sampleValues.
    getAllMetricsFromMetricRow() {
      const sampleArr = this.$parent.sampleArr;
      const markedMetrics = [];
      for (const metric of sampleArr) {
        for (const e of this.markedTableMetrics) {
          if (metric.name === e) {
            markedMetrics.push(metric);
          }
        }
      }
      return markedMetrics;
    },

    //  The metrics from grid are the ones that come
    //  after selecting items from tree-menu.
    //  We need to filter just that metrics from the total
    //  sampleValues metrics.
    getMetricsFromGrid() {
      const sampleArr = this.$parent.sampleArr;
      const gridData = this.$parent.gridData;
      const metricsDependingOnGrid = [];
      for (const metric of sampleArr) {
        for (const e of gridData) {
          if (metric.name === e.metric) {
            metricsDependingOnGrid.push(metric);
          }
        }
      }
      return metricsDependingOnGrid;
    }
  },

  watch: {
    //  Whenever a new diagnostic is chosen or removed, the graph
    //  is replotted because these are displayed in the same plot
    //  by comparison and it should be updated.
    selected_diagnostics() {
      if (this.selected_diagnostics.length !== 0) {
        this.setCheckBoxes(false, 'checkbox-head');
        this.createPlot();
      }
    },

    //  Whenever the chosen plot is changed by the user it has to
    //  be created another type of plot with the same specifications.
    plot() {
      if (this.plot === 'Cumulative frequency plot' ||
        this.plot === 'Dot plot') {
        this.createPlot();
      }
    },

    //  Whenever the top level diagnostic is changed all the previous
    //  selected sub-diagnostics have to be removed. Otherwise the old
    //  selections will be displayed. Also the plot is displayed with
    //  values for all available sub-diagnostics.
    diagnostic() {
      this.empty();
      app.plotSingleMetricWithAllSubdiagnostics(this.metric.metric,
          this.story.story, this.diagnostic);
    },

    //  Whenever a new subdiagnostic from table columns is chosen
    //  it is added to the chart. Depending on the main diagnostic
    //  and its subdiagnostics, all the sample values for a particular
    //  metric, multiple stories, a single main diagnostic and multiple
    //  subdiagnostics are computed. The plot is drawn using this data.
    markedTableDiagnostics() {
      if (this.markedTableDiagnostics.length === 0) {
        return undefined;
      }
      const sampleArr = this.$parent.sampleArr;
      const guidValue = this.$parent.guidValue;
      const multipleMetrics = this.markedTableMetrics.length > 1;
      const multipleStories = this.markedTableStories.length > 1;
      let metric = '';
      if (this.markedTableMetrics.length === 0) {
        metric = this.metric.metric;
      } else {
        metric = this.markedTableMetrics[0];
      }

      let stories = '';
      if (this.markedTableStories.length === 0) {
        stories = this.getStoriesByMetric(app
            .gridData[0].metric, sampleArr, guidValue);
      } else {
        stories = this.markedTableStories;
      }

      if (multipleMetrics) {
        const markedMetrics = this.getAllMetricsFromMetricRow();
        const obj = app.computeDataForStackPlot(markedMetrics,
            stories, this.markedTableDiagnostics);
        const string = 'Stacked plot';
        app.plotStackBar(obj, string);
      } else if (multipleStories) {
        const data = this
            .getDataForBarChart(sampleArr, guidValue,
                this
                    .markedTableDiagnostics, stories, metric);
        app.plotBarChart(data);
      } else {
        app.plotSingleMetric(metric,
            story, 'labels',
            this.markedTableDiagnostics,
            'Cumulative frequency plot');
      }
    },

    //  Whenever a new story from table is chosen it has to be added
    //  in the final chart. The chart that should be updated might be
    //  a stacked chart or a bar chart in this particular case.
    markedTableStories() {
      const sampleArr = this.$parent.sampleArr;
      const guidValue = this.$parent.guidValue;

      const multipleMetrics = this.markedTableMetrics.length > 1;
      const multipleStories = this.markedTableStories.length > 1;

      let labelsName = this.markedTableDiagnostics;
      if (this.markedTableDiagnostics.length === 0) {
        labelsName = this.$parent.columnsForChosenDiagnostic;
      }

      let metric = '';
      if (this.markedTableMetrics.length === 0) {
        metric = this.metric.metric;
      } else {
        metric = this.markedTableMetrics[0];
      }

      const stories = this.markedTableStories;

      if (multipleMetrics) {
        const markedMetrics = this.getAllMetricsFromMetricRow();
        const obj = app.computeDataForStackPlot(markedMetrics,
            this.markedTableStories, labelsName);
        const string = 'Stacked plot';
        app.plotStackBar(obj, string);
      } else if (multipleStories) {
        const data = this.
            getDataForBarChart(sampleArr, guidValue, labelsName,
                stories, metric);
        app.plotBarChart(data);
      } else {
        app.plotSingleMetric(metric,
            stories[0], 'labels',
            this.markedTableDiagnostics,
            'Cumulative frequency plot');
      }
    },

    //  Whenever a new metric is selected the stacked chart should
    //  be updated.
    markedTableMetrics() {
      const sampleArr = this.$parent.sampleArr;
      const guidValue = this.$parent.guidValue;
      //  As sources for final objet:
      //  1) the metrics are taken from sampleValues; these
      //  should have the same same as the selected row;
      const markedMetrics = this.getAllMetricsFromMetricRow();
      //  2) the stories are the ones from the top level metric
      //  or the ones already selected;
      let stories = this.markedTableStories;
      if (this.markedTableStories.length === 0) {
        stories = this.getStoriesByMetric(app
            .gridData[0].metric, sampleArr, guidValue);
      }
      //  3) the labels are all the available labels
      //  or the ones already selected;
      let labelsName = this.markedTableDiagnostics;
      if (this.markedTableDiagnostics.length === 0) {
        labelsName = this.$parent.columnsForChosenDiagnostic;
      }

      const multipleMetrics = this.markedTableMetrics.length > 1;

      if (multipleMetrics) {
        //  For multiple metrics we need a Stacked Plot.
        const obj = app.computeDataForStackPlot(markedMetrics,
            stories, labelsName);
        const string = 'Stacked plot';
        app.plotStackBar(obj, string);
      } else {
        //  For single metric we need a bar chart.
        const data = this.
            getDataForBarChart(sampleArr, guidValue, labelsName, stories,
                this.markedTableMetrics[0]);
        app.plotBarChart(data);
        this.markedTableStories = this
            .getStoriesByMetric(this
                .markedTableMetrics[0], sampleArr, guidValue);
      }
    }
  }
});
