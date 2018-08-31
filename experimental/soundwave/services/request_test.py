# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import pickle
import unittest

from services import request


class TestRequestErrors(unittest.TestCase):
  def testClientErrorPickleable(self):
    error = request.ClientError(
        'api', {'status': '400'}, 'You made a bad request!')
    error = pickle.loads(pickle.dumps(error))
    self.assertIsInstance(error, request.ClientError)
    self.assertEqual(error.request, 'api')
    self.assertEqual(error.response, {'status': '400'})
    self.assertEqual(error.content, 'You made a bad request!')

  def testServerErrorPickleable(self):
    error = request.ServerError(
        'api', {'status': '500'}, 'Oops, I had a problem!')
    error = pickle.loads(pickle.dumps(error))
    self.assertIsInstance(error, request.ServerError)
    self.assertEqual(error.request, 'api')
    self.assertEqual(error.response, {'status': '500'})
    self.assertEqual(error.content, 'Oops, I had a problem!')
