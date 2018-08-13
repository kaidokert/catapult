'use strict';
/**
 * Concrete implementation of Plotter strategy for creating
 * bar charts.
 * @implements {Plotter}
 */
class BarPlotter {
  constructor() {
    /** @private @const {number} x_
     * The x axis column in the graph data table.
     */
    this.x_ = 0;
    /** @private @const {number} x_
     * The y axis column in the graph data table.
     */
    this.y_ = 1;
  }
  /**
   * Initalises the chart by computing the scales for the axes and
   * drawing them. It also applies the labels to the graph (axes and
   * graph titles).
   * @param {GraphData} graph Data to be drawn.
   * @param {Object} chart Chart to draw to.
   * @param {Object} chartDimensions Size of the chart.
   */
  initChart_(graph, chart, chartDimensions) {
    this.outerBandScale_ = this.createXAxisScale_(graph, chartDimensions);
    this.scaleForYAxis_ = this.createYAxisScale_(graph, chartDimensions);
    this.xAxisGenerator_ = d3.axisBottom(this.outerBandScale_);
    this.yAxisGenerator_ = d3.axisLeft(this.scaleForYAxis_);
    // Draw the x-axis.
    chart.append('g')
        .call(this.xAxisGenerator_)
        .attr('transform', `translate(0, ${chartDimensions.height})`);
    this.yAxisDrawing_ = chart.append('g')
        .call(this.yAxisGenerator_);
    // Each story is assigned a band by the createXAxisScale function
    // which maintains the positions in which each category of the chart
    // will be rendered. This further divides these bands into
    // sub-bands for each data source.
    this.innerBandScale_ = this.createInnerBandScale_(graph);
  }

  getBarCategories_(graph) {
    // Process data sources so that their data contains only their categories.
    const dataSources = graph.process(data => data.map(row => row[this.x_]));
    // Extract categories from each data source and put them in one array.
    // This is to handle the possiblity that different datasources
    // may have different categories.
    const allCategories = dataSources
        .map(({ data }) => data)
        .reduce((arr, curr) => arr.concat(curr), []);
    return Array.from(new Set(allCategories));
  }

  createXAxisScale_(graph, chartDimensions) {
    return d3.scaleBand()
        .domain(this.getBarCategories_(graph))
        .range([0, chartDimensions.width])
        .padding(0.2);
  }

  createYAxisScale_(graph, chartDimensions) {
    return d3.scaleLinear()
        .domain([graph.max(row => row[this.y_]), 0])
        .range([0, chartDimensions.height]);
  }

  createInnerBandScale_(graph) {
    const keys = graph.keys();
    return d3.scaleBand()
        .domain(keys)
        .range([0, this.outerBandScale_.bandwidth()]);
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
    this.initChart_(graph, chart, chartDimensions);
    graph.dataSources.forEach(({ data, color, key }, index) => {
      const barStart = category =>
        this.outerBandScale_(category) + this.innerBandScale_(key);
      const barWidth = this.innerBandScale_.bandwidth();
      const barHeight = value =>
        chartDimensions.height - this.scaleForYAxis_(value);
      chart.selectAll(`.bar-${key}`)
          .data(data)
          .enter()
          .append('rect')
          .attr('class', `.bar-${key}`)
          .attr('x', d => barStart(d[this.x_]))
          .attr('y', d => this.scaleForYAxis_(d[this.y_]))
          .attr('width', barWidth)
          .attr('height', d => barHeight(d[this.y_]))
          .attr('fill', color);
      legend.append('text')
          .text(key)
          .attr('y', index + 'em')
          .attr('fill', color);
    });
  }
}
