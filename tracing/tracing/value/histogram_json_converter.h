// Copyright 2019 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "dashboard/dashboard/proto/histogram.pb.h"

namespace catapult {

bool ToJson(const dashboard::dashboard::proto::HistogramSet& histogram_set,
            std::string* output);

}
