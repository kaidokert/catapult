# Copyright 2024 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Code to handle the optparse -> argparse migration.

Once all Telemetry and Telemetry-dependent code switches to using these wrappers
instead of directly using optparse, incremental changes can be made to move the
underlying implementation from optparse to argparse before finally switching
directly to argparse.
"""

import argparse


def _AddArgumentImpl(parser, *args, **kwargs):
  if 'help' in kwargs:
    help_str = kwargs['help']
    help_str = help_str.replace('%default', '%(default)s')
    kwargs['help'] = help_str
  parser.add_argument(*args, **kwargs)


class ArgumentParser(argparse.ArgumentParser):

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # parse_args behavior differs between optparse and argparse, so store a
    # reference to the original implementation now before we override it later.
    self.argparse_parse_args = self.parse_args

  def parse_args(self, args=None, namespace=None):
    """optparse-like override of argparse's parse_args.

    optparse's parse_args appears to function like argparse's parse_known_args,
    so just use that.
    """
    return self.parse_known_args(args, namespace)

  def add_option(self, *args, **kwargs):
    _AddArgumentImpl(self, *args, **kwargs)

  def add_option_group(self, *args, **kwargs):
    # We no-op since argparse's add_argument_group already associates the group
    # with the argument parser.
    pass

  def get_default_values(self):
    defaults = {}
    for action in self._actions:
      defaults[action.dest] = action.default
    return ArgumentValues(**defaults)


class _ArgumentGroup(argparse._ArgumentGroup):

  def add_option(self, *args, **kwargs):
    _AddArgumentImpl(self, *args, **kwargs)


# Used by BrowserFinderOptions
class ArgumentValues(argparse.Namespace):
  # To be filled in over time.
  pass


def CreateOptionGroup(parser, title, description=None):
  """Creates an ArgumentParser group using the same arguments as optparse.

  See Python's optparse.OptionGroup documentation for argument descriptions.
  """
  # Copied from argparse's source code for add_argument_group, but using our own
  # class.
  group = _ArgumentGroup(parser, title, description)
  parser._action_groups.append(group)
  return group


def CreateFromOptparseInputs(usage='%prog [options]', description=None):
  """Creates an ArgumentParser using the same constructor arguments as optparse.

  See Python's optparse.OptionParser documentation for argument descriptions.
  The following args have been omitted since they do not appear to be used in
  Telemetry, but can be added later if necessary.
    * option_list
    * option_class
    * version
    * conflict_handler
    * formatter
    * add_help_option
    * prog
    * epilog
  """
  usage = usage.replace('%prog', '%(prog)s')
  return ArgumentParser(usage=usage, description=description)
