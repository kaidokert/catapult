# Copyright 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""This module provides the global variable options_for_unittests.

This is set to a BrowserOptions object by the test harness, or None
if unit tests are not running.

This allows multiple unit tests to use a specific
browser, in face of multiple options."""

from telemetry.internal import story_runner
from telemetry.testing import fakes


_options = []


def Push(options):
  _options.append(options)


def Pop():
  return _options.pop()


def GetCopy():
  if not AreSet():
    return None
  return _options[-1].Copy()


def AreSet():
  return bool(_options)


def GetRunOptions(output_dir=None, benchmark_cls=None, fake_browser=False,
                  overrides=None):
  """Get an options object filled in necessary defaults for the Run command.

  The returned options also try to suppress outputs and raise an exception if
  ever passed directly to results_options.CreateResults. Tests that require the
  creation of artifacts or other outputs must explicitly set any required
  options as needed, e.g. assign a temporary directory to options.output_dir.

  Args:
    output_dir: A directory to be used for writing outputs and artifacts.
      Usually the caller will create a temporary directory and pass its path
      here. Note that it is an error to leave the output_dir as None and pass
      the returned options object to results_options.CreateResults.
    benchmark_cls: An optional benchmark class. If given, the benchmark may
      also define and process additional arguments.
    fake_browser: Whether to create options object that always "finds" a
      fakes.FakePossibleBrowser. The default is to use the browser selected
      on the command line of the test runner.
    overrides: An optional dictionary with option values to override *before*
      options are processed by benchmark and story runner. In most situations
      this should not be needed, tests should be able to just adjust options on
      the returned object. TODO(crbug.com/985712): This should not be required,
      ideally the processing of options should not change the internal state of
      Telemetry objects.
  Returns:
    An options object with default values for all command line arguments.
  """
  if fake_browser:
    options = fakes.CreateBrowserFinderOptions()
  else:
    options = GetCopy()  # A copy of the unittest options.
  parser = options.CreateParser()
  if benchmark_cls is not None:
    benchmark_cls.AddCommandLineArgs(parser)
  story_runner.AddCommandLineArgs(parser)
  if benchmark_cls is not None:
    benchmark_cls.SetArgumentDefaults(parser)
  options.MergeDefaultValues(parser.get_default_values())
  if overrides:
    for name, value in overrides.items():
      if not hasattr(options, name):
        raise AttributeError('Options object has no attribute: %s' % name)
      setattr(options, name, value)
  if benchmark_cls is not None:
    benchmark_cls.ProcessCommandLineArgs(parser, options)
  story_runner.ProcessCommandLineArgs(parser, options)
  options.output_dir = output_dir
  options.output_formats = ['none']
  options.suppress_gtest_report = True
  options.upload_bucket = None
  options.upload_results = False
  return options
