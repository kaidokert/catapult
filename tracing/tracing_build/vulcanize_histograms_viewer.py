# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import codecs

import tracing_project
from py_vulcanize import generate

from tracing_build import render_histograms_viewer


def VulcanizeHistogramsViewer(
    path=render_histograms_viewer.VULCANIZED_HISTOGRAMS_VIEWER_PATH):
  """Vulcanizes Histograms viewer with its dependencies.

  Args:
    path: destination to write the vulcanized viewer HTML.
  """
  vulcanizer = tracing_project.TracingProject().CreateVulcanizer()
  load_sequence = vulcanizer.CalcLoadSequenceForModuleNames(
      ['tracing_build.histograms_viewer'])
  html = generate.GenerateStandaloneHTMLAsString(load_sequence)
  with codecs.open(path, 'wb', encoding='utf-8') as viewer_file:
    viewer_file.write(html)
