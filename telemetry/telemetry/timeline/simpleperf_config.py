# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

class SimpleperfConfig(object):
  """Stores configuration options specific to simpleperf.

    profile_process: Name of the process to profiles ('browser' or 'renderer')
    profile_thread: Name of the thread to profiles ('main' or 'compositor')
    sample_frequency: Frequency of profiling samples, in samples per second.
  """
  def __init__(self):
    self.profile_process = ''
    self.profile_thread = ''
    self.sample_frequency = 0
