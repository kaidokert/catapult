'use strict';
const DEFAULT_PLOTS = ['Cumulative frequency plot', 'Dot plot'];

//  Vue component for drop-down menu; here the metrics,
//  stories and diagnostics are chosen through selection.
const app = new Vue({
  el: '#app',
  data: {
    sampleArr: [],
    guidValue: null,
    graph: new GraphData(),
    searchQuery: '',
    gridColumns: ['metric'],
    gridData: [],
    parsedMetrics: null,
    columnsForChosenDiagnostic: null,
    defaultGridData: [],
    typesOfPlot: DEFAULT_PLOTS,
    chosenTypeOfPlot: null
  },

  methods: {
    //  Reset the table content by returning to the
    //  previous way that contained all the available
    //  metrics.
    resetTableData() {
      this.gridData = this.defaultGridData;
    },

    //  Get all stories for a specific metric.
    getStoriesByMetric(entry) {
      const stories = [];
      for (const e of this.sampleArr) {
        if (e.name !== entry) {
          continue;
        }
        const nameOfStory = this.guidValue.get(e.diagnostics.stories);
        if (nameOfStory === undefined) {
          continue;
        }
        stories.push(nameOfStory);
      }
      return _.uniq(stories);
    },

    //  Extract a diagnostic from a specific
    //  element (like metric). This should be 'parsed' because
    //  sometimes it might be either a number or a
    //  single element array.
    getDiagnostic(elem, diagnostic) {
      const currentDiagnostic = this.guidValue.
          get(elem.diagnostics[diagnostic]);
      if (currentDiagnostic === undefined) {
        return undefined;
      }
      return currentDiagnostic;
    },

    //  This method creates an object for multiple metrics,
    //  multiple stories and some diagnostics:
    //  {labelName: {storyName: { metricName: sampleValuesArray}}}
    computeDataForStackPlot(metricsDependingOnGrid,
        storiesName, labelsName) {
      const obj = {};
      for (const elem of metricsDependingOnGrid) {
        const currentDiagnostic = this.getDiagnostic(elem, 'labels');
        if (currentDiagnostic === undefined) {
          continue;
        }
        const nameOfStory = this.getDiagnostic(elem, 'stories');
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
      this.graph.xAxis('Story')
          .yAxis('Memory used (MiB)')
          .title('Labels')
          .setData(data, story => app.$emit('bar_clicked', story))
          .plotBar();
    },

    //  Draw a dot plot.
    plotDotPlot(target, story, traces) {
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

    //  Draw a cumulative frequency plot.
    plotCumulativeFrequencyPlot(target, story) {
      this.graph.yAxis('Cumulative frequency')
          .xAxis('Memory used (MiB)')
          .title(story)
          .setData(target)
          .plotCumulativeFrequency();
    },

    //  Draw a stack bar chart.
    plotStackBar(obj, title) {
      this.graph.xAxis('Stories')
          .yAxis('Memory used (MiB)')
          .title(title)
          .setData(obj)
          .plotStackedBar();
    },

    //  Being given a metric, a story, a diagnostic and a set of
    //  subdiagnostics (i.e. 3 labels from the total of 4), the
    //  method return the sample values for each subdiagnostic.
    getSubdiagnostics(
        getTargetValueFromSample, metric, story, diagnostic, diagnostics) {
      const result = this.sampleArr
          .filter(value => value.name === metric &&
          this.guidValue
              .get(value.diagnostics.stories) ===
              story);

      const content = new Map();
      for (const val of result) {
        const diagnosticItem = this.guidValue.get(
            val.diagnostics[diagnostic]);
        if (diagnosticItem === undefined) {
          continue;
        }
        const targetValue = getTargetValueFromSample(val);
        if (content.has(diagnosticItem)) {
          const aux = content.get(diagnosticItem);
          content.set(diagnosticItem, aux.concat(targetValue));
        } else {
          content.set(diagnosticItem, targetValue);
        }
      }
      const obj = {};
      for (const [key, value] of content.entries()) {
        let key_ = key;
        if (diagnostics !== undefined) {
          if (typeof diagnostics[0] === 'number') {
            key_ = Number(key_);
          } else {
            key_ = key_.toString();
          }
        }
        if (diagnostics === undefined ||
          diagnostics.includes(key_)) {
          obj[key_] = value;
        }
      }
      return obj;
    },

    getSampleValues(sample) {
      const toMiB = (x) => (x / MiB).toFixed(5);
      const values = sample.sampleValues;
      return values.map(value => toMiB(value));
    },

    //  Draw a cumulative frequency plot by default with
    //  all the sub-diagnostics (labels) in the same plot.
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
    //  sub-diagnostics are chosen.
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
      return this.gridData.length > 0;
    },

    data_loaded() {
      return this.sampleArr.length > 0;
    }
  },

  watch: {
    //  Whenever a new metric/ story/ diagnostic is chosen
    //  this function will run for drawing a new type of plot.
    //  These items are chosen from the drop-down menu.
    filteredData() {
      this.plotCumulativeFrequency();
    },

    //  Whenever we have new inputs from the menu (parsed inputs that
    //  where obtained by choosing from the tree) these should be
    //  added in the table (adding the average sample value).
    //  Also it creates by default a stack plot for all the metrics
    //  obtained from the tree-menu, all the stories from the top-level
    //  metric and all labels.
    parsedMetrics() {
      const newGridData = [];
      const gridMetricsName = [];
      for (const metric of this.parsedMetrics) {
        for (const elem of this.defaultGridData) {
          if (elem.metric === metric) {
            newGridData.push(elem);
            gridMetricsName.push(elem.metric);
          }
        }
      }
      this.gridData = newGridData;

      //  The top level metric is taken as source in
      //  computing stories.
      const storiesName = this.getStoriesByMetric(this
          .gridData[0].metric);
      const labelsName = this.columnsForChosenDiagnostic;

      this.$refs.tableComponent.markedTableMetrics = gridMetricsName;
      this.$refs.tableComponent.markedTableStories = storiesName;
      this.$refs.tableComponent.markedTableDiagnostics = labelsName;
      this.typesOfPlot = DEFAULT_PLOTS;
      this.$refs.tableComponent.setCheckBoxes(true, 'checkbox-metric');
      this.$refs.tableComponent.setCheckBoxes(true, 'checkbox-head');
      this.$refs.tableComponent.setCheckBoxes(true, 'checkbox-story');
    }
  }
});
