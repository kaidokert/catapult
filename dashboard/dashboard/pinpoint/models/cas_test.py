# Copyright 2021 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import datetime

import mock

from google.appengine.ext import ndb

from dashboard.pinpoint.models.change import change_test
from dashboard.pinpoint.models import cas
from dashboard.pinpoint import test


class CASReferenceTest(test.TestCase):

  def testPutAndGet(self):
    cas_references = (
        ('Mac Builder Perf', change_test.Change(1), 'target_name',
         'https://isolate.server', '7c7e90be'),
        ('Mac Builder Perf', change_test.Change(2), 'target_name',
         'https://isolate.server', '38e2f262'),
    )
    cas.Put(cas_references)

    cas_instance, cas_digest = cas.Get('Mac Builder Perf',
                                       change_test.Change(1),
                                       'target_name')
    self.assertEqual(cas_instance, 'https://isolate.server')
    self.assertEqual(cas_digest, '7c7e90be')

  def testUnknownCASReference(self):
    with self.assertRaises(KeyError):
      cas.Get('Wrong Builder', change_test.Change(1), 'target_name')

  @mock.patch.object(cas, 'datetime')
  def testExpiredCASReference(self, mock_datetime):
    cas_references = (('Mac Builder Perf', change_test.Change(1), 'target_name',
                       'https://isolate.server', '7c7e90be'),)
    cas.Put(cas_references)

    # Teleport to the future after the isolate is expired.
    mock_datetime.datetime.utcnow.return_value = (
        datetime.datetime.utcnow() + cas.CAS_EXPIRY_DURATION +
        datetime.timedelta(days=1))
    mock_datetime.timedelta = datetime.timedelta

    with self.assertRaises(KeyError):
      cas.Get('Mac Builder Perf', change_test.Change(1), 'target_name')

  def testDeleteExpiredCASReference(self):
    cas_references = (
        ('Mac Builder Perf', change_test.Change(0), 'target_name',
         'https://isolate.server', '123'),
        ('Mac Builder Perf', change_test.Change(1), 'target_name',
         'https://isolate.server', '456'),
    )
    cas.Put(cas_references)

    cur = ndb.Key(
        'CASReference',
        cas._Key('Mac Builder Perf', change_test.Change(0),
                 'target_name')).get()
    cur.created = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
    cur.put()

    cur = ndb.Key(
        'CASReference',
        cas._Key(cas_references[1][0], cas_references[1][1],
                 cas_references[1][2])).get()
    cur.created = datetime.datetime.utcnow() - (
        cas.CAS_EXPIRY_DURATION + datetime.timedelta(hours=1))
    cur.put()

    cas.DeleteExpiredCASReference()

    q = cas.CASReference.query()
    refs = q.fetch()

    self.assertEqual(1, len(refs))
    self.assertEqual('123', refs[0].cas_digest)
