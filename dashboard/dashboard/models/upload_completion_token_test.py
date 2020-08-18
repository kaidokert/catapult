# Copyright 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import datetime
import time
import unittest
import uuid

from dashboard.common import testing_common
from dashboard.models import upload_completion_token


class UploadCompletionTokenTest(testing_common.TestCase):

  def setUp(self):
    super(UploadCompletionTokenTest, self).setUp()
    testing_common.SetIsInternalUser('foo@bar.com', True)
    self.SetCurrentUser('foo@bar.com', is_admin=True)

  def testPutAndUpdate(self):
    token_id = str(uuid.uuid4())
    gcs_file = 'path/%s.gcs' % str(uuid.uuid4())
    creation_time = datetime.datetime.now()
    token = upload_completion_token.Token(
        id=token_id, temporary_staging_file_path=gcs_file).put().get()

    max_delta = datetime.timedelta(seconds=1)

    self.assertEqual(token_id, token.key.id())
    self.assertEqual(gcs_file, token.temporary_staging_file_path)
    self.assertTrue((token.creation_time - creation_time) < max_delta)
    self.assertTrue((token.update_time - creation_time) < max_delta)
    self.assertEqual(token.state, upload_completion_token.State.PENDING)

    # Sleep for 1 second, so update_time change is visible.
    time.sleep(1)

    new_state = upload_completion_token.State.PROCESSING
    token.UpdateStateAsync(new_state).wait()

    changed_token = upload_completion_token.Token.get_by_id(token_id)
    self.assertEqual(token_id, changed_token.key.id())
    self.assertEqual(gcs_file, changed_token.temporary_staging_file_path)
    self.assertTrue((changed_token.creation_time - creation_time) < max_delta)
    self.assertTrue((changed_token.update_time - creation_time) > max_delta)
    self.assertEqual(changed_token.state, new_state)

    new_state = upload_completion_token.State.COMPLETED
    upload_completion_token.Token.UpdateStateById(token_id, new_state)

    changed_token = upload_completion_token.Token.get_by_id(token_id)
    self.assertEqual(changed_token.state, new_state)

  def testStatusUpdateWithMeasurements(self):
    token_id = str(uuid.uuid4())
    token = upload_completion_token.Token(id=token_id).put().get()

    self.assertEqual(token.state, upload_completion_token.State.PENDING)

    measurement1 = token.CreateMeasurement('test/1')
    measurement2 = token.CreateMeasurement('test/2')
    self.assertEqual(token.state, upload_completion_token.State.PROCESSING)

    token.UpdateStateAsync(upload_completion_token.State.PROCESSING).wait()
    self.assertEqual(token.state, upload_completion_token.State.PROCESSING)

    measurement1.UpdateStateAsync(upload_completion_token.State.FAILED).wait()
    self.assertEqual(token.state, upload_completion_token.State.PROCESSING)

    token.UpdateStateAsync(upload_completion_token.State.COMPLETED).wait()
    measurement2.UpdateStateAsync(
        upload_completion_token.State.COMPLETED).wait()
    self.assertEqual(token.state, upload_completion_token.State.FAILED)

    measurement1.UpdateStateAsync(
        upload_completion_token.State.COMPLETED).wait()
    self.assertEqual(token.state, upload_completion_token.State.COMPLETED)

  def testUpdateNonexistentToken(self):
    token_id = str(uuid.uuid4())
    upload_completion_token.Token.UpdateStateById(
        None, upload_completion_token.State.COMPLETED)
    upload_completion_token.Token.UpdateStateById(
        token_id, upload_completion_token.State.COMPLETED)

  def testStatusUpdateWithExpiredMeasurement(self):
    token_id = str(uuid.uuid4())
    token = upload_completion_token.Token(id=token_id).put().get()
    measurement1 = token.CreateMeasurement('test/1')
    measurement2 = token.CreateMeasurement('test/2')

    measurement1.key.delete()

    self.assertEqual(token.state, upload_completion_token.State.PROCESSING)

    token.UpdateStateAsync(upload_completion_token.State.PROCESSING).wait()
    self.assertEqual(token.state, upload_completion_token.State.PROCESSING)

    measurement2.UpdateStateAsync(
        upload_completion_token.State.COMPLETED).wait()
    self.assertEqual(token.state, upload_completion_token.State.COMPLETED)


if __name__ == '__main__':
  unittest.main()
