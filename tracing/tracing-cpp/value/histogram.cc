// Copyright 2019 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "tracing/tracing-cpp/value/histogram.h"

#include <cmath>

#include "third_party/protobuf/src/google/protobuf/util/json_util.h"
#include "tracing/tracing-cpp/value/histogram.pb.h"

namespace catapult {

Histogram2::Histogram2(const std::string& name, Unit2 unit)
    : name_(name), unit_(unit) {}

void Histogram2::AddSample(double value) {
  if (std::isnan(value)) {
    (void)unit_;
  } else {
    sample_values_.push_back(value);
  }
}

}  // namespace catapult

using namespace catapult;
int main(int argc, char** argv) {
  Histogram histogram;
  histogram.set_name("name!");
  histogram.set_unit(ms);
  BinBoundary* bin_boundary = histogram.add_bin_boundaries();
  bin_boundary->set_bin_boundary(17);
  bin_boundary = histogram.add_bin_boundaries();
  BinBoundarySpec* spec = bin_boundary->mutable_bin_spec();
  spec->add_spec(1);
  spec->add_spec(2);
  spec->add_spec(3);

  std::string output;
  google::protobuf::util::Status status =
      google::protobuf::util::MessageToJsonString(histogram, &output);
  if (!status.ok()) {
    printf("Failed: %.*s", static_cast<int>(status.error_message().size()),
           status.error_message().data());
    return 1;
  }
  printf("%s\n", output.c_str());
  return 0;
}
