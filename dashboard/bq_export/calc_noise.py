# Copyright (c) 2021 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Calculate sample noise from BigQuery rows export, output to BigQuery.
"""

import logging

from bq_export import bq_noise

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  bq_noise.main()
