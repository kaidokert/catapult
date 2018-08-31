'use strict';
/**
 * Concrete implementation of Plotter strategy for creating
 * stacked bar charts.
 * @implements {Plotter}
 */
class StackedBarPlotter {
  constructor() {
    /** @private @const {number} x_
     * The x axis column in the graph data table.
     */
    this.name_ = 0;
    /** @private @const {number} x_
     * The y axis column in the graph data table.
     */
    this.data_ = 1;
  }
  /**
   * Initalises the chart by computing the scales for the axes and
   * drawing them. It also applies the labels to the graph (axes and
   * graph titles).
   * @param {GraphData} graph Data to be drawn.
   * @param {Object} chart Chart to draw to.
   * @param {Object} chartDimensions Size of the chart.
   */
  initChart_(graph, chart, chartDimensions, data) {
    this.outerBandScale_ = this.createXAxisScale_(graph, chartDimensions);
    this.scaleForYAxis_ = this.createYAxisScale_(chartDimensions, data);
    this.xAxisGenerator_ = d3.axisBottom(this.outerBandScale_);
    this.yAxisGenerator_ = d3.axisLeft(this.scaleForYAxis_);
    chart.append('g')
        .attr('class', 'xaxis')
        .call(this.xAxisGenerator_)
        .attr('transform', `translate(0, ${chartDimensions.height})`);
    this.yAxisDrawing_ = chart.append('g')
        .call(this.yAxisGenerator_);
    // Each story is assigned a band by the createXAxisScale function
    // which maintains the positions in which each category of the chart
    // will be rendered. This further divides these bands into
    // sub-bands for each data source, so that different labels can be
    // grouped within the same category.
    this.innerBandScale_ = this.createInnerBandScale_(graph);
  }

  getBarCategories_(graph) {
    // Process data sources so that their data contains only their categories.
    const dataSources = graph.process(data => data.map(row => row[this.name_]));
    if (dataSources.length > 0) {
      return dataSources[0].data;
    }
    return [];
  }

  createXAxisScale_(graph, chartDimensions) {
    return d3.scaleBand()
        .domain(this.getBarCategories_(graph))
        .range([0, chartDimensions.width])
        .padding(0.2);
  }

  createYAxisScale_(chartDimensions, sources) {
    const getStackHeights =
        metrics => metrics.map(metric => metric[this.data_].height);
    const getBarHeight =
        story => this.sum_(getStackHeights(story[this.data_]));
    const maxHeight =
        stories => d3.max(stories.map(story => getBarHeight(story)));
    const maxHeightOfAllSources =
        d3.max(sources.map(({ data }) => maxHeight(data)));
    return d3.scaleLinear()
        .domain([maxHeightOfAllSources, 0]).nice()
        .range([0, chartDimensions.height]);
  }

  createInnerBandScale_(graph) {
    const keys = graph.keys();
    return d3.scaleBand()
        .domain(keys)
        .range([0, this.outerBandScale_.bandwidth()]);
  }

  /**
   * Attempts to compute the average of the given numbers but returns
   * 0 if the supplied array is empty.
   * @param {Array<number>} data
   * @returns {number}
   */
  avg_(data) {
    return this.sum_(data) / data.length || 0;
  }

  sum_(data) {
    if (!data.every(val => typeof val === 'number')) {
      throw new TypeError('Expected an array of numbers.');
    }
    return data.reduce((a, b) => a + b, 0);
  }

  computeStackedAvgs_(data) {
    const stackedAverages = [];
    let cumulativeAvg = 0;
    for (const [name, values] of Object.entries(data)) {
      const average = this.avg_(values);
      const yValues = {
        start: cumulativeAvg,
        height: average,
      };
      cumulativeAvg += average;
      stackedAverages.push([name, yValues]);
    }
    return stackedAverages;
  }
  /**
   * Draws a bar chart to the canvas. If there are multiple dataSources it will
   * plot them both and label their colors in the legend. This expects the data
   * in graph to be formatted as a table, with the first column being categories
   * and the second being the corresponding values.
   * @param {GraphData} graph The data to be plotted.
   * @param {Object} chart d3 selection for the chart element to be drawn on.
   * @param {Object} legend d3 selection for the legend element for
   * additional information to be drawn on.
   * @param {Object} chartDimensions The margins, width and height
   * of the chart. This is useful for computing appropriates axis
   * scales and positioning elements.
   */
  plot(graph, chart, legend, chartDimensions) {
    const computeAllAverages = stories =>
      stories.map(
          ([story, values]) => [story, this.computeStackedAvgs_(values)]);
    const dataInAverages = graph.process(computeAllAverages);
    this.initChart_(graph, chart, chartDimensions, dataInAverages);
    dataInAverages.forEach(({ data, color, key }, index) => {
      data.forEach((stories) => {
        this.drawStackedBar(chart, stories, chartDimensions, key);
      });
    });
    const metrics = dataInAverages[0].data[0][1].map(([metric]) => metric);
    d3.selectAll('.xaxis .tick text')
        .attr('font-size', 15)
        .attr('dy', 50);
    metrics.forEach((metric, i) => {
      const g = legend.append('g').attr('transform', `translate(0, ${i * 20})`);
      g.append('rect')
          .attr('fill', d3.schemeCategory10[i])
          .attr('height', 10)
          .attr('width', 10)
          .attr('y', 0)
          .attr('x', 0);
      g.append('text')
          .text(metric)
          .attr('dx', 10)
          .attr('y', 10)
          .attr('text-anchor', 'start');
    });
  }

  drawStackedBar(selection, stories, chartDimensions, key) {
    const storyName = stories[this.name_];
    const stackData = stories[this.data_];
    const colors = d3.schemeCategory10;
    const x = this.outerBandScale_(storyName) + this.innerBandScale_(key);
    stackData.forEach((metrics, i) => {
      const positions = metrics[this.data_];
      const height =
          chartDimensions.height - this.scaleForYAxis_(positions.height);
      selection.append('rect')
          .attr('x', x)
          .attr('y', this.scaleForYAxis_(positions.height + positions.start))
          .attr('width', this.innerBandScale_.bandwidth())
          .attr('height', height)
          .attr('fill', colors[i]);
    });
    // Show display label
    const labelEnd = x + this.innerBandScale_.bandwidth();
    d3.select('.xaxis')
        .append('text')
        .text(key)
        .attr('fill', 'black')
        .attr('text-anchor', 'end')
        .attr('transform', `translate(${labelEnd}, 10)rotate(-10)`)
        .append('title')
        .text(key);
  }
}
