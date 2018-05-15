/**
@license
Copyright (c) 2017 The Polymer Project Authors. All rights reserved.
This code may only be used under the BSD style license found at http://polymer.github.io/LICENSE.txt
The complete set of authors may be found at http://polymer.github.io/AUTHORS.txt
The complete set of contributors may be found at http://polymer.github.io/CONTRIBUTORS.txt
Code distributed by Google as part of the polymer project is also
subject to an additional IP rights grant found at http://polymer.github.io/PATENTS.txt
*/
import '../../../polymer-legacy.js';

import { Polymer } from '../../../lib/legacy/polymer-fn.js';
import { html } from '../../../lib/utils/html-tag.js';
Polymer({
  _template: html`
    <span id="content">inner-element</span>
`,

  is: 'inner-element'
});
