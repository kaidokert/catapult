# Copyright 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
class TabList(object):
  def __init__(self, tab_list_backend):
    self._tab_list_backend = tab_list_backend

  # |tab_type| can be TAB_IN_CURRENT_WINDOW or TAB_IN_NEW_POPUP
  def New(self, tab_type="TAB_IN_CURRENT_WINDOW", timeout=300):
    return self._tab_list_backend.New(tab_type, timeout)

  def __iter__(self):
    return self._tab_list_backend.__iter__()

  def __len__(self):
    return self._tab_list_backend.__len__()

  def __getitem__(self, index):
    return self._tab_list_backend.__getitem__(index)

  def GetTabById(self, identifier):
    """The identifier of a tab can be accessed with tab.id."""
    return self._tab_list_backend.GetTabById(identifier)

