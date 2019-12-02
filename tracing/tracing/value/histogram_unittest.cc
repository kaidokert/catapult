// Copyright 2019 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "tracing/tracing/value/histogram.h"

#include <sstream>

#include "testing/gtest/include/gtest/gtest.h"
#include "third_party/jsoncpp/source/include/json/reader.h"

namespace catapult {

TEST(HistogramTest, WritesCorrectNameToJson) {
  Histogram histogram("my name", Unit::kUnitless);

  std::string json = histogram.ToJson();

  std::istringstream input(json);
  Json::Value root;
  input >> root;

  ASSERT_FALSE(root["name"].isNull());
  ASSERT_EQ(root["name"].asString(), "my name");
}

// TODO: add more unit tests once JSON writing is added.

}  // namespace catapult

// TODO(https://bugs.chromium.org/1029452): Figure out where this main should
// live. Do we pull in unit tests to downstream binaries as a source set or
// is it a an actual test() we add to WebRTC and Chromium bots?
int main(int argc, char** argv) {
  testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}
