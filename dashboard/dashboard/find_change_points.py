# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""A simplified change-point detection algorithm.

Historically, the performance dashboard has used the GASP service for
detection. Brett Schein wrote a simplified version of this algorithm
for the dashboard in Matlab, and this was ported to Python by Dave Tu.

The general goal is to find any increase or decrease which is likely to
represent a real change in the underlying data source.

See: http://en.wikipedia.org/wiki/Step_detection

In 2019, we also integrate a successive bisection with combined Mann-Whitney
U-test and Kolmogorov-Smirnov tests to identify potential change points. This is
not exactly the E-divisive algorithm, but is close enough.

See: https://arxiv.org/abs/1306.4933
"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import collections
import itertools
import logging
import math
import random

from dashboard import find_step
from dashboard import ttest
from dashboard.common import math_utils

# TODO(dberris): Remove this dependency if/when we are able to depend on SciPy
# instead.
from dashboard.pinpoint.models.compare import compare as pinpoint_compare

# Maximum number of points to consider at one time.
_MAX_WINDOW_SIZE = 50

# Minimum number of points in a segment. This can help filter out erroneous
# results by ignoring results that were found from looking at too few points.
MIN_SEGMENT_SIZE = 6

# Minimum absolute difference between medians before and after.
_MIN_ABSOLUTE_CHANGE = 0

# Minimum relative difference between medians before and after.
_MIN_RELATIVE_CHANGE = 0.01

# "Steppiness" is a number between 0 and 1 that indicates how similar the
# shape is to a perfect step function, where 1 represents a step function.
_MIN_STEPPINESS = 0.5

# The "standard deviation" is based on a subset of points in the series.
# This parameter is the minimum acceptable ratio of the relative change
# and this standard deviation.
_MULTIPLE_OF_STD_DEV = 2.5


class ChangePoint(
    collections.namedtuple(
        'ChangePoint',
        (
            # The x-value of the first point after a step.
            'x_value',
            # Median of the segments before and after the change point.
            'median_before',
            'median_after',
            # Number of points before and after the change point.
            'size_before',
            'size_after',
            # X-values of the first and last point in the series window used.
            'window_start',
            'window_end',
            # Relative change from before to after.
            'relative_change',
            # Standard deviation of points before.
            'std_dev_before',
            # Results of the Welch's t-test for values before and after.
            't_statistic',
            'degrees_of_freedom',
            'p_value'))):
  """A ChangePoint represents a change in a series -- a potential alert."""
  _slots = None

  def AsDict(self):
    """Returns a dictionary mapping attributes to values."""
    return self._asdict()


class Error(Exception):
  pass


class InsufficientData(Error):

  def __init__(self, message):
    super(InsufficientData, self).__init__(message)


def FindChangePoints(series,
                     max_window_size=_MAX_WINDOW_SIZE,
                     min_segment_size=MIN_SEGMENT_SIZE,
                     min_absolute_change=_MIN_ABSOLUTE_CHANGE,
                     min_relative_change=_MIN_RELATIVE_CHANGE,
                     min_steppiness=_MIN_STEPPINESS,
                     multiple_of_std_dev=_MULTIPLE_OF_STD_DEV):
  """Finds at most one change point in the given series.

  Only the last |max_window_size| points are examined, regardless of
  how many points are passed in. The reason why it might make sense to
  limit the number of points to look at is that if there are multiple
  change-points in the window that's looked at, then this function will
  be less likely to find any of them.

  First, the "most likely" split is found. The most likely split is defined as
  a split that minimizes the sum of the variances on either side. Then the
  split point is checked to see whether it passes the thresholds.

  Args:
    series: A list of (x, y) pairs.
    max_window_size: Number of points to analyze.
    min_segment_size: Min size of segments before or after change point.
    min_absolute_change: Absolute change threshold.
    min_relative_change: Relative change threshold.
    min_steppiness: Threshold for how similar to a step a change point must be.
    multiple_of_std_dev: Threshold for change as multiple of std. deviation.

  Returns:
    A list with one ChangePoint object, or an empty list.
  """
  if len(series) < 2:
    return []  # Not enough points to possibly contain a valid split point.
  series = series[-max_window_size:]
  _, y_values = zip(*series)
  split_index = _FindSplit(y_values)
  alternate_split_index = split_index
  try:
    alternate_split_index = _ClusterAndFindSplit(y_values, min_segment_size)
    logging.warning(
        'Alternative found an alternate split at index %s compared to %s (%s)',
        alternate_split_index, split_index,
        'SAME' if alternate_split_index == split_index else 'DIFFERENT')
    logging.debug(
        'Revisions found: alternate = %s (index=%s); current = %s (index=%s)',
        series[alternate_split_index][0], alternate_split_index,
        series[split_index][0], split_index)
  except InsufficientData as e:
    # TODO(dberrs): When this is the default, bail out after logging.
    logging.warning('Pinpoint based comparison failed: %s', e)
  if _PassesThresholds(
      y_values,
      split_index,
      min_segment_size=min_segment_size,
      min_absolute_change=min_absolute_change,
      min_relative_change=min_relative_change,
      min_steppiness=min_steppiness,
      multiple_of_std_dev=multiple_of_std_dev):
    return [MakeChangePoint(series, split_index)]
  return []


def MakeChangePoint(series, split_index):
  """Makes a ChangePoint object for the given series at the given point.

  Args:
    series: A list of (x, y) pairs.
    split_index: Index of the first point after the split.

  Returns:
    A ChangePoint object.
  """
  assert 0 <= split_index < len(series)
  x_values, y_values = zip(*series)
  left, right = y_values[:split_index], y_values[split_index:]
  left_median, right_median = math_utils.Median(left), math_utils.Median(right)
  ttest_results = ttest.WelchsTTest(left, right)
  return ChangePoint(
      x_value=x_values[split_index],
      median_before=left_median,
      median_after=right_median,
      size_before=len(left),
      size_after=len(right),
      window_start=x_values[0],
      window_end=x_values[-1],  # inclusive bound
      relative_change=math_utils.RelativeChange(left_median, right_median),
      std_dev_before=math_utils.StandardDeviation(left),
      t_statistic=ttest_results.t,
      degrees_of_freedom=ttest_results.df,
      p_value=ttest_results.p)


def _FindSplit(values):
  """Finds the index of the "most interesting" split of a sample of data.

  Currently, the most interesting split is considered to be the split that
  minimizes the standard deviation of the two sides concatenated together
  (after modifying both sides by shifting all the numbers in the left and
  right sides by the median of the left and right sides respectively).

  The reason why this is done is that normalizing the two segments on either
  side of a point so that both have the same center essentially removes any
  jump or step that occurs at that point.

  Args:
    values: A list of numbers.

  Returns:
    The index of the "most interesting" point.
  """

  def StdDevOfTwoNormalizedSides(index):
    left, right = values[:index], values[index:]
    return math_utils.StandardDeviation(_ZeroMedian(left) + _ZeroMedian(right))

  return min(range(1, len(values)), key=StdDevOfTwoNormalizedSides)


def _ClusterAndFindSplit(values, min_segment_size):
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

  def Cluster(sequence, partition_point):
    """Return a tuple (left, right) where partition_point is part of left."""
    cluster_a = sequence[:partition_point + 1]
    cluster_b = sequence[partition_point + 1:]
    return (cluster_a, cluster_b)

  def Midpoint(sequence):
    """Return an index in the sequence representing the midpoint."""
    return len(sequence) // 2 if len(sequence) > 2 else 0

  def RandomPermutations(sequence, length, count):
    pool = tuple(sequence)
    for i in itertools.count(0):
      if i == count:
        return
      yield tuple(random.sample(pool, length))

  def ClusterAndCompare(sequence, partition_point):
    """Returns the comparison result and the clusters at the partition point."""
    # Detect a difference between the two clusters
    cluster_a, cluster_b = Cluster(sequence, partition_point)
    magnitude = float(math_utils.Iqr(cluster_a) + math_utils.Iqr(cluster_b)) / 2
    return (pinpoint_compare.Compare(cluster_a, cluster_b,
                                     (len(cluster_a) + len(cluster_b)) // 2,
                                     'performance',
                                     magnitude), cluster_a, cluster_b)

  def PermutationTest(sequence):
    """Determine whether there's a potential change point within the sequence,

    using randomised permutation testing.
    """
    if len(sequence) < (min_segment_size * 4):
      return False

    sames = 0
    differences = 0
    unknowns = 0
    for permutation in RandomPermutations(
        sequence, Midpoint(sequence), min(100, math.factorial(len(sequence)))):
      change_point, found = ChangePointEstimator(permutation)
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

  def ChangePointEstimator(sequence):
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
      x_a = sum(
          abs(a - b)**2 for a, b in itertools.product(cluster_a, repeat=2))
      x_b = sum(
          abs(a - b)**2 for a, b in itertools.product(cluster_b, repeat=2))
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

  logging.debug('Starting change point detection.')
  length = len(values)
  if length <= min_segment_size:
    raise InsufficientData(
        'Sequence is not larger than min_segment_size (%s <= %s)' %
        (length, min_segment_size))
  partition_point, _ = ChangePointEstimator(values)
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
      if len(cluster_a) > min_segment_size and PermutationTest(cluster_a):
        partition_point, in_a = ChangePointEstimator(cluster_a)
        length = len(cluster_a)
      if len(cluster_b) > min_segment_size and PermutationTest(cluster_b):
        partition_point, in_b = ChangePointEstimator(cluster_b)
        length = len(cluster_b)
        start += max(len(cluster_a), 1) - 1
      if not in_a and not in_b:
        potential_culprit = start + partition_point
        logging.debug('Found potential change point @%s', potential_culprit)
        return potential_culprit
    elif compare_result == pinpoint_compare.SAME:
      in_a = False
      in_b = False
      if len(cluster_a) > min_segment_size and PermutationTest(cluster_a):
        partition_point, in_a = ChangePointEstimator(cluster_a)
        length = len(cluster_a)
      if len(cluster_b) > min_segment_size and PermutationTest(cluster_b):
        partition_point, in_b = ChangePointEstimator(cluster_b)
        length = len(cluster_b)
        start += max(len(cluster_a), 1) - 1
      if not in_a and not in_b:
        raise InsufficientData('Not enough data to suggest a change point.')
    else:
      potential_culprit = start + partition_point
      logging.debug('Found potential change point @%s', potential_culprit)
      return potential_culprit


def _ZeroMedian(values):
  """Subtracts the median value in the list from all values in the list."""
  median = math_utils.Median(values)
  return [val - median for val in values]


def _PassesThresholds(values, split_index, min_segment_size,
                      min_absolute_change, min_relative_change, min_steppiness,
                      multiple_of_std_dev):
  """Checks whether a point in a series appears to be an change point.

  Args:
    values: A list of numbers.
    split_index: An index in the list of numbers.
    min_segment_size: Threshold for size of segments before or after a point.
    min_absolute_change: Minimum absolute median change threshold.
    min_relative_change: Minimum relative median change threshold.
    min_steppiness: Threshold for how similar to a step a change point must be.
    multiple_of_std_dev: Threshold for change as multiple of std. deviation.

  Returns:
    True if it passes all of the thresholds, False otherwise.
  """
  left, right = values[:split_index], values[split_index:]
  left_median, right_median = math_utils.Median(left), math_utils.Median(right)

  # 1. Segment size filter.
  if len(left) < min_segment_size or len(right) < min_segment_size:
    return False

  # 2. Absolute change filter.
  absolute_change = abs(left_median - right_median)
  if absolute_change < min_absolute_change:
    return False

  # 3. Relative change filter.
  relative_change = math_utils.RelativeChange(left_median, right_median)
  if relative_change < min_relative_change:
    return False

  # 4. Multiple of standard deviation filter.
  min_std_dev = min(
      math_utils.StandardDeviation(left), math_utils.StandardDeviation(right))
  if absolute_change < multiple_of_std_dev * min_std_dev:
    return False

  # 5. Steppiness filter.
  steppiness = find_step.Steppiness(values, split_index)
  if steppiness < min_steppiness:
    return False

  # Passed all filters!
  return True
