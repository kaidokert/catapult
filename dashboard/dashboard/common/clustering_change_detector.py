# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""An approximation of the E-Divisive change detection algorithm.

This module implements the constituent functions and components for a change
detection module for time-series data. It derives heavily from the paper [0] on
E-Divisive using hierarchical significance testing and the Euclidean
distance-based divergence estimator.

[0]: https://arxiv.org/abs/1306.4933
"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import itertools
import math
import logging
import random

from dashboard.common import math_utils

# TODO(dberris): Remove this dependency if/when we are able to depend on SciPy
# instead.
from dashboard.pinpoint.models.compare import compare as pinpoint_compare


class Error(Exception):
  pass


class InsufficientData(Error):
  pass


def Cluster(sequence, partition_point):
  """Return a tuple (left, right) where partition_point is part of left."""
  cluster_a = sequence[:partition_point + 1]
  cluster_b = sequence[partition_point + 1:]
  return (cluster_a, cluster_b)


def Midpoint(sequence):
  """Return an index in the sequence representing the midpoint."""
  return len(sequence) // 2 if len(sequence) > 2 else 0


def ClusterAndCompare(sequence, partition_point):
  """Returns the comparison result and the clusters at the partition point."""
  # Detect a difference between the two clusters
  cluster_a, cluster_b = Cluster(sequence, partition_point)
  magnitude = float(math_utils.Iqr(cluster_a) + math_utils.Iqr(cluster_b)) / 2
  return (pinpoint_compare.Compare(cluster_a, cluster_b,
                                   (len(cluster_a) + len(cluster_b)) // 2,
                                   'performance',
                                   magnitude), cluster_a, cluster_b)


def PermutationTest(sequence, min_segment_size):
  """Run permutation testing on a sequence.

  Determine whether there's a potential change point within the sequence,
  using randomised permutation testing.
  """
  if len(sequence) < (min_segment_size * 4):
    return False

  def RandomPermutations(sequence, length, count):
    pool = tuple(sequence)
    for i in itertools.count(0):
      if i == count:
        return
      yield tuple(random.sample(pool, length))

  sames = 0
  differences = 0
  unknowns = 0
  for permutation in RandomPermutations(sequence, Midpoint(sequence),
                                        min(100,
                                            math.factorial(len(sequence)))):
    change_point, found = ChangePointEstimator(permutation, min_segment_size)
    if not found:
      continue
    compare_result = ClusterAndCompare(permutation, change_point)
    if compare_result == pinpoint_compare.SAME:
      sames += 1
    elif compare_result == pinpoint_compare.UNKNOWN:
      unknowns += 1
    else:
      differences += 1

  # If at least 5% of the permutations compare differently, then it passes the
  # permutation test (meaning we can detect a potential change-point in the
  # sequence).
  probability = float(differences) / float(sames + unknowns + differences)
  logging.debug('Computed probability: %s for sequence %s', probability,
                sequence)
  return probability >= 0.05


def ChangePointEstimator(sequence, min_segment_size):
  # This algorithm does the following:
  #   - For each element in the sequence:
  #     - Partition the sequence into two clusters (X[a], X[b])
  #     - Compute the intra-cluster distances squared (X[n])
  #     - Scale the intra-cluster distances by the number of intra-cluster
  #       pairs. (X'[n] = X[n] / combinations(|X[n]|, 2) )
  #     - Compute the inter-cluster distances squared (Y)
  #     - Scale the inter-cluster distances by the number of total pairs
  #       multiplied by 2 (Y' = (Y * 2) / |X[a]||X[b]|)
  #     - Sum up as: Y' - X'[a] - X'[b]
  #   - Return the index of the highest estimator.
  #
  # The computation is based on Euclidean distances between measurements
  # within and across clusters to show the likelihood that the values on
  # either side of a sequence is likely to show a divergence.
  #
  # This algorithm is O(N^2) to the size of the sequence.
  def Estimator(index):
    cluster_a, cluster_b = Cluster(sequence, index)
    x_a = sum(abs(a - b)**2 for a, b in itertools.product(cluster_a, repeat=2))
    x_b = sum(abs(a - b)**2 for a, b in itertools.product(cluster_b, repeat=2))
    y = sum(abs(a - b)**2 for a, b in itertools.product(cluster_a, cluster_b))
    a_len_combinations = (
        math.factorial(len(cluster_a)) /
        (math.factorial(2) * math.factorial(len(cluster_a) - 2)))
    b_len_combinations = (
        math.factorial(len(cluster_b)) /
        (math.factorial(2) * math.factorial(len(cluster_b) - 2)))
    return (((y * 2.0) / (len(cluster_a) * len(cluster_b))) -
            (x_a / a_len_combinations) - (x_b / b_len_combinations))

  estimates = [
      Estimator(i)
      for i, _ in enumerate(sequence)
      if min_segment_size < i < len(sequence) - min_segment_size
  ]
  if not estimates:
    return (0, False)
  max_estimate = max(estimates)
  try:
    index = estimates.index(max_estimate)
  except ValueError:
    return (0, False)
  return (index + min_segment_size, True)


def ClusterAndFindSplit(values, min_segment_size):
  """Finds an index where we can identify a significant change.

  This algorithm looks for the point at which clusterings of the "left" and
  "right" datapoints show a significant difference. We understand that this
  algorithm is working on potentially already-aggregated data (means, etc.) and
  it would work better if we had access to all the underlying data points, but
  for now we can do our best with the points we have access to.

  This works by successive bisection, first by segmenting the series into two
  clusters first down the middle of the range. If we find that the left and
  right clusters have a statistically significant difference, then we'll refine
  the clustering until we can find a single point where we can have a high
  confidence that this point is a change point.

  In the E-Divisive paper, this is a two-step process: first estimate potential
  change points through bisection, then test whether the clusters partitioned by
  the proposed change point internally has potentially hidden change-points
  through random permutation testing. Because the current implementation only
  returns a single change-point, we do the change point estimation through
  bisection, and use the permutation testing to identify whether we should
  continue the bisection, not to find all potential change points.
  """

  logging.debug('Starting change point detection.')
  length = len(values)
  if length <= min_segment_size:
    raise InsufficientData(
        'Sequence is not larger than min_segment_size (%s <= %s)' %
        (length, min_segment_size))
  partition_point, _ = ChangePointEstimator(values, min_segment_size)
  start = 0
  while True:
    logging.debug('Values for start = %s, length = %s, partition_point = %s',
                  start, length, partition_point)
    compare_result, cluster_a, cluster_b = ClusterAndCompare(
        values[start:length], partition_point)
    if compare_result == pinpoint_compare.DIFFERENT:
      logging.debug('Found partition point: %s', partition_point)
      logging.debug('Attempting to refine with permutation testing.')
      in_a = False
      in_b = False
      if len(cluster_a) > min_segment_size and PermutationTest(
          cluster_a, min_segment_size):
        partition_point, in_a = ChangePointEstimator(cluster_a,
                                                     min_segment_size)
        length = len(cluster_a)
      if len(cluster_b) > min_segment_size and PermutationTest(
          cluster_b, min_segment_size):
        partition_point, in_b = ChangePointEstimator(cluster_b,
                                                     min_segment_size)
        length = len(cluster_b)
        start += max(len(cluster_a), 1) - 1
      if not in_a and not in_b:
        potential_culprit = start + partition_point
        logging.debug('Found potential change point @%s', potential_culprit)
        return potential_culprit
    elif compare_result == pinpoint_compare.SAME:
      in_a = False
      in_b = False
      if len(cluster_a) > min_segment_size and PermutationTest(
          cluster_a, min_segment_size):
        partition_point, in_a = ChangePointEstimator(cluster_a,
                                                     min_segment_size)
        length = len(cluster_a)
      if len(cluster_b) > min_segment_size and PermutationTest(
          cluster_b, min_segment_size):
        partition_point, in_b = ChangePointEstimator(cluster_b,
                                                     min_segment_size)
        length = len(cluster_b)
        start += max(len(cluster_a), 1) - 1
      if not in_a and not in_b:
        raise InsufficientData('Not enough data to suggest a change point.')
    else:
      potential_culprit = start + partition_point
      logging.debug('Found potential change point @%s', potential_culprit)
      return potential_culprit
