# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import tracing_project
import vinn


_REVISION_CMD_LINE = os.path.join(
    os.path.dirname(__file__), 'get_revision_cmdline.html')

def GetRevision(filename):

  tracefile = 'file://' + filename
  project = tracing_project.TracingProject()
  all_source_paths = list(project.source_paths)
  res = vinn.RunFile(
      _REVISION_CMD_LINE, source_paths=all_source_paths, js_args=[tracefile])

  if res.returncode != 0:
    raise RuntimeError('Error running get_revision_cmdline: ' + res.stdout)
  else:
    return res.stdout
