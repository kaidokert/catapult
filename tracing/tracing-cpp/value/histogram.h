// Copyright 2019 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include <string>
#include <vector>

namespace catapult {

enum class Unit {
    ms,
    msBestFitFormat,
    tsMs,
    nPercent,
    sizeInBytes,
    bytesPerSecond,
    J,
    W,
    A,
    V,
    Hz,
    Unitless,
    Count,
    Sigma
};

class Histogram {
 public:
  Histogram(const std::string& name, Unit unit);
  void AddSample(double value);
 private:
  std::string name_;
  Unit unit_;
  std::vector<double> sample_values_;
};

}  // namespace catapult
