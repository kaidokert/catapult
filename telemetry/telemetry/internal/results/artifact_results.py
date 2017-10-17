# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import collections

class ArtifactResults(object):
  def __init__(self):
    self._page_run_artifacts = collections.defaultdict(dict)

  def AddArtifactFromPageRun(self, page, artifact, reason):
    self._page_run_artifacts[page.name][reason] = artifact

  def AddArtifactFromTestRun(self, page, artifact, reason):
    pass
