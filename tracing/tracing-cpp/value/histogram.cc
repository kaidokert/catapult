// Copyright 2019 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "tracing/tracing-cpp/value/histogram.h"

#include <cmath>

namespace catapult {

Histogram::Histogram(const std::string& name, Unit unit)
    : name_(name), unit_(unit) {}

void Histogram::AddSample(double value) {
  if (std::isnan(value)) {
    (void)unit_;
  } else {
    sample_values_.push_back(value);
  }
}

}  // namespace catapult
