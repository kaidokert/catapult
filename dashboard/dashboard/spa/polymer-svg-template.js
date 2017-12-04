/* Copyright 2017 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.

   TODO Remove this file after Polymer#1976 is fixed:
   https://github.com/Polymer/polymer/issues/1976
   https://github.com/garryyao/polymer-svg-template
*/
'use strict';
(function(root, factory) {
  if (typeof define === 'function' && define.amd) {
    // AMD. Register as an anonymous module.
    define([], function() {
      return (root.PolymerSvgTemplate = factory());
    });
  } else if (typeof exports === 'object') {
    // Node. Does not work with strict CommonJS, but
    // only CommonJS-like enviroments that support module.exports,
    // like Node.
    module.exports = factory();
  } else {
    // Browser globals
    root.PolymerSvgTemplate = factory();
  }
}(this, function() {
  // UMD Definition above, do not remove this line
  // To get to know more about the Universal Module Definition
  // visit: https://github.com/umdjs/umd
  return name => {
    const ua = window.navigator.userAgent;

    // IE10-11 does not need this fix.
    if (/MSIE /.test(ua) || /Trident\//.test(ua)) return;

    // owner document of this import module
    const doc = document.currentScript.ownerDocument;
    const ns = doc.body.namespaceURI;

    const template = Polymer.DomModule.import(name, 'template');
    if (template) {
      walkTemplate(template._content || template.content);
    }

    function upgradeTemplate(el) {
      const attribs = el.attributes;
      const tmpl = el.ownerDocument.createElement('template');
      el.parentNode.insertBefore(tmpl, el);
      let count = attribs.length;
      while (count-- > 0) {
        const attrib = attribs[count];
        tmpl.setAttribute(attrib.name, attrib.value);
        el.removeAttribute(attrib.name);
      }
      el.parentNode.removeChild(el);
      const content = tmpl.content;
      let child;
      while (child = el.firstChild) {
        content.appendChild(child);
      }
      return tmpl;
    }

    function walkTemplate(root) {
      const treeWalker = doc.createTreeWalker(
          root,
          NodeFilter.SHOW_ELEMENT,
          {acceptNode(node) { return NodeFilter.FILTER_ACCEPT; }},
          false);
      while (treeWalker.nextNode()) {
        let node = treeWalker.currentNode;
        if (node.localName === 'svg') {
          walkTemplate(node);
        } else if (node.localName === 'template' &&
                   !node.hasAttribute('preserve-content') &&
                   node.namespaceURI !== ns) {
          node = upgradeTemplate(node);
          walkTemplate(node._content || node.content);
          treeWalker.currentNode = node;
        }
      }
    }
  };
}));
