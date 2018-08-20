//  Vue component for drop-down menu; here the metrics,
//  stories and diagnostics are chosen through selection.
'use strict';
const app = new Vue({
  el: '#app',
  data: {
    sampleArr: [],
    guidValue: null,
    selected_metric: null,
    selected_story: null,
    selected_diagnostic: null,
    graph: null,
    searchQuery: '',
    gridColumns: ['id', 'metric', 'averageSampleValues'],
    gridData: [],
    parsedMetrics: null
  },

  methods: {
    //  Draw a cumulative frequency plot depending on the target value.
    //  This is mainly for results from the drop-down menu.
    plotCumulativeFrequency() {
      this.graph.xAxis('Data Points')
          .yAxis('Memory used (MiB)')
          .title(this.selected_story)
          .addData(JSON.parse(JSON.stringify((this.target))))
          .plotCumulativeFrequency();
    },

    //  Draw a dot plot depending on the target value.
    //  This is mainly for results from the table.
    plotDotPlot(target, story) {
      this.graph
          .xAxis('Memory used (MiB)')
          .title(story)
          .addData(JSON.parse(JSON.stringify(target)))
          .plotDot();
    },

    //  Draw a cumulative frequency plot depending on the target value.
    //  This is mainly for the results from the table.
    plotCumulativeFrequencyPlot(target, story) {
      this.graph.xAxis('Data Points')
          .yAxis('Memory used (MiB)')
          .title(story)
          .addData(JSON.parse(JSON.stringify(target)))
          .plotCumulativeFrequency();
    },

    //  Draw a plot by default with all the sub-diagnostics
    //  in the same plot;
    plotDefaultByDiagnostic(metric, story, diagnostic) {
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
        if (content.has(currentDiagnostic)) {
          const aux = content.get(currentDiagnostic);
          content.set(currentDiagnostic, aux.concat(val.sampleValues));
        } else {
          content.set(currentDiagnostic, val.sampleValues);
        }
      }
      const contentKeys = [];
      const contentVal = [];
      for (const [key, value] of content.entries()) {
        value.map(value => +((value / MiB).toFixed(5)));
        contentKeys.push(key);
        contentVal.push(value);
      }
      const obj = _.object(contentKeys, contentVal);
      if (this.graph === null) {
        this.graph = new GraphData();
        this.plotCumulativeFrequencyPlot(obj, story);
      } else {
        this.graph.plotter_.remove();
        this.graph = new GraphData();
        this.plotCumulativeFrequencyPlot(obj, story);
      }
    },
    //  Draw a plot depending on the target value which is made
    //  of a metric, a story, a diagnostic and a couple of sub-diagnostics
    //  and the chosen type of plot. All are chosen from the table.
    plotDiagnostics(metric, story, diagnostic,
        diagnostics, chosenPlot) {
      const target = this.targetForMultipleDiagnostics(metric, story,
          diagnostic, diagnostics);
      if (chosenPlot === 'Dot plot') {
        if (this.graph === null) {
          this.graph = new GraphData();
          this.plotDotPlot(target, story);
        } else {
          this.graph.plotter_.remove();
          this.graph = new GraphData();
          this.plotDotPlot(target, story);
        }
      } else {
        if (this.graph === null) {
          this.graph = new GraphData();
          this.plotCumulativeFrequencyPlot(target, story);
        } else {
          this.graph.plotter_.remove();
          this.graph = new GraphData();
          this.plotCumulativeFrequencyPlot(target, story);
        }
      }
    },

    //  Compute the target when the metric, story, diagnostics and
    //  sub-diagnostics come from the table, not from the drop-down menu.
    //  It should be the same for both components but for now they should
    //  be divided.
    targetForMultipleDiagnostics(metric, story, diagnostic, diagnostics) {
      if (metric !== null && story !== null &&
        diagnostic !== null && diagnostics !== null) {
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
          if (content.has(currentDiagnostic)) {
            const aux = content.get(currentDiagnostic);
            content.set(currentDiagnostic, aux.concat(val.sampleValues));
          } else {
            content.set(currentDiagnostic, val.sampleValues);
          }
        }

        const contentKeys = [];
        const contentVal = [];
        for (const [key, value] of content.entries()) {
          if (diagnostics.includes(key.toString())) {
            value.map(value => +((value / MiB).toFixed(5)));
            contentKeys.push(key);
            contentVal.push(value);
          }
        }
        const obj = _.object(contentKeys, contentVal);
        return obj;
      }
      return undefined;
    }
  },

  computed: {
    seen() {
      return this.sampleArr.length > 0 ? true : false;
    },

    seen_stories() {
      if (this.stories !== null && this.stories !== undefined) {
        return this.stories.length > 0 ? true : false;
      }
    },

    seen_diagnostics() {
      if (this.diagnostics !== null && this.diagnostics !== undefined) {
        return this.diagnostics.length > 0 ? true : false;
      }
    },

    //  Compute the metrics for the drop-down menu;
    //  The user will chose one of them.
    metrics() {
      if (this.parsedMetrics !== null) {
        return this.parsedMetrics;
      }
      const metricsNames = [];
      this.sampleArr.forEach(el => metricsNames.push(el.name));
      return _.uniq(metricsNames);
    },

    //  Compute the stories depending on the chosen metric.
    //  The user should chose one of them.
    stories() {
      const reqMetrics = this.sampleArr
          .filter(elem => elem.name === this.selected_metric);
      const storiesByGuid = [];
      for (const elem of reqMetrics) {
        let storyName = this.guidValue.get(elem.diagnostics.stories);
        if (storyName === undefined) {
          continue;
        }
        if (typeof storyName !== 'number') {
          storyName = storyName[0];
        }
        storiesByGuid.push(storyName);
      }
      return Array.from(new Set(storiesByGuid));
    },

    //  Compute all diagnostic elements; the final result will actually
    //  depend on the metric, the story and this diagnostic.
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

    //  Compute the final result with the chosen metric, story and diagnostics.
    //  These are chosen from the drop-down menu.
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
          const diagnosticItem = this.guidValue.get(
              val.diagnostics[this.selected_diagnostic]);
          if (diagnosticItem === undefined) {
            continue;
          }
          let currentDiagnostic = '';
          if (typeof diagnosticItem === 'number') {
            currentDiagnostic = diagnosticItem;
          } else {
            currentDiagnostic = diagnosticItem[0];
          }
          if (content.has(currentDiagnostic)) {
            const aux = content.get(currentDiagnostic);
            content.set(currentDiagnostic, aux.concat(val.sampleValues));
          } else {
            content.set(currentDiagnostic, val.sampleValues);
          }
        }

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
    //  Whenever a new metric/ story/ diagnostic is chosen
    //  this function will run for drawing a new type of plot.
    //  These items are chosen from the drop-down menu.
    target() {
      if (this.graph === null) {
        this.graph = new GraphData();
        this.plotCumulativeFrequency();
      } else {
        this.graph.plotter_.remove();
        this.graph = new GraphData();
        this.plotCumulativeFrequency();
      }
    },
    metrics() {
      this.selected_metric = null;
      this.selected_story = null;
      this.selected_diagnostic = null;
    }
  }
});
