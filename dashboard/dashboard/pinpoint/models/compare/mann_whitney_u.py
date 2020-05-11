# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Pure Python implementation of the Mann-Whitney U test.

This code is adapted from SciPy:
  https://github.com/scipy/scipy/blob/master/scipy/stats/stats.py
Which is provided under a BSD-style license.

There is also a JavaScript version in Catapult:
  https://github.com/catapult-project/catapult/blob/master/tracing/third_party/mannwhitneyu/mannwhitneyu.js
"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import itertools
import math

# DO NOT SUBMIT
# This is an experiment to use numpy in these computations.
import numpy as np

def MannWhitneyU(x, y):
  """Computes the Mann-Whitney rank test on samples x and y.

  The distribution of U is approximately normal for large samples. This
  implementation uses the normal approximation, so it's recommended to have
  sample sizes > 20.
  """
  n1 = len(x)
  n2 = len(y)
  a = np.concatenate((x, y), axis=None)
  ranked = _RankData(a)
  rankx = ranked[0:n1]  # get the x-ranks
  u1 = n1*n2 + n1*(n1+1)/2.0 - np.sum(rankx)  # calc U for x
  u2 = n1*n2 - u1  # remainder is U for y
  t = _TieCorrectionFactor(ranked)
  if t == 0:
    return 1.0
  sd = math.sqrt(t * n1 * n2 * (n1+n2+1) / 12.0)

  mean_rank = n1*n2/2.0 + 0.5
  big_u = max(u1, u2)

  z = (big_u - mean_rank) / sd
  return 2 * _NormSf(abs(z))


def _RankData(a):
  """Assigns ranks to data. Ties are given the mean of the ranks of the items.

  This is called "fractional ranking":
    https://en.wikipedia.org/wiki/Ranking
  """
  ranked_max = np.argsort(-a)
  ranked_min = np.argsort(a)[::-1]

  pairwise = np.concatenate(
      (ranked_min.reshape(-1, 1), ranked_max.reshape(-1, 1)), 1)
  average_rank = np.sum(pairwise, axis=1) / 2.0
  result = np.ones(len(a)) + average_rank
  return result


def _TieCorrectionFactor(rankvals):
  """Tie correction factor for ties in the Mann-Whitney U test."""
  _, counts = np.unique(rankvals, return_counts=True)
  size = len(rankvals)
  if size < 2:
    return 1.0
  else:
    return 1.0 - (np.sum(counts**3 - counts) / float(size**3 - size))


def _NormSf(x):
  """Survival function of the standard normal distribution. (1 - cdf)"""
  return (1 - math.erf(x/math.sqrt(2))) / 2
