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

  @contextlib.contextmanager
  def BrowserSession(self, browser_options):
    try:
      self.SetUpEnvironment(browser_options)
      browser = self.Create()
      try:
        yield browser
      finally:
        browser.Close()
    finally:
      self.CleanUpEnvironment()

  def SetUpEnvironment(self, browser_options):
    # TODO(crbug.com/801578): Make this a strict check after all clients
    # make sure of cleaning up the environment after themselves.
    if self._browser_options is not None:
      logging.warning(
          'Browser environment was not cleaned up, make sure to update the '
          'client creating this browser. See crbug.com/801578 for details.')
    # Check we were called with browser_options and not finder_options.
    assert getattr(browser_options, 'IS_BROWSER_OPTIONS', False)
    self._browser_options = browser_options

  def Create(self, finder_options=None):
    # TODO(crbug.com/801578): Remove finder_options arg when all clients
    # have switched to the new API.
    raise NotImplementedError()

  def CleanUpEnvironment(self):
    # Subclasses should take into account that this method may be called
    # even if SetUpEnvironment was not called, or was only partially executed
    # due to exceptions.
    self._browser_options = None

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
