'use strict';
/**
 * Represents the data to be displayed on a graph and enables processing
 * of the data for display. This class is to be used as input to a
 * graph plotter.
 */
class GraphData {
  constructor() {
    /** @private @const {xAxis: string, yAxis:string} */
    this.labels = {
      xAxis: '',
      yAxis: '',
      title: '',
    };
    /** @private @const {Array<Object>} */
    this.dataSources = [];
    /** @private @const {Object} */
    this.plotter_ = new GraphPlotter(this);
    /** @private @const {Array<string>} colors_
     * Each new datasource is assigned a color.
     * At first an attempt will be made to assign an unused color
     * from this array and failing that the default color is used.
     */
    this.colors_ = [
      'green',
      'orange',
    ];
    /** @private @const {string} fallbackColor_ The default line color.*/
    this.fallbackColor_ = 'black';
  }

  /**
   * Sets the label for the x-axis if provided as an argument and returns
   * this instance for method chaining. If no label is provided then
   * the current label is returned.
   * @param {string} label
   * @return {(string|GraphData)}
   */
  xAxis(label) {
    if (arguments.length > 0) {
      this.labels.xAxis = label;
      return this;
    }
    return this.labels.xAxis;
  }

  /**
   * Sets the label for the y-axis if provided as an argument and returns
   * this instance for method chaining. If no label is provided then
   * the current label is returned.
   * @param {string} label
   * @return {(string|GraphData)}
   */
  yAxis(label) {
    if (arguments.length > 0) {
      this.labels.yAxis = label;
      return this;
    }
    return this.labels.yAxis;
  }

  /**
   * Sets the label for the title if provided as an argument and returns
   * this instance for method chaining. If no label is provided then
   * the current label is returned.
   * @param {string} label
   * @return {(string|GraphData)}
   */
  title(label) {
    if (arguments.length > 0) {
      this.labels.title = label;
      return this;
    }
    return this.labels.title;
  }

  /**
   * Registers the supplied data as a dataSource, enabling it to be plotted and
   * processed. The data source should be in the form of an object where
   * the keys are the desired display labels (for the legend) corresponding
   * to the supplied values, each of which should be an array of numbers.
   * @param {Object} data
   * @return {GraphData}
   */
  addData(data) {
    if (typeof data !== 'object') {
      throw new Error('Expected an object to be supplied.');
    }
    const displayLabels = Object.keys(data);
    let index = this.dataSources.length;
    for (const displayLabel of displayLabels) {
      const values = data[displayLabel];
      if (values.constructor !== Array ||
        !values.every((val) => typeof val === 'number')) {
        throw new Error('The supplied values should be an array of numbers.');
      }
      this.dataSources.push({
        data: values,
        color: index < this.colors_.length ?
          this.colors_[index] : this.fallbackColor_,
        key: displayLabel,
      });
      index++;
    }
    return this;
  }

  /**
   * Returns the maximum value from all dataSources based on the value
   * computed by projection.
   * @param {function(Object): number} projection
   * @return {number}
   */
  max_(projection) {
    const projectAll = dataSource => dataSource.data.map(projection);
    const maxReducer =
      (acc, curr) => Math.max(acc, Math.max(...projectAll(curr)));
    return this.dataSources.reduce(maxReducer, Number.MIN_VALUE);
  }

  /**
   * Finds the maximum value along the points for the x-axis.
   * This is useful when computing appropriate scales for the x-axis.
   * @return {number}
   */
  xAxisMax() {
    return this.max_(point => point.x);
  }

  /**
   * Finds the maximum value along the points for the y-axis.
   * This is useful when computing appropriate scales for the y-axis.
   * @return {number}
   */
  yAxisMax() {
    return this.max_(point => point.y);
  }

  /**
   * Applies the supplied processingFn to all of the dataSources held
   * in this instance and replaces the old data with the newly processed data.
   * The processing function supplied to process should return data in
   * a format suitable for plotting (e.g., an array of
   * objects, consisting of x and y co-ordinates, for a line plot).
   * @param {function(Array<?>): Array<Object>} processingFn
   * @returns {GraphData}
   */
  process(processingFn) {
    if (typeof processingFn !== 'function') {
      const type = typeof processingFn;
      throw new TypeError(
          `Expected argument of type function, but got: ${type}`);
    }
    this.dataSources.forEach(
        source => source.data = processingFn(source.data));
    return this;
  }

  /**
   * Computes the cumulative frequency for all data sources provided
   * and plots the results to the screen. The provided
   * data field in the dataSource must be a list of numbers.
   */
  plotCumulativeFrequency() {
    this.process(GraphData.computeCumulativeFrequencies);
    this.plotter_.linePlot();
  }

  /**
   * Computes the cumulative frequency for the list of values provided.
   * @param {Array<number>} data
   * @returns {Array<Object>}
   */
  static computeCumulativeFrequencies(data) {
    const sortedData = data.sort((a, b) => a - b);
    return sortedData.map((value, i) => {
      return {
        x: i,
        y: value,
      };
    });
  }
}
