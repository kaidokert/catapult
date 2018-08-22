'use strict';
const menu = new Vue({
  el: '#menu',
  data: {
    sampleArr: null,
    guidValueInfo: null,

    browser: null,
    subprocess: null,
    probe: null,
    component: null,
    size: null,
    metricNames: null,

    browserOptions: [],
    subprocessOptions: [],

    subcomponent: null,
    subsubcomponent: null,

    componentMap: null,
    sizeMap: null

  },

  computed: {
    //  Compute the probe options from the map returned by parse method.
    probeOptions() {
      if (this.componentMap === null) {
        return undefined;
      }
      const probes = [];
      for (const [key, value] of this.componentMap.entries()) {
        probes.push(key);
      }
      return probes;
    },

    //  Compute size options depending on the type of probe.
    sizeOptions() {
      if (this.probe === null) {
        return undefined;
      }
      return this.sizeMap.get(this.probe);
    },
    //  The components are different depending on the type of probe.
    componentsOptions() {
      if (this.probe === null) {
        return undefined;
      }
      const components = [];
      for (const [key, value] of this.componentMap.get(this.probe).entries()) {
        components.push(key);
      }
      return components;
    },

    sizeOptions() {
      if (this.probe === null) {
        return undefined;
      }
      return this.sizeMap.get(this.probe);
    },

    //  Compute the options for the first subcomponent depending on the probes.
    //  When the user chooses a component, it might be a hierarchical one.
    firstSubcompOptions() {
      if (this.component === null) {
        return undefined;
      }
      const subcomponent = [];
      for (const [key, value] of this
          .componentMap.get(this.probe).get(this.component).entries()) {
        subcomponent.push(key);
      }
      return subcomponent;
    },

    //  In case when the component is from Chrome, the hierarchy might have more
    //  levels.
    secondSubcompOptions() {
      if (this.subcomponent === null) {
        return undefined;
      }
      const subcomponent = [];
      for (const [key, value] of this
          .componentMap
          .get(this.probe)
          .get(this.component)
          .get(this.subcomponent).entries()) {
        subcomponent.push(key);
      }
      return subcomponent;
    }
  },
  watch: {
    probe() {
      this.component = null;
      this.subcomponent = null;
      this.subsubcomponent = null;
      this.size = null;
    },

    component() {
      this.subcomponent = null;
      this.subsubcomponent = null;
    },

    subcomponent() {
      this.subsubcomponent = null;
    },

  },
  methods: {
    //  Build the available metrics upon the chosen items.
    //  The method applies an intersection for all of them and
    //  return the result as a collection of metrics that matched.
    apply() {
      const metrics = [];
      for (const name of this.metricNames) {
        if (this.browser !== null && name.includes(this.browser) &&
          this.subprocess !== null && name.includes(this.subprocess) &&
          this.component !== null && name.includes(this.component) &&
          this.size !== null && name.includes(this.size) &&
          this.probe !== null && name.includes(this.probe)) {
          if (this.subcomponent === null) {
            metrics.push(name);
          } else {
            if (name.includes(this.subcomponent)) {
              if (this.subcomponent_ === null) {
                metrics.push(name);
              } else {
                if (name.includes(this.subcomponent_)) {
                  metrics.push(name);
                }
              }
            }
          }
        }
      }
      if (_.uniq(metrics).length === 0) {
        alert('No metrics found');
      } else {
        alert('You can pick a metric from drop-down');
        app.parsedMetrics = _.uniq(metrics);
      }
    }
  }
});
