# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging


def ClearCaches(platform, clear_system_cache,
                browser_profile_directory, browser_directory):
  """ Clear system caches related to browser.

  This clear DNS caches, then clear caches on file paths that are related to
  the browser.

  Notes that this is done with best effort and may have no actual effects on
  the system.
  """
  platform.FlushDnsCache()
  if not clear_system_cache:
    return
  if platform.CanFlushIndividualFilesFromSystemCache():
    platform.FlushSystemCacheForDirectory(browser_profile_directory)
    platform.FlushSystemCacheForDirectory(browser_directory)
  elif platform.SupportFlushEntireSystemCache():
    platform.FlushEntireSystemCache()
  else:
    logging.warning(
        'Flush system cache is not supported. Did not flush system cache.')
