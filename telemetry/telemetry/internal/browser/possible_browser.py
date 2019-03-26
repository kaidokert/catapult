# Copyright 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import contextlib
import logging

from telemetry.internal.app import possible_app


class PossibleBrowser(possible_app.PossibleApp):
  """A browser that can be controlled.

  Clients are responsible for setting up the environment for the browser before
  creating it, and cleaning it up when done with it. Namely:

    try:
      possible_browser.SetUpEnvironment(browser_options)
      browser = possible_browser.Create()
      try:
        # Do something with the browser.
      finally:
        browser.Close()
    finally:
      possible_browser.CleanUpEnvironment()

  Or, if possible, just:

    with possible_browser.BrowserSession(browser_options) as browser:
      # Do something with the browser.
  """

  def __init__(self, browser_type, target_os, supports_tab_control):
    super(PossibleBrowser, self).__init__(app_type=browser_type,
                                          target_os=target_os)
    self._supports_tab_control = supports_tab_control
    self._browser_options = None

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

  def _GetPathsForOsPageCacheFlushing(self):
    """Clients should return a list paths for OS page cache flushing.

    For convenience, it's OK to include paths in the list that resolve to
    None, those will be ignored.
    """
    raise NotImplementedError()

  def FlushOsPageCaches(self):
    """Clear OS page caches on file paths related to the browser.

    Note: this is done with best effort and may have no actual effects on the
    system.
    """
    paths_to_flush = [
        p for p in self._GetPathsForOsPageCacheFlushing() if p is not None]
    if (self.platform.CanFlushIndividualFilesFromSystemCache() and
        paths_to_flush):
      self.platform.FlushSystemCacheForDirectories(paths_to_flush)
    elif self.platform.SupportFlushEntireSystemCache():
      self.platform.FlushEntireSystemCache()
    else:
      logging.warning(
          'Flush system cache is not supported. Did not flush OS page cache.')

  @contextlib.contextmanager
  def BrowserSession(self, browser_options, log_verbose_browser_info=True):
    try:
      self.SetUpEnvironment(browser_options,
                            log_details=log_verbose_browser_info)
      browser = self.Create(log_verbose_browser_info)
      try:
        yield browser
      finally:
        browser.Close()
    finally:
      self.CleanUpEnvironment()

  def SetUpEnvironment(self, browser_options, log_details=True):
    del log_details
    assert self._browser_options is None, (
        'Browser environment is already set up.')
    # Check we were called with browser_options and not finder_options.
    assert getattr(browser_options, 'IS_BROWSER_OPTIONS', False)
    self._browser_options = browser_options

  def Create(self, log_verbose_browser_info=True):
    """Start the browser process.

    Args:
      log_verbose_browser_info: If True, log verbose and exceptionally long
        details about the browser (such as startup commandline which may
        contain Finch feature flags).
    """
    raise NotImplementedError()

  def CleanUpEnvironment(self):
    if self._browser_options is None:
      return  # No environment to clean up.
    try:
      self._TearDownEnvironment()
    finally:
      self._browser_options = None

  def _TearDownEnvironment(self):
    # Subclasses may override this method to perform any needed clean up
    # operations on the environment. It won't be called if the environment
    # has already been cleaned up or never set up, but may be called even if
    # SetUpEnvironment was only partially executed due to exceptions.
    pass

  def SupportsOptions(self, browser_options):
    """Tests for extension support."""
    raise NotImplementedError()

  def UpdateExecutableIfNeeded(self):
    pass

  @property
  def last_modification_time(self):
    return -1
