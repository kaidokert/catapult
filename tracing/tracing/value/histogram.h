// Copyright 2019 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include <memory>
#include <string>
#include <vector>

namespace catapult {

class RunningStatistics;

enum class Unit {
  kMs,
  kMsBestFitFormat,
  kTsMs,
  kNPercent,
  kSizeInBytes,
  kBytesPerSecond,
  kJ,
  kW,
  kA,
  kV,
  kHz,
  kUnitless,
  kCount,
  kSigma,
};

class Histogram {
 public:
  Histogram(const std::string& name, Unit unit);
  ~Histogram();

  void AddSample(float value);

  std::string ToJson();

 private:
  int _GetDefaultMaxNumSampleValues();

 private:
  class Resampler;

  std::unique_ptr<Resampler> resampler_;
  std::unique_ptr<RunningStatistics> running_statistics_;
  int max_num_sample_values_;
  std::string name_;
  Unit unit_;
  std::vector<float> sample_values_;
  int num_nans_;
};

}  // namespace catapult
