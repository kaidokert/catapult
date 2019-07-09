/* Copyright 2019 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import {RequestBase} from './request-base.js';

// If `options.text` is unset, then the handler will query for notes matching
// suite, measurement, bot, case, minRevision, maxRevision. Use request.reader()
// to process both cached results from the service worker as well as fresh
// results from the network.
// If `options.text` is set to the empty string, then the handler will delete
// the note identified by `options.key`.
// If `options.text` is a non-empty string, then the handler will update the
// note identified by `options.key`.
export class NotesRequest extends RequestBase {
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
    if (options.key) this.body_.set('key', options.key);
    if (options.text !== undefined) this.body_.set('text', options.text);
  }

  get url_() {
    return NotesRequest.URL;
  }

  postProcess_(notes, isFromChannel = false) {
    return notes.map(note => {
      return {
        ...note,
        updated: new Date(note.updated),
        minRevision: note.min_revision,
        maxRevision: note.max_revision,
      };
    });
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
