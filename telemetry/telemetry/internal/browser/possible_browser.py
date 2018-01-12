# Copyright 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import contextlib

from telemetry.internal.app import possible_app
from telemetry.internal.browser import browser_options as b_options


class PossibleBrowser(possible_app.PossibleApp):
  """A browser that can be controlled.

  Clients should set up the environment for the browser before creating it,
  namely:

    try:
      possible_browser.SetUpEnvironment(browser_options)
      browser = self.Create()
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
    assert self._browser_options is None, (
        'Browser environment has already been set up.')
    assert isinstance(browser_options, b_options.BrowserOptions)
    self._browser_options = browser_options

  def Create(self, finder_options=None):
    # TODO(crbug.com/787834): Remove finder_options arg when all clients
    # make sure to call SetUpEnvironment instead.
    raise NotImplementedError()

  def CleanUpEnvironment(self):
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
