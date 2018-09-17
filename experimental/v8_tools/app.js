//  Vue component for drop-down menu; here the metrics,
//  stories and diagnostics are chosen through selection.
'use strict';
const app = new Vue({
  el: '#app',
  data: {
    state: {
      parsedMetrics: [],
      gridData: [],
      typesOfPlot: [],
      chosenTypeOfPlot: null,
      searchQuery: '',
      history: false,
    },
    sampleArr: [],
    guidValue: null,
    graph: new GraphData(),
    gridColumns: ['metric'],
    columnsForChosenDiagnostic: null,
    resetDropDownMenu: false,
    defaultGridData: [],
    stateManager: new StateManager(),
  },

  methods: {
    //  Reset the table content by returning to the
    //  previous default way with all the components
    //  available.
    resetTableData() {
      this.state.gridData = this.defaultGridData;
    },

    //  Get all stories for a specific metric.
    getStoriesByMetric(entry) {
      const stories = [];
      for (const e of this.sampleArr) {
        if (e.name !== entry) {
          continue;
        }
        let nameOfStory = this.guidValue.get(e.diagnostics.stories);
        if (nameOfStory === undefined) {
          continue;
        }
        if (typeof nameOfStory !== 'number') {
          nameOfStory = nameOfStory[0];
        }
        stories.push(nameOfStory);
      }
      return _.uniq(stories);
    },

    getDiagnostic(elem) {
      let currentDiagnostic = this.guidValue.
          get(elem.diagnostics.labels);
      if (currentDiagnostic === undefined) {
        return undefined;
      }
      if (currentDiagnostic !== 'number') {
        currentDiagnostic = currentDiagnostic[0];
      }
      return currentDiagnostic;
    },

    getStory(elem) {
      let nameOfStory = this.guidValue.
          get(elem.diagnostics.stories);
      if (nameOfStory === undefined) {
        return undefined;
      }
      if (typeof nameOfStory !== 'number') {
        nameOfStory = nameOfStory[0];
      }
      return nameOfStory;
    },

    //  This method creates an object for multiple metrics,
    //  multiple stories and some diagnostics:
    //  {labelName: {storyName: { metricName: sampleValuesArray}}}
    computeDataForStackPlot(metricsDependingOnGrid,
        storiesName, labelsName) {
      const obj = {};
      for (const elem of metricsDependingOnGrid) {
        const currentDiagnostic = this.getDiagnostic(elem);
        if (currentDiagnostic === undefined) {
          continue;
        }
        const nameOfStory = this.getStory(elem);
        if (nameOfStory === undefined) {
          continue;
        }

        if (storiesName.includes(nameOfStory) &&
          labelsName.includes(currentDiagnostic)) {
          let storyToMetricValues = {};
          if (obj.hasOwnProperty(currentDiagnostic)) {
            storyToMetricValues = obj[currentDiagnostic];
          }

          let metricToSampleValues = {};
          if (storyToMetricValues.hasOwnProperty(nameOfStory)) {
            metricToSampleValues = storyToMetricValues[nameOfStory];
          }

          let array = [];
          if (metricToSampleValues.hasOwnProperty(elem.name)) {
            array = metricToSampleValues[elem.name];
          }
          array = array.concat(average(elem.sampleValues));
          metricToSampleValues[elem.name] = array;
          storyToMetricValues[nameOfStory] = metricToSampleValues;
          obj[currentDiagnostic] = storyToMetricValues;
        }
      }
      return obj;
    },

    //  Draw a bar chart.
    plotBarChart(data) {
      this.push();
      this.graph.xAxis('Story')
          .yAxis('Memory used (MiB)')
          .title('Labels')
          .setData(data, story => app.$emit('bar_clicked', story))
          .plotBar();
    },

    //  Draw a dot plot depending on the target value.
    //  This is mainly for results from the table.
    plotDotPlot(target, story, traces) {
      this.push();
      const openTrace = (label, index) => {
        window.open(traces[label][index]);
      };
      this.graph
          .yAxis('')
          .xAxis('Memory used (MiB)')
          .title(story)
          .setData(target, openTrace)
          .plotDot();
    },

    //  Draw a cumulative frequency plot depending on the target value.
    //  This is mainly for the results from the table.
    plotCumulativeFrequencyPlot(target, story) {
      this.push();
      this.graph.yAxis('Cumulative frequency')
          .xAxis('Memory used (MiB)')
          .title(story)
          .setData(target)
          .plotCumulativeFrequency();
    },

    plotStackBar(obj, title) {
      this.push();
      this.graph.xAxis('Stories')
          .yAxis('Memory used (MiB)')
          .title(title)
          .setData(obj)
          .plotStackedBar();
    },

    push() {
      if (!this.state.history) {
        this.state.history = true;
        const clone = o => JSON.parse(JSON.stringify(o));
        this.stateManager.pushState({
          app: clone(this.state),
          menu: clone(menu.state),
          table: clone(this.$refs.tableComponent.state),
        });
      }
      this.state.history = false;
    },

    undo() {
      const state = this.stateManager.popState();
      this.replaceState(this.state, state.app);
      this.replaceState(menu.state, state.menu);
      this.replaceState(this.$refs.tableComponent.state, state.table);
    },

    replaceState(oldState, newState) {
      Object.keys(oldState).forEach((key) => {
        if (!_.isEqual(oldState[key], newState[key])) {
          oldState[key] = newState[key];
        }
      });
    },
    //  Being given a metric, a story, a diagnostic and a set of
    //  subdiagnostics (for example, 3 labels from the total available
    //  ones), the method return the sample values for each subdiagnostic.
    getSubdiagnostics(
        getTargetValueFromSample, metric, story, diagnostic, diagnostics) {
      const result = this.sampleArr
          .filter(value => value.name === metric &&
          this.guidValue
              .get(value.diagnostics.stories)[0] ===
              story);

      const content = new Map();
      for (const val of result) {
        const diagnosticItem = this.guidValue.get(
            val.diagnostics[diagnostic]);
        if (diagnosticItem === undefined) {
          continue;
        }
        let currentDiagnostic = '';
        if (typeof diagnosticItem === 'number') {
          currentDiagnostic = diagnosticItem;
        } else {
          currentDiagnostic = diagnosticItem[0];
        }
        const targetValue = getTargetValueFromSample(val);
        if (content.has(currentDiagnostic)) {
          const aux = content.get(currentDiagnostic);
          content.set(currentDiagnostic, aux.concat(targetValue));
        } else {
          content.set(currentDiagnostic, targetValue);
        }
      }
      const obj = {};
      for (const [key, value] of content.entries()) {
        if (diagnostics === undefined ||
          diagnostics.includes(key.toString())) {
          obj[key] = value;
        }
      }
      return obj;
    },

    getSampleValues(sample) {
      const toMiB = (x) => (x / MiB).toFixed(5);
      const values = sample.sampleValues;
      return values.map(value => toMiB(value));
    },
    //  Draw a plot by default with all the sub-diagnostics
    //  in the same plot;
    plotSingleMetricWithAllSubdiagnostics(metric, story, diagnostic) {
      const obj = this.getSubdiagnostics(
          this.getSampleValues, metric, story, diagnostic);
      this.plotCumulativeFrequencyPlot(obj, story);
    },

    //  Draw a plot depending on the target value which is made
    //  of a metric, a story, a diagnostic and a couple of sub-diagnostics
    //  and the chosen type of plot. All are chosen from the table.
    plotSingleMetric(metric, story, diagnostic,
        diagnostics, chosenPlot) {
      this.state.chosenTypeOfPlot = chosenPlot;
      const target = this.targetForMultipleDiagnostics(
          this.getSampleValues, metric, story, diagnostic, diagnostics);
      if (chosenPlot === 'Dot plot') {
        const getTraceLinks = (sample) => {
          const traceId = sample.diagnostics.traceUrls;
          return this.guidValue.get(traceId);
        };
        const traces = this.targetForMultipleDiagnostics(
            getTraceLinks, metric, story, diagnostic, diagnostics);
        this.plotDotPlot(target, story, traces);
      } else {
        this.plotCumulativeFrequencyPlot(target, story);
      }
    },

    //  Compute the target when the metric, story, diagnostics and
    //  sub-diagnostics are chosen from the table, not from the drop-down menu.
    //  It should be the same for both components but for now they should
    //  be divided.
    targetForMultipleDiagnostics(
        getTargetValueFromSample, metric, story, diagnostic, diagnostics) {
      if (metric === null || story === null ||
        diagnostic === null || diagnostics === null) {
        return undefined;
      }
      return this.getSubdiagnostics(
          getTargetValueFromSample, metric, story, diagnostic, diagnostics);
    }
  },

  computed: {
    gridDataLoaded() {
      return this.state.gridData.length > 0;
    },
    data_loaded() {
      return this.sampleArr.length > 0;
    },

    seen_stories() {
      return this.stories && this.stories.length > 0;
    },

    seen_diagnostics() {
      return this.diagnostics && this.diagnostics.length > 0;
    },
  },

  watch: {

    //  Whenever we have new inputs from the menu (parsed inputs that
    //  where obtained by choosing from the tree) these should be
    //  added in the table (adding the average sample value).
    //  Also it creates by default a stack plot for all the metrics
    //  obtained from the tree-menu, all the stories from the top-level
    //  metric and all available labels.
    'state.parsedMetrics'() {
      if (this.state.parsedMetrics.length === 0) {
        // The menu has no metrics selected (the default state) so show
        // the entire table.
        this.resetTableData();
        return;
      }
      const newGridData = [];
      for (const metric of this.state.parsedMetrics) {
        for (const elem of this.defaultGridData) {
          if (elem.metric === metric) {
            newGridData.push(elem);
          }
        }
      }
      this.state.gridData = newGridData;

      //  We select from sampleValues all the metrics thath
      //  corespond to the result from tree menu (gridData)
      const metricsDependingOnGrid = [];
      const gridMetricsName = [];

      for (const metric of this.state.gridData) {
        gridMetricsName.push(metric.metric);
      }

      for (const metric of this.sampleArr) {
        if (gridMetricsName.includes(metric.name)) {
          metricsDependingOnGrid.push(metric);
        }
      }

      //  The top level metric is taken as source in
      //  computing stories.
      const storiesName =
          this.getStoriesByMetric(this.state.gridData[0].metric);
      const labelsName = this.columnsForChosenDiagnostic;
      const obj = this.computeDataForStackPlot(metricsDependingOnGrid,
          storiesName, labelsName);
      this.plotStackBar(obj, newGridData[0].metric);
      //  From now on the user will be able to switch between
      //  this 2 types of plot (taking into consideration that
      //  the scope of the tree-menu is to analyse using the
      //  the stacked plot and bar plot, we avoid for the moment
      //  other types of plot that should be actually used without
      //  using the tree menu)
      this.state.typesOfPlot = ['Bar chart plot', 'Stacked bar plot'];
      this.state.chosenTypeOfPlot = 'Stacked bar plot';
    }
  }
});
