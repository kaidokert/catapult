'use strict';
class SizeByProbe {
  constructor(sizeOsProbe, sizeChromeProbe) {
    this.sizeOs = sizeOsProbe;
    this.sizeChrome = sizeChromeProbe;
  }
}

class ComponentByProbe {
  constructor(componentByOs, componentByChrome) {
    this.componentByOs = componentByOs;
    this.componentByChrome = componentByChrome;
  }
}

//  Method for parsing the metric string. It creates collections with
//  all types of browsers, subprocesses, probes, components and sizes.
//  Sizes are splitted in two because they are linked with the type of
//  probe: from Chrome or from OS.
//  Components are stored in a hierarchy made from maps.
function parseAllMetrics(metricNames) {
  let browserOptions = [];
  let subprocessOptions = [];
  let probeOptions = [];
  const componentForOs = new Map();
  const componentForChrome = new Map();
  const componentOptions = new ComponentByProbe();
  let sizeForOs = [];
  let sizeForChrome = [];
  const sizeOptions = new SizeByProbe();

  //  Depending on the type of probe, two maps will be created.
  for (let element of metricNames) {
    if (element.includes('memory')) {
      element = element.split(':');
      element.splice(0, 1);
      browserOptions.push(element[0]);
      subprocessOptions.push(element[1]);
      element.splice(0, 2);
      if (element[0] === 'reported_by_chrome') {
        probeOptions.push(element[0]);
        sizeForChrome.push(element[element.length - 1]);
        element.splice(0, 1);
        element.splice(element.length - 1, 1);
        if (element.length === 0) {
          continue;
        }
        if (element.length === 1) {
          if (!componentForChrome.has(element[0])) {
            componentForChrome.set(element[0], []);
          }
        } else {
          if (!componentForChrome.has(element[0])) {
            const map = new Map();
            if (element[2] === undefined) {
              map.set(element[1], []);
              componentForChrome.set(element[0], map);
            } else {
              map.set(element[1], [element[2]]);
              componentForChrome.set(element[0], map);
            }
          } else {
            const map = componentForChrome.get(element[0]);
            if (map.has(element[1])) {
              if (element[2] !== undefined) {
                const arr = map.get(element[1]);
                if (!arr.includes(element[2])) {
                  arr.push(element[2]);
                  map.set(element[1], arr);
                  componentForChrome.set(element[0], map);
                }
              }
            } else {
              if (element[2] === undefined) {
                map.set(element[1], []);
                componentForChrome.set(element[0], map);
              } else {
                map.set(element[1], [element[2]]);
                componentForChrome.set(element[0], map);
              }
            }
          }
        }
      } else
      if (element[0] === 'reported_by_os') {
        probeOptions.push(element[0]);
        sizeForOs.push(element[element.length - 1]);
        element.splice(0, 1);
        element.splice(element.length - 1, 1);
        if (element.length === 0) {
          continue;
        }
        if (element.length === 1) {
          if (!componentForOs.has(element[0])) {
            componentForOs.set(element[0], []);
          }
        } else {
          if (componentForOs.has(element[0])) {
            const aux = componentForOs.get(element[0]);
            if (!aux.includes(element[1])) {
              aux.push(element[1]);
              componentForOs.set(element[0], aux);
            }
          } else {
            componentForOs.set(element[0], [element[1]]);
          }
        }
      } else {
        element.splice(0, 1);
        element.splice(element.length - 1, 1);
      }
    }
  }

  browserOptions = _.uniq(browserOptions);
  subprocessOptions = _.uniq(subprocessOptions);
  probeOptions = _.uniq(probeOptions);
  sizeForChrome = _.uniq(sizeForChrome);
  sizeForOs = _.uniq(sizeForOs);
  sizeOptions.sizeOs = sizeForOs;
  sizeOptions.sizeChrome = sizeForChrome;
  componentOptions.componentByChrome = componentForChrome;
  componentOptions.componentByOs = componentForOs;

  return {
    browsers: browserOptions,
    subprocesses: subprocessOptions,
    probes: probeOptions,
    components: componentOptions,
    sizes: sizeOptions,
    names: metricNames
  };
}
