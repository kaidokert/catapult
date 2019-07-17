/* Copyright 2018 The Chromium Authors. All rights reserved.
   Use of this source code is governed by a BSD-style license that can be
   found in the LICENSE file.
*/
'use strict';

import {ResultChannelSender} from '@chopsui/result-channel';

import {
  CacheRequestBase, READONLY, READWRITE, jsonResponse,
} from './cache-request-base.js';

const STORE_NOTES = 'notes';
const EXPIRATION_MS = 20 * 60 * 60 * 1000;

export class NotesCacheRequest extends CacheRequestBase {
  get databaseName() {
    return this.databaseName_;
  }

  get databaseVersion() {
    return 1;
  }

  async upgradeDatabase(db) {
    if (db.oldVersion < 1) {
      db.createObjectStore(STORE_NOTES);
    }
  }

  async writeDatabase(notes) {
    const transaction = await this.transaction([STORE_NOTES], READWRITE);
    const dataStore = transaction.objectStore(STORE_NOTES);
    for (const note of notes) {
      dataStore.put(note, note.key);
    }
    await transaction.complete;
  }

  async readDatabase_(minRevision, maxRevision) {
    const transaction = await this.transaction([STORE_NOTES], READONLY);
    const dataStore = transaction.objectStore(STORE_NOTES);
    const notes = [];
    let cursor = await dataStore.openCursor();
    while (cursor) {
      if (cursor.value.min_revision < maxRevision &&
          cursor.value.max_revision > minRevision) {
        notes.push(cursor.value);
      }
      cursor = await cursor.continue();
    }
    return notes;
  }

  async respond() {
    this.fetchEvent.respondWith(this.responsePromise.then(jsonResponse));
    const resultsSent = this.sendResults_();
    this.fetchEvent.waitUntil(resultsSent);
    await resultsSent;
  }

  async getResponse() {
    return [];
  }

  constructor(fetchEvent) {
    super(fetchEvent);
    this.parseRequestPromise = this.parseRequest_();
  }

  async parseRequest_() {
    this.body_ = await this.fetchEvent.request.clone().formData();
  }

  async sendResults_() {
    await this.parseRequestPromise;
    const channelName = this.fetchEvent.request.url + '?' +
      new URLSearchParams(this.body_);
    const sender = new ResultChannelSender(channelName);
    await sender.send(this.generateResults());
    this.onResponded();
  }

  generateResults() {
    return (async function* () {
      await this.parseRequestPromise;
      if (this.body_.has('text')) {
        // This request is creating or editing a note, so forward it to the
        // server as-is.
        yield await fetch(this.fetchEvent.request);
        return;
      }

      this.databaseName_ = NotesCacheRequest.databaseName({
        suite: this.body_.get('suite'),
        measurement: this.body_.get('measurement'),
        bot: this.body_.get('bot'),
        case: this.body_.get('case'),
      });
      // read all notes in the revision range.

      const minRevision = parseInt(this.body_.get('min_revision') || 0);
      const maxRevision = parseInt(
          this.body_.get('max_revision') || Number.MAX_SAFE_INTEGER);
      let notes = await this.readDatabase_(minRevision, maxRevision);

      if (notes.length) yield notes;

      // TODO early return if this range has been fetched recently.

      const notesByKey = new Map();
      for (const note of notes) {
        notesByKey.set(note.key, note);
      }

      let anyChanged = false;
      for (const note of await this.readNetwork_()) {
        if (notesByKey.has(note.key) &&
            notesByKey.get(note.key).modified === note.modified) {
          continue;
        }
        anyChanged = true;
        notesByKey.set(note.key, note);
      }
      notes = [...notesByKey.values()];

      if (anyChanged) yield notes;

      this.scheduleWrite(notes);
    }).call(this);
  }

  async readNetwork_() {
    const response = await fetch(this.fetchEvent.request);
    return await response.json();
  }

  static databaseName({suite, measurement, bot, case: cas}) {
    return `notes/${suite}/${measurement}/${bot}/${cas}`;
  }
}
