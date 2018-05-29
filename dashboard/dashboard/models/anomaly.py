# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""The database model for an "Anomaly", which represents a step up or down."""

import sys

from google.appengine.ext import ndb

from dashboard.common import utils
from dashboard.models import internal_only_model
from dashboard.models import sheriff as sheriff_module

# A string to describe the magnitude of a change from zero to non-zero.
FREAKIN_HUGE = 'zero-to-nonzero'

# Possible improvement directions for a change. An Anomaly will always have a
# direction of UP or DOWN, but a test's improvement direction can be UNKNOWN.
UP, DOWN, UNKNOWN = (0, 1, 4)

INVALID_BUG_ID = -1000


class Anomaly(internal_only_model.InternalOnlyModel):
  """Represents a change-point or step found in the data series for a test.

  An Anomaly can be an upward or downward change, and can represent an
  improvement or a regression.
  """
  # Whether the alert should only be viewable by internal users.
  internal_only = ndb.BooleanProperty(indexed=True, default=False)

  # The time the alert fired.
  timestamp = ndb.DateTimeProperty(indexed=True, auto_now_add=True)

  # Note: -1 denotes an invalid alert and -2 an ignored alert.
  # By default, this is None, which denotes a non-triaged alert.
  # Do not set this to INVALID_BUG_ID; that would break GetAll().
  bug_id = ndb.IntegerProperty(indexed=True)

  # The sheriff rotation that should handle this alert.
  sheriff = ndb.KeyProperty(kind=sheriff_module.Sheriff, indexed=True)

  # Each Alert is related to one Test.
  test = ndb.KeyProperty(indexed=True)

  # We'd like to be able to query Alerts by Master, Bot, and Benchmark names.
  master_name = ndb.ComputedProperty(
      lambda self: utils.TestPath(self.test).split('/')[0],
      indexed=True)
  bot_name = ndb.ComputedProperty(
      lambda self: utils.TestPath(self.test).split('/')[1],
      indexed=True)
  benchmark_name = ndb.ComputedProperty(
      lambda self: utils.TestPath(self.test).split('/')[2],
      indexed=True)

  # Each Alert has a revision range it's associated with; however,
  # start_revision and end_revision could be the same.
  start_revision = ndb.IntegerProperty(indexed=True)
  end_revision = ndb.IntegerProperty(indexed=True)

  # The revisions to use for display, if different than point id.
  display_start = ndb.IntegerProperty(indexed=False)
  display_end = ndb.IntegerProperty(indexed=False)

  # Ownership data, mapping e-mails to the benchmark's owners' emails and
  # component as the benchmark's Monorail component
  ownership = ndb.JsonProperty()

  # The number of points before and after this anomaly that were looked at
  # when finding this anomaly.
  segment_size_before = ndb.IntegerProperty(indexed=False)
  segment_size_after = ndb.IntegerProperty(indexed=False)

  # The medians of the segments before and after the anomaly.
  median_before_anomaly = ndb.FloatProperty(indexed=False)
  median_after_anomaly = ndb.FloatProperty(indexed=False)

  # The standard deviation of the segments before the anomaly.
  std_dev_before_anomaly = ndb.FloatProperty(indexed=False)

  # The number of points that were used in the before/after segments.
  # This is also  returned by FindAnomalies
  window_end_revision = ndb.IntegerProperty(indexed=False)

  # In order to estimate how likely it is that this anomaly is due to noise,
  # t-test may be performed on the points before and after. The t-statistic,
  # degrees of freedom, and p-value are potentially-useful intermediary results.
  t_statistic = ndb.FloatProperty(indexed=False)
  degrees_of_freedom = ndb.FloatProperty(indexed=False)
  p_value = ndb.FloatProperty(indexed=False)

  # Whether this anomaly represents an improvement; if false, this anomaly is
  # considered to be a regression.
  is_improvement = ndb.BooleanProperty(indexed=True, default=False)

  # Whether this anomaly recovered (i.e. if this is a step down, whether there
  # is a corresponding step up later on, or vice versa.)
  recovered = ndb.BooleanProperty(indexed=True, default=False)

  # If the TestMetadata alerted upon has a ref build, store the ref build.
  ref_test = ndb.KeyProperty(indexed=False)

  # The corresponding units from the TestMetaData entity.
  units = ndb.StringProperty(indexed=False)

  recipe_bisects = ndb.KeyProperty(repeated=True, indexed=False)
  pinpoint_bisects = ndb.StringProperty(repeated=True, indexed=False)

  @property
  def percent_changed(self):
    """The percent change from before the anomaly to after."""
    if self.median_before_anomaly == 0.0:
      return sys.float_info.max
    difference = self.median_after_anomaly - self.median_before_anomaly
    return 100 * difference / self.median_before_anomaly

  @property
  def absolute_delta(self):
    """The absolute change from before the anomaly to after."""
    return self.median_after_anomaly - self.median_before_anomaly

  @property
  def direction(self):
    """Whether the change is numerically an increase or decrease."""
    if self.median_before_anomaly < self.median_after_anomaly:
      return UP
    return DOWN

  @classmethod
  @ndb.tasklet
  def GetAll(cls,
             internal_only=None,
             bug_id=INVALID_BUG_ID,
             sheriff=None,
             is_improvement=None,
             recovered=None,
             test=None,
             master_name=None,
             bot_name=None,
             benchmark_name=None,
             inequality_property_name=None,
             min_start_revision=None,
             max_start_revision=None,
             min_end_revision=None,
             max_end_revision=None,
             min_timestamp=None,
             max_timestamp=None,
             limit=None):
    """Query for entities generally and efficiently.

    Users should be able to filter by any and all properties generally.
    There are enough properties that it is too cumbersome to maintain sufficient
    indexes to support every possible style of query. A single index over all
    properties is used instead, which requires all queries to filter by all
    properties. This classmethod encapsulates that complex process of specifying
    all properties correctly.
    """
    # The query must filter by all properties in order to hit the single index.
    # If the caller does not specify a property, then "filter" such that that
    # property != None, which should match all entities.
    query = cls.query()

    if internal_only is None:
      query = query.filter(cls.internal_only != None)
    else:
      query = query.filter(cls.internal_only == internal_only)

    if bug_id is INVALID_BUG_ID:
      query = query.filter(cls.bug_id != INVALID_BUG_ID)
    else:
      query = query.filter(cls.bug_id == bug_id)

    if sheriff is None:
      query = query.filter(cls.sheriff != None)
    else:
      query = query.filter(cls.sheriff == sheriff)

    if test is None:
      query = query.filter(cls.test != None)
    else:
      query = query.filter(cls.test == test)

    if master_name is None:
      query = query.filter(cls.master_name != None)
    else:
      query = query.filter(cls.master_name == master_name)

    if bot_name is None:
      query = query.filter(cls.bot_name != None)
    else:
      query = query.filter(cls.bot_name == bot_name)

    if benchmark_name is None:
      query = query.filter(cls.benchmark_name != None)
    else:
      query = query.filter(cls.benchmark_name == benchmark_name)

    if is_improvement is None:
      query = query.filter(cls.is_improvement != None)
    else:
      query = query.filter(cls.is_improvement == is_improvement)

    if recovered is None:
      query = query.filter(cls.recovered != None)
    else:
      query = query.filter(cls.recovered == recovered)

    # If callers set inequality_property_name without actually specifying a
    # corresponding inequality filter, then reset the inequality_property_name
    # and compute it automatically as if it were not specified.
    if inequality_property_name == 'start_revision':
      if min_start_revision is None and max_start_revision is None:
        inequality_property_name = None
    elif inequality_property_name == 'end_revision':
      if min_end_revision is None and max_end_revision is None:
        inequality_property_name = None
    elif inequality_property_name == 'timestamp':
      if min_timestamp is None and max_timestamp is None:
        inequality_property_name = None

    if inequality_property_name is None:
      # Callers may set any subset of the inequality filters without specifying
      # inequality_property_name, so automatically select one of the inequality
      # filters.
      if min_start_revision is not None or max_start_revision is not None:
        inequality_property_name = 'start_revision'
      elif min_end_revision is not None or max_end_revision is not None:
        inequality_property_name = 'end_revision'
      elif min_timestamp is not None or max_timestamp is not None:
        inequality_property_name = 'timestamp'

    if inequality_property_name == 'start_revision':
      query = query.order(-cls.start_revision)
      query = query.filter(cls.end_revision != None)
      query = query.filter(cls.timestamp != None)
      if min_start_revision is not None:
        query = query.filter(cls.start_revision >= min_start_revision)
      if max_start_revision is not None:
        query = query.filter(cls.start_revision <= max_start_revision)
    elif inequality_property_name == 'end_revision':
      query = query.order(-cls.end_revision)
      query = query.filter(cls.start_revision != None)
      query = query.filter(cls.timestamp != None)
      if min_end_revision is not None:
        query = query.filter(cls.end_revision >= min_end_revision)
      if max_end_revision is not None:
        query = query.filter(cls.end_revision <= max_end_revision)
    elif inequality_property_name == 'timestamp':
      query = query.order(-cls.timestamp)
      query = query.filter(cls.start_revision != None)
      query = query.filter(cls.end_revision != None)
      if min_timestamp is not None:
        query = query.filter(cls.timestamp >= min_timestamp)
      if max_timestamp is not None:
        query = query.filter(cls.timestamp <= max_timestamp)
    else:
      # The query must always filter or order by all properties regardless of
      # inequality_property_name.
      query = query.order(-cls.timestamp)
      query = query.filter(cls.start_revision != None)
      query = query.filter(cls.end_revision != None)

    results = yield query.fetch_async(limit=limit)

    postfilter = False
    if inequality_property_name == 'start_revision':
      if (min_end_revision is not None or
          max_end_revision is not None or
          min_timestamp is not None or
          max_timestamp is not None):
        postfilter = True
    elif inequality_property_name == 'end_revision':
      if (min_start_revision is not None or
          max_start_revision is not None or
          min_timestamp is not None or
          max_timestamp is not None):
        postfilter = True
    elif inequality_property_name == 'timestamp':
      if (min_start_revision is not None or
          max_start_revision is not None or
          min_end_revision is not None or
          max_end_revision is not None):
        postfilter = True

    if postfilter:
      # The NDB query can only use inequality filters for a single property, so
      # handle any other inequality filters after fetching results.
      filtered_results = []
      for result in results:
        # Cache locality requires applying all filters to each result at a time.
        if inequality_property_name != 'start_revision':
          if (min_start_revision is not None and
              result.start_revision < min_start_revision):
            continue
          if (max_start_revision is not None and
              result.start_revision > max_start_revision):
            continue
        if inequality_property_name != 'end_revision':
          if (min_end_revision is not None and
              result.end_revision < min_end_revision):
            continue
          if (max_end_revision is not None and
              result.end_revision > max_end_revision):
            continue
        if inequality_property_name != 'timestamp':
          if min_timestamp is not None and result.timestamp < min_timestamp:
            continue
          if max_timestamp is not None and result.timestamp > max_timestamp:
            continue
        filtered_results.append(result)
      results = filtered_results

    raise ndb.Return(results)

  def GetDisplayPercentChanged(self):
    """Gets a string showing the percent change."""
    if abs(self.percent_changed) == sys.float_info.max:
      return FREAKIN_HUGE
    else:
      return '%.1f%%' % abs(self.percent_changed)

  def GetDisplayAbsoluteChanged(self):
    """Gets a string showing the absolute change."""
    if abs(self.absolute_delta) == sys.float_info.max:
      return FREAKIN_HUGE
    else:
      return '%f' % abs(self.absolute_delta)

  def GetRefTestPath(self):
    if not self.ref_test:
      return None
    return utils.TestPath(self.ref_test)

  def SetIsImprovement(self, test=None):
    """Sets whether the alert is an improvement for the given test."""
    if not test:
      test = self.GetTestMetadataKey().get()
    # |self.direction| is never equal to |UNKNOWN| (see the definition above)
    # so when the test improvement direction is |UNKNOWN|, |self.is_improvement|
    # will be False.
    self.is_improvement = (self.direction == test.improvement_direction)

  def GetTestMetadataKey(self):
    """Get the key for the TestMetadata entity of this alert.

    We are in the process of converting from Test entities to TestMetadata.
    Until this is done, it's possible that an alert may store either Test
    or TestMetadata in the 'test' KeyProperty. This gets the TestMetadata key
    regardless of what's stored.
    """
    return utils.TestMetadataKey(self.test)

  @classmethod
  @ndb.synctasklet
  def GetAlertsForTest(cls, test_key, limit=None):
    result = yield cls.GetAlertsForTestAsync(test_key, limit=limit)
    raise ndb.Return(result)

  @classmethod
  @ndb.tasklet
  def GetAlertsForTestAsync(cls, test_key, limit=None):
    result = yield cls.query(cls.test.IN([
        utils.TestMetadataKey(test_key),
        utils.OldStyleTestKey(test_key)])).fetch_async(limit=limit)
    raise ndb.Return(result)


def GetBotNamesFromAlerts(alerts):
  """Gets a set with the names of the bots related to some alerts."""
  # a.test is the key of a TestMetadata entity, and the TestPath is a path like
  # master_name/bot_name/test_suite_name/metric...
  return {utils.TestPath(a.test).split('/')[1] for a in alerts}
