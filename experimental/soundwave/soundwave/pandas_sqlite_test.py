# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import pandas  # pylint: disable=import-error
import sqlite3
import unittest

from soundwave import pandas_sqlite


class TestPandasSQLite(unittest.TestCase):
  COLUMNS = ('bug_id', 'summary', 'status')
  INDEX = COLUMNS[0]

  def _ExampleDf1(self):
    return pandas.DataFrame.from_records(
        [(123, 'Some bug', 'Started'), (456, 'Another bug', 'Assigned')],
        columns=self.COLUMNS, index=self.INDEX)

  def _ExampleDf2(self):
    return pandas.DataFrame.from_records(
        [(123, 'Some bug', 'Fixed'), (789, 'A new bug', 'Untriaged')],
        columns=self.COLUMNS, index=self.INDEX)

  def testInsertOrReplaceRecords_newTable(self):
    df1 = self._ExampleDf1()
    conn = sqlite3.connect(':memory:')
    try:
      # Write new table to database, read back and check they are equal.
      pandas_sqlite.InsertOrReplaceRecords(df1, 'bugs', conn)
      df = pandas.read_sql('SELECT * FROM bugs', conn, index_col=self.INDEX)
      self.assertTrue(df.equals(df1))
    finally:
      conn.close()

  def testInsertOrReplaceRecords_existingTable(self):
    df1 = self._ExampleDf1()
    df2 = self._ExampleDf2()
    conn = sqlite3.connect(':memory:')
    try:
      # Write first data frame to database.
      pandas_sqlite.InsertOrReplaceRecords(df1, 'bugs', conn)
      df = pandas.read_sql('SELECT * FROM bugs', conn, index_col=self.INDEX)
      self.assertEqual(len(df), 2)
      self.assertEqual(df.loc[123]['status'], 'Started')

      # Write second data frame to database.
      pandas_sqlite.InsertOrReplaceRecords(df2, 'bugs', conn)
      df = pandas.read_sql('SELECT * FROM bugs', conn, index_col=self.INDEX)
      self.assertEqual(len(df), 3)  # Only one extra record added.
      self.assertEqual(df.loc[123]['status'], 'Fixed')  # Bug is now fixed.
      self.assertItemsEqual(df.index, (123, 456, 789))
    finally:
      conn.close()


if __name__ == '__main__':
  unittest.main()
