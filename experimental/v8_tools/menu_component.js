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
    probeOptions: [],

    componentObject: null,
    sizeObject: null,

    subcomponent: null,
    subcomponent_: null,


  },

  computed: {
    //  Compute size options depending on the type of probe.
    sizeOptions() {
      if (this.sizeObject !== null) {
        if (this.probe === 'reported_by_chrome') {
          return this.sizeObject.sizeChrome;
        }
        return this.sizeObject.sizeOs;
      }
      return undefined;
    },
    //  The components are different depending on the type of probe.
    componentOptions() {
      if (this.componentObject !== null) {
        if (this.probe === 'reported_by_chrome') {
          const component = [];
          for (const [key, value] of this.componentObject
              .componentByChrome.entries()) {
            component.push(key);
          }
          return component;
        }
        const component = [];
        for (const [key, value] of this.componentObject
            .componentByOs.entries()) {
          component.push(key);
        }
        return component;
      }
      return undefined;
    },

    //  Compute the options for the first subcomponent depending on the probes.
    //  When the user chooses a component, it might be a hierarchical one.
    firstSubcompOptions() {
      if (this.component !== null) {
        if (this.probe === 'reported_by_chrome') {
          if (this.componentObject.componentByChrome
              .get(this.component) !== undefined) {
            const map = this.componentObject
                .componentByChrome.get(this.component);
            const array = [];
            for (const [key, value] of map.entries()) {
              array.push(key);
            }
            return array;
          }
          return undefined;
        }
        return this.componentObject.componentByOs.get(this.component);
      }
      return undefined;
    },

    //  In case when the component is from Chrome, the hierarchy might have more
    //  levels.
    secondSubcompOptions() {
      if (this.probe === 'reported_by_chrome' && this.subcomponent !== null) {
        const map = this.componentObject.componentByChrome.get(this.component);
        return map.get(this.subcomponent);
      }
      return undefined;
    }
  },
  watch: {
    probe() {
      this.component = null;
      this.subcomponent = null;
      this.subcomponent_ = null;
      this.size = null;
    },

    component() {
      this.subcomponent = null;
      this.subcomponent_ = null;
      this.size = null;
    },

    subcomponent() {
      this.subcomponent_ = null;
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
        app.parsedMetrics = _.uniq(metrics);
      }
    }
  }
});
