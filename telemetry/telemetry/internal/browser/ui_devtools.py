# Copyright 2021 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.


class UIDevTools(object):

  def __init__(self, ui_devtools_backend):
    self._ui_devtools_backend = ui_devtools_backend

  def SearchNodes(self, query):
    return self._ui_devtools_backend.SearchNodes(query)

  # pylint: disable=redefined-builtin
  def DispatchMouseEvent(self,
                         node_id,
                         type='mousePressed',
                         x=0,
                         y=0,
                         button='left',
                         wheel_direction='none'):
    return self._ui_devtools_backend.DispatchMouseEvent(node_id,
                                                        type,
                                                        x,
                                                        y,
                                                        button,
                                                        wheel_direction)
