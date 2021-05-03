# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# The pylint in use is a older version that will consider using io.open() as
# refining builtin functions. This is fixed in a lower version:
#   https://github.com/PyCQA/pylint/issues/464
# For now, we will skip the check for python 3 conversion.
from io import open  # pylint: disable=redefined-builtin

class SystemStubTest(object):
  @staticmethod
  def TestOpen(file_path):
    return open(file_path)
