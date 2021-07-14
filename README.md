
<!-- Copyright 2015 The Chromium Authors. All rights reserved.
     Use of this source code is governed by a BSD-style license that can be
     found in the LICENSE file.
-->
Catapult
========

Catapult is the home for several performance tools that span from gathering,
displaying and analyzing performance data. This includes:

 * [Trace-viewer](tracing/README.md)
 * [Telemetry](telemetry/README.md)
 * [Performance Dashboard](dashboard/README.md)
 * [Systrace](systrace/README.md)
 * [Web Page Replay](web_page_replay_go/README.md)

These tools were created by Chromium developers for performance analysis,
testing, and monitoring of Chrome, but they can also be used for analyzing and
monitoring websites, and eventually Android apps.

Contributing
============
Please see [our contributor's guide](CONTRIBUTING.md)

# Chromium project note:
If you are working on Chromium, you will have a much easier time setting up
your environmnent to edit catapult if you use a `chromium/src` checkout and edit
the DEPS'd clone of this repo under its `third_party` dir rather than cloning and editing
this repo directly.

Follow instructions at [Get the
code](https://chromium.googlesource.com/chromium/src.git/+/refs/heads/main/docs/get_the_code.md)
first and then make your changes under `src/third_party/catapult`.

<!-- **[Current build status](https://build.chromium.org/p/client.catapult/waterfall)** -->
