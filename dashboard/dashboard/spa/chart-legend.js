/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import {LitElement, html, css} from 'lit-element';

export default class ChartLegend extends LitElement {
  static get properties() {
    return {
      items: {type: Array},
    };
  }

  static get styles() {
    return css`
      :host {
        display: flex;
        flex-direction: column;
      }
      :host * {
        flex-shrink: 0;
      }
      chart-legend {
        margin-left: 16px;
      }
      .leaf {
        cursor: pointer;
      }
      .leaf:hover {
        background: #eee;
      }
    `;
  }

  render() {
    return html`
      ${(this.items || []).map(item => (item.children ? html`
        <div class="branch">
          ${item.label}
        </div>

        <chart-legend .items="${item.children}">
        </chart-legend>
      ` : html`
        <div class="leaf"
            style="color: ${item.color};"
            @mouseover="${this.onLeafMouseOver_}"
            @mouseout="${this.onLeafMouseOut_}"
            @click="${this.onLeafClick_}">
          ${item.label}
        </div>
      `))}
    `;
  }

  async onLeafMouseOver_(event) {
    this.dispatchEvent(new CustomEvent('leaf-mouseover', {
      bubbles: true,
      composed: true,
      detail: event.model.item,
    }));
  }

  async onLeafMouseOut_(event) {
    this.dispatchEvent(new CustomEvent('leaf-mouseout', {
      bubbles: true,
      composed: true,
      detail: event.model.item,
    }));
  }

  async onLeafClick_(event) {
    event.stopPropagation();
    this.dispatchEvent(new CustomEvent('leaf-click', {
      bubbles: true,
      composed: true,
      detail: event.model.item,
    }));
  }
}

customElements.define('chart-legend', ChartLegend);
