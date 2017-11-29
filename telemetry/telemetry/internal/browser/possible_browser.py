# Copyright 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging

from telemetry.internal.app import possible_app



class PossibleBrowser(possible_app.PossibleApp):
  """A browser that can be controlled.

  Call Create() to launch the browser and begin manipulating it..
  """

  def __init__(self, browser_type, target_os, supports_tab_control):
    super(PossibleBrowser, self).__init__(app_type=browser_type,
                                          target_os=target_os)
    self._supports_tab_control = supports_tab_control

  def __repr__(self):
    return 'PossibleBrowser(app_type=%s)' % self.app_type

  @property
  def browser_type(self):
    return self.app_type

  @property
  def supports_tab_control(self):
    return self._supports_tab_control

  def _InitPlatformIfNeeded(self):
    raise NotImplementedError()

  def Create(self, finder_options):
    raise NotImplementedError()

  def SupportsOptions(self, browser_options):
    """Tests for extension support."""
    raise NotImplementedError()

  def IsRemote(self):
    return False

  def RunRemote(self):
    pass

  def UpdateExecutableIfNeeded(self):
    pass

  @property
  def last_modification_time(self):
    return -1

  def ClearCache(self, platform, browser_backend, clear_system_cache):
    platform.FlushDnsCache()
    if not clear_system_cache:
      return
    if platform.CanFlushIndividualFilesFromSystemCache():
      platform.FlushSystemCacheForDirectory(browser_backend.profile_directory)
      platform.FlushSystemCacheForDirectory(browser_backend.browser_directory)
    elif platform.SupportFlushEntireSystemCache():
      platform.FlushEntireSystemCache()
    else:
      logging.warning(
          'Flush system cache is not supported. ' +
          'Did not flush system cache.')
