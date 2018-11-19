# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""
Helper methods for dealing with a SQLite database with pandas.
"""
import pandas  # pylint: disable=import-error


def EmptyFrame(column_types, index=None):
  df = pandas.DataFrame()
  for column, dtype in column_types:
    df[column] = pandas.Series(dtype=dtype)
  if index is not None:
    if not isinstance(index, basestring):
      index = list(index)
    df.set_index(index, inplace=True)
  return df


def CreateTableIfNotExists(con, name, frame):
  """Create a new empty table, if it doesn't already exist.

  Args:
    con: A sqlite connection object.
    name: Name of SQL table to create.
    frame: A DataFrame from which to infer the table schema, the index columns
      of the frame, if any, are set as PRIMARY KEY of the table.
  """
  keys = [k for k in frame.index.names if k is not None]
  print keys
  if not keys:
    keys = None
  db = pandas.io.sql.SQLiteDatabase(con)
  table = pandas.io.sql.SQLiteTable(
      name, db, frame=frame.reset_index(), index=False, keys=keys,
      if_exists='append')
  table.create()


def _InsertOrReplaceStatement(name, keys):
  columns = ','.join(keys)
  values = ','.join('?' for _ in keys)
  return 'INSERT OR REPLACE INTO %s(%s) VALUES (%s)' % (name, columns, values)


def InsertOrReplaceRecords(con, name, frame):
  """Insert or replace records from a DataFrame into a SQLite database.

  Assumes that the table already exists. Any new records with a matching
  PRIMARY KEY, usually the frame.index, will replace existing records.

  Args:
    con: A sqlite connection object.
    name: Name of SQL table.
    frame: DataFrame with records to write.
  """
  db = pandas.io.sql.SQLiteDatabase(con)
  table = pandas.io.sql.SQLiteTable(
      name, db, frame=frame, index=True, if_exists='append')
  assert table.exists()
  keys, data = table.insert_data()
  insert_statement = _InsertOrReplaceStatement(name, keys)
  with db.run_transaction() as c:
    c.executemany(insert_statement, zip(*data))
