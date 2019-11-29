// Copyright 2019 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "tracing/tracing-cpp/value/running_statistics.h"

#include <sstream>

#include "testing/gtest/include/gtest/gtest.h"

namespace catapult {

TEST(RunningStatisticsUnittest, GetsCountRight) {
  RunningStatistics stats;

  stats.Add(1);
  stats.Add(1);
  stats.Add(1);
  stats.Add(1);
  stats.Add(1);
  stats.Add(1);

  ASSERT_EQ(stats.count(), 6);
}

TEST(RunningStatisticsUnittest, ComputesMean) {
  RunningStatistics stats;

  stats.Add(1);
  stats.Add(2);
  stats.Add(3);
  stats.Add(4);

  ASSERT_EQ(stats.mean(), 2.5);
}

// TODO(https://bugs.chromium.org/1029452): more tests!

}  // namespace catapult
