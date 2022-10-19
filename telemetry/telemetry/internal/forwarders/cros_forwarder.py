# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import

from telemetry.internal.forwarders import linux_based_forwarder



class CrOsForwarderFactory(linux_based_forwarder.LinuxBasedForwarderFactory):
  pass


class CrOsSshForwarder(linux_based_forwarder.LinuxBasedSshForwarder):
  pass

