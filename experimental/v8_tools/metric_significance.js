'use strict';
/**
 * Performs a test of significance on supplied metric data.
 */
class MetricSignificance {
  constructor() {
    this.data = {};
    this.criticalPValue = 0.05;
  }
  /**
   * Adds the given values to an entry for the supplied metric and
   * label. Tests of significance will be performed against the supplied
   * labels for the given metric. Therefore, each metric should be supplied
   * two labels.
   * @param {string} metric
   * @param {string} label
   * @param {Array<number>} value
   */
  add(metric, label, value) {
    if (!this.data[metric]) {
      this.data[metric] = {};
    }
    if (!this.data[metric][label]) {
      this.data[metric][label] = [];
    }
    const values = this.data[metric][label];
    this.data[metric][label] = values.concat(value);
  }
  /**
   * Returns the metrics which have been identified as having statistically
   * significant changes along with the evidence supporting this (the p values
   * and U values).
   * @return {Array<Object>} The metrics which have significant changes.
   */
  mostSignificant() {
    const significantChanges = [];
    Object.entries(this.data).forEach(([metric, runs]) => {
      const runsData = Object.values(runs);
      if (runsData.length === 2) {
        const evidence = mannwhitneyu.test(...runsData);
        if (evidence.p < this.criticalPValue) {
          significantChanges.push({
            metric,
            evidence,
          });
        }
      }
    });
    return significantChanges;
  }
}
