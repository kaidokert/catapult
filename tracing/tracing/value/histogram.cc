// Copyright 2019 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "tracing/tracing/value/histogram.h"

#include <cmath>
#include <cstdint>
#include <map>
#include <random>

#include "tracing/tracing/value/running_statistics.h"

namespace catapult {

namespace proto = tracing::tracing::proto;

class HistogramBuilder::Resampler {
 public:
  Resampler() : distribution_(0.0, 1.0) {}

  // When processing a stream of samples, call this method for each new sample
  // in order to decide whether to keep it in |samples|.
  // Modifies |samples| in-place such that its length never exceeds
  // |num_samples|. After |stream_length| samples have been processed, each
  // sample has equal probability of being retained in |samples|. The order of
  // samples is not preserved after |stream_length| exceeds |num_samples|.
  void UniformlySampleStream(std::vector<float>* samples,
                             uint32_t stream_length,
                             float new_element,
                             uint32_t num_samples) {
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

  float random() { return distribution_(generator_); }

 private:
  std::default_random_engine generator_;
  std::uniform_real_distribution<float> distribution_;
};

HistogramBuilder::HistogramBuilder(
    const std::string& name, proto::UnitAndDirection unit)
    : resampler_(std::make_unique<Resampler>()),
      running_statistics_(std::make_unique<RunningStatistics>()),
      name_(name),
      num_nans_(0) {
  max_num_sample_values_ = _GetDefaultMaxNumSampleValues();
}

HistogramBuilder::~HistogramBuilder() = default;

void HistogramBuilder::AddSample(float value) {
  if (std::isnan(value)) {
    num_nans_++;
  } else {
    running_statistics_->Add(value);
    int num_values = running_statistics_->count();
    resampler_->UniformlySampleStream(&sample_values_, num_nans_ + num_values,
                                      value, max_num_sample_values_);
  }
}

std::unique_ptr<proto::Histogram> HistogramBuilder::toProto() const {
  auto histogram = std::make_unique<proto::Histogram>();
  histogram->set_name(name_);
  *(histogram->mutable_unit()) = unit_;
  histogram->set_description(description_);

  for (float sample: sample_values_) {
    histogram->add_sample_values(sample);
  }

  histogram->set_max_num_sample_values(max_num_sample_values_);

  histogram->set_num_nans(num_nans_);

  proto::RunningStatistics* running = histogram->mutable_running();
  running->set_count(running_statistics_->count());
  running->set_max(running_statistics_->max());
  if (running_statistics_->meanlogs_valid()) {
    running->set_meanlogs(running_statistics_->meanlogs());
  }
  running->set_mean(running_statistics_->mean());
  running->set_min(running_statistics_->min());
  running->set_sum(running_statistics_->sum());
  running->set_variance(running_statistics_->variance());

  return histogram;
}

int HistogramBuilder::_GetDefaultMaxNumSampleValues() {
  // Assume a single bin. The default num sample values is num bins * 10.
  return 10;
}

}  // namespace catapult
