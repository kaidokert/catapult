# Pinpoint: Regression Explorer

[**Pinpoint**](https://pinpoint-dot-chromeperf.appspot.com/) is a Python App
Engine service for analyzing regressions.

Given a metric and commit range, it can narrow down a regression to a specific
commit. It's designed to gracefully handle a variety of tough situations: *
Noisy performance metrics. * Flaky and failing tests. * Multiple regressions and
improvements. * Commit ranges with thousands of commits. * Regressions in
dependent repositories.

It also provides a UI for visualizing the raw result data and digging into the
root causes. Users can adjust the parameters and test potential fixes.

# Resources

*   [API reference](handlers/README.md)
*   [Contributing](../../docs/getting-set-up.md)
*   [Architecture overview](models/README.md)
*   [Design overview](elements/README.md)
