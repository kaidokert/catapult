// Copyright 2019 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "tracing/tracing/value/histogram.h"

#include <cmath>
#include <sstream>

#include "testing/gtest/include/gtest/gtest.h"
#include "tracing/tracing/proto/histogram.pb.h"
#include "tracing/tracing/value/histogram_json_converter.h"

namespace catapult {

namespace proto = tracing::tracing::proto;

proto::UnitAndDirection UnitWhatever() {
  proto::UnitAndDirection unit;
  unit.set_unit(proto::UNITLESS);
  unit.set_improvement_direction(proto::BIGGER_IS_BETTER);
  return unit;
}

TEST(HistogramTest, WritesCorrectNameToJson) {
  HistogramBuilder builder("my name", UnitWhatever());

  auto histogram = builder.toProto();

  ASSERT_TRUE(histogram->has_name());
  ASSERT_EQ(histogram->name(), "my name");
}

// TODO(https://crbug.com/1029452): Make a real test or delete.
TEST(JsonOutputTest, DumpProtoToJsonTest) {
  proto::HistogramSet histogram_set;

  proto::Histogram* histogram = histogram_set.add_histograms();
  histogram->set_name("name!");
  proto::UnitAndDirection* unit = histogram->mutable_unit();
  *unit = UnitWhatever();

  proto::BinBoundaries* bin_boundaries = histogram->mutable_bin_boundaries();
  bin_boundaries->set_first_bin_boundary(17);
  proto::BinBoundarySpec* bin_boundary_spec =
      bin_boundaries->add_bin_specs();
  bin_boundary_spec->set_bin_boundary(18);

  bin_boundary_spec = bin_boundaries->add_bin_specs();
  proto::BinBoundaryDetailedSpec* detailed_spec =
      bin_boundary_spec->mutable_bin_spec();
  detailed_spec->set_boundary_type(proto::BinBoundaryDetailedSpec::EXPONENTIAL);
  detailed_spec->set_maximum_bin_boundary(19);
  detailed_spec->set_num_bin_boundaries(20);

  histogram->set_description("description!");

  proto::DiagnosticMap* diagnostics = histogram->mutable_diagnostics();
  auto diagnostic_map = diagnostics->mutable_diagnostic_map();
  proto::Diagnostic stories;
  stories.set_shared_diagnostic_guid("923e4567-e89b-12d3-a456-426655440000");
  (*diagnostic_map)["stories"] = stories;

  proto::Diagnostic generic_set_diag;
  proto::GenericSet* generic_set = generic_set_diag.mutable_generic_set();
  generic_set->add_values("some value");
  (*diagnostic_map)["whatever"] = generic_set_diag;

  histogram->add_sample_values(21.0);
  histogram->add_sample_values(22.0);
  histogram->add_sample_values(23.0);

  histogram->set_max_num_sample_values(3);

  histogram->set_num_nans(1);
  proto::DiagnosticMap* nan_diagnostics = histogram->add_nan_diagnostics();
  diagnostic_map = nan_diagnostics->mutable_diagnostic_map();
  // Reuse for laziness.
  (*diagnostic_map)["some nan diagnostic"] = generic_set_diag;

  proto::RunningStatistics* running = histogram->mutable_running();
  running->set_count(4);
  running->set_max(23.0);
  running->set_meanlogs(1.0); // ??
  running->set_mean(22.0);
  running->set_min(21.0);
  running->set_sum(66.0);
  running->set_variance(1.0);

  auto bin_map = histogram->mutable_all_bins();
  proto::Bin bin;
  bin.set_bin_count(24);
  proto::DiagnosticMap* bin_diagnostics = bin.add_diagnostic_maps();
  diagnostic_map = bin_diagnostics->mutable_diagnostic_map();
  (*diagnostic_map)["some bin diagnostic"] = generic_set_diag;
  (*bin_map)[0] = bin;

  proto::SummaryOptions* options = histogram->mutable_summary_options();
  options->set_nans(true);
  options->add_percentile(90.0);
  options->add_percentile(95.0);
  options->add_percentile(99.0);

  auto shared_diagnostics = histogram_set.mutable_shared_diagnostics();
  proto::Diagnostic stories_diag;
  generic_set = stories_diag.mutable_generic_set();
  generic_set->add_values("browse:news:cnn");
  (*shared_diagnostics)["923e4567-e89b-12d3-a456-426655440000"] = stories_diag;

  std::string output;
  ASSERT_TRUE(catapult::ToJson(histogram_set, &output));
  printf("%s\n", output.c_str());
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
