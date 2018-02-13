# Copyright 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging

from telemetry.internal.browser import possible_browser


class PossibleChromeBrowser(possible_browser.PossibleBrowser):
  """Base class for possible chrome browsers."""

  def Create(self):
    # Added for pylint to figure out that this is an abstract class.
    raise NotImplementedError()

  def _GetPathsForOsPageCacheFlushing(self):
    """Return paths whose OS page cache should be flushed.

    For convenience, it's OK to return paths that resolve to None, those will
    be excluded.
    """
    return [self.profile_directory, self.browser_directory]

  def FlushOsPageCaches(self):
    """Clear OS page caches on file paths related to the browser.

    Note: this is done with best effort and may have no actual effects on the
    system.
    """
    paths_to_flush = [
        p for p in self._GetPathsForOsPageCacheFlushing() if p is not None]
    if (self.platform.CanFlushIndividualFilesFromSystemCache() and
        paths_to_flush):
      for path in paths_to_flush:
        self.platform.FlushSystemCacheForDirectory(path)
    elif self.platform.SupportFlushEntireSystemCache():
      self.platform.FlushEntireSystemCache()
    else:
      logging.warning(
          'Flush system cache is not supported. Did not flush OS page cache.')

  def _ClearCachesOnStart(self):
    """Clear DNS caches and OS page caches if the corresponding option is set.

    TODO(crbug.com/811244): Cache clearing decisions should me moved to the
    shared state and this method removed.
    """
    self.platform.FlushDnsCache()
    if self._browser_options.clear_sytem_cache_for_browser_and_profile_on_start:
      self.FlushOsPageCaches()
