// Copyright 2019 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include <memory>
#include <string>
#include <vector>

namespace catapult {

class HistogramImpl;

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

typedef double Sample;

class Histogram {
 public:
  Histogram(const std::string& name, Unit unit);
  void AddSample(Sample value);

 private:
  int _GetDefaultMaxNumSampleValues();

 private:
  int max_num_sample_values_;
  std::string name_;
  Unit unit_;
  std::vector<Sample> sample_values_;
  int num_nans_;
  int num_values_;
  std::unique_ptr<HistogramImpl> impl_;
};

}  // namespace catapult
