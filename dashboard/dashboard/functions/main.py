from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import functions_framework
import start_pinpoint_job

@functions_framework.http
def start_pinpoint_job(request):
  return start_pinpoint_job(request)
