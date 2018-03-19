# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import contextlib
import os
import sqlite3


DATABASE_SCHEMA_PATH = os.path.normpath(os.path.join(
    os.path.dirname(__file__), 'schema.sql'))


class Database(object):
  def __init__(self, filename):
    """An object to hold the connection to the soundwave database.

    Use as a context manager to open/close the database, e.g.:

      with database.Database(filepath) as db:
        # do something with db

    """
    self._filename = filename
    self._conn = None
    self._put = {}

  def __enter__(self):
    """Open the database."""
    assert self._conn is None, 'Connection is already open'
    self._conn = sqlite3.connect(self._filename)
    with self.Transaction():
      with open(DATABASE_SCHEMA_PATH) as f:
        self._conn.executescript(f.read())
    return self

  def __exit__(self, *args, **kwargs):
    """Close the database."""
    assert self._conn is not None, 'Connection is already closed'
    try:
      self._conn.close()
    finally:
      self._conn = None

  @contextlib.contextmanager
  def Transaction(self):
    """A context manager to automatically commit/rollback a set of operations.

    For example:

      with db.Transaction():
        for item in items:
          db.Put(item)

    will commit once after storing all items, or rollback and not store any of
    them if an exception is raised within the context managed code.
    """
    with self._conn:
      yield

  def Put(self, item, commit=False):
    """Store a single item in the database.

    Args:
      item: The item to store, the item is updated if a row with the same
        primary key exits. The item's class provides the table information.
      commit: Whether to automatically commit after storing the item.
    """
    table = type(item)
    if table.name not in self._put:
      self._put[table.name] = 'INSERT OR REPLACE INTO %s VALUES (%s)' % (
          table.name, ','.join('?' * len(table.columns)))
    self._conn.execute(self._put[table.name], item)
    if commit:
      self._conn.commit()

  def Find(self, table, **kwargs):
    """Find an item given an exact specification.

    For example:
      alert = db.Find(models.Alert, key='key_of_some_alert')

    Args:
      table: A class for the kind of item to find.
      **kwargs: Key-value pairs where keys correspond to column names.

    Returns:
      An item (instance of table) if found, or None otherwise.
    """
    assert kwargs, 'Missing specification for the item to find.'
    keys, values = zip(*kwargs.iteritems())
    query = 'SELECT * FROM %s WHERE %s' % (
        table.name, ' AND '.join('%s=?' % k for k in keys))
    row = self._conn.execute(query, values).fetchone()
    return table.FromTuple(row) if row is not None else None

  def IterItems(self, table):
    """Iterate over all items of a given table."""
    for row in self._conn.execute('SELECT * FROM %s' % table.name):
      yield table.FromTuple(row)
