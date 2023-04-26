from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from skia_export import skia_pipeline

if __name__ == '__main__':
  logging.getLogger().setLevel(logging.INFO)
  skia_pipeline.main()
