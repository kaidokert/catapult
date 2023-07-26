# Overview

This document is based on code at git hash b119dc4 and analyzes the existing Pinpoint service, focusing on the bisection algorithm. The primary goal is to provide a general overview and ensure that the bisection workflow works as intended. This document expects familiarity with both high-level and low-level concepts related to the Pinpoint service, such as Tryjobs, Bisections, Quests and Changes. Please go through the other README.md files found throughout the [Pinpoint folder](http://shortn/_XVomSNgcUf), or reach out to speed-services-dev@chromium.org.

# Entrypoints

There are two entry points to the Pinpoint service:

1. Auto Bisection [dashboard/auto_bisect.py](http://shortn/_zresB5xYqU)
2. Pinpoint Request [dashboard/pinpoint_request.py](http://shortn/_fer6lh1Zsd)
  * There are two types of requests directly to Pinpoint: tryjob and bisection.

All requests are dispatched to the Pinpoint service. Supported APIs through Flask can be found at [pinpoint/dispatcher.py](http://shortn/_VhT9KTf9nu). Various handlers for those APIs are at [pinpoint/handlers/](http://shortn/_SUnEippx9x).

The type of job executed (Try, Bisect) are defined in the request through `comparison_mode`, which is defined as part of the payload.

# Pinpoint

Calls made to `/api/new` are handled at [_CreateJob() (pinpoint/handlers/new.py)](http://shortn/_I2WIQm2SOC). The job is scheduled to a FIFO Queue defined by the job's configuration, which may include keys such as browser, builder or bucket.

