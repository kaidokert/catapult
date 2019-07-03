/* Copyright 2019 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import RequestBase from './request-base.js';

export default class NotesRequest extends RequestBase {
  constructor(options) {
    super(options);
    this.method_ = 'POST';
    this.body_ = new FormData();
    this.body_.set('suite', options.suite);
    this.body_.set('measurement', options.measurement);
    this.body_.set('bot', options.bot);
    this.body_.set('case', options.case);
    this.body_.set('min_revision', options.maxRevision);
    this.body_.set('max_revision', options.maxRevision);
    if (options.id) this.body_.set('id', options.id);
    if (options.text) this.body_.set('text', options.text);
  }

  get url_() {
    return NotesRequest.URL;
  }

  get description_() {
    const path = [
      this.body_.get('suite'),
      this.body_.get('measurement'),
      this.body_.get('bot'),
      this.body_.get('case'),
    ].join('/');
    return `loading notes for ${path}`;
  }
}
NotesRequest.URL = '/api/notes';
