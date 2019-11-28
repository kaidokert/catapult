// Copyright 2019 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "tracing/tracing-cpp/value/histogram.h"

#include <cmath>
#include <map>
#include <random>

namespace catapult {

namespace {

class HistogramImpl {
 public:
  HistogramImpl(): distribution_(0.0, 1.0) {}

 // When processing a stream of samples, call this method for each new sample in
  // order to decide whether to keep it in |samples|.
  // Modifies |samples| in-place such that its length never exceeds |num_samples|.
  // After |stream_length| samples have been processed, each sample has equal
  // probability of being retained in |samples|.
  // The order of samples is not preserved after |stream_length| exceeds
  // |num_samples|.
  void UniformlySampleStream(std::vector<Sample>* samples, int stream_length,
                             Sample new_element, int num_samples) {
    if (stream_length <= num_samples) {
      if (samples->size() >= stream_length) {
        (*samples)[stream_length - 1] = new_element;
      } else {
        samples->push_back(new_element);
      }
      return;
    }
    float prob_keep = static_cast<float>(num_samples) / stream_length;
    if (random() > prob_keep) {
      // Reject new sample.
      return;
    }

    // Replace a random element.
    int victim = static_cast<int>(std::floor(random() * num_samples));
    (*samples)[victim] = new_element;
  }

  float random() {
    return distribution_(generator_);
  }

 private:
  std::default_random_engine generator_;
  std::uniform_real_distribution<float> distribution_;
};

}  // namespace

Histogram::Histogram(const std::string& name, Unit unit)
    : name_(name), unit_(unit), num_nans_(0), num_values_(0),
      impl_(std::make_unique<HistogramImpl>()) {
  _max_num_sample_values = _GetDefaultMaxNumSampleValues();
}

void Histogram::AddSample(Sample value) {
  if (std::isnan(value)) {
    num_nans_++;
  } else {
    // TODO: get from running statistics later.
    num_values_++;
    impl->UniformlySampleStream(
        &samples_, num_nans_ + num_values_, value, _max_num_sample_values);
  }
}

int Histogram::_GetDefaultMaxNumSampleValues() {
  // Assume a single bin. The default num sample values is num bins * 10.
  return 10;
}

}  // namespace catapult
