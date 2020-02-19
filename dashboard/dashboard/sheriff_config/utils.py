# Copyright 2020 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
""" Commonly used utilities """

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import functools
import re
import time


# We need mocking time for testing.
def Time():
  return time.time()


def LRUCacheWithTTL(ttl_seconds=60, **lru_args):
  def Wrapper(func):
    @functools.lru_cache(**lru_args)
    # pylint: disable=unused-argument
    def Cached(ttl, *args, **kargs):
      return func(*args, **kargs)
    def Wrapping(*args, **kargs):
      ttl = int(Time()) // ttl_seconds
      return Cached(ttl, *args, **kargs)
    return Wrapping
  return Wrapper


# Modified from fnmatch.translate
# 1. * shouldn't match /
# 2. re2 doesn't support \Z
def Translate(pat):
  """Translate a shell PATTERN to a regular expression.
  There is no way to quote meta-characters.
  """

  i, n = 0, len(pat)
  res = ''
  while i < n:
    c = pat[i]
    i = i+1
    if c == '*':
      res = res + '[^/]*'
    elif c == '?':
      res = res + '[^/]'
    elif c == '[':
      j = i
      if j < n and pat[j] == '!':
        j = j+1
      if j < n and pat[j] == ']':
        j = j+1
      while j < n and pat[j] != ']':
        j = j+1
      if j >= n:
        res = res + '\\['
      else:
        stuff = pat[i:j].replace('\\', '\\\\')
        i = j+1
        if stuff[0] == '!':
          stuff = '^' + stuff[1:]
        elif stuff[0] == '^':
          stuff = '\\' + stuff
        res = '%s[%s]' % (res, stuff)
    else:
      res = res + re.escape(c)
    return res
