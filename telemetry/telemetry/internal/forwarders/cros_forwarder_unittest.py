# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest

from telemetry.internal.forwarders import cros_forwarder


# pylint: disable=protected-access
class ForwardingArgsTest(unittest.TestCase):

  def testForwardingArgs(self):
    # TODO: FIXME
    forwarding_args = cros_forwarder.CrOsSshForwarder._ForwardingArgs(
        local_port=111, remote_port=222, reverse=False)
    self.assertEqual(['-R222:127.0.0.1:111'], forwarding_args)

  def testForwardingArgsReverse(self):
    # TODO: FIXME
    forwarding_args = cros_forwarder.CrOsSshForwarder._ForwardingArgs(
        local_port=111, remote_port=222, reverse=True)
    self.assertEqual(['-L111:127.0.0.1:222'], forwarding_args)
