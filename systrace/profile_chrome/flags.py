# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import optparse


def OutputOptions(parser):
  output_options = optparse.OptionGroup(parser, 'Output options')
  output_options.add_option('-o', '--output', dest='output_file',
                            help='Save trace output to file.')
  output_options.add_option('--json', help='Save trace as raw JSON instead of '
                            'HTML.', dest='write_json')
  output_options.add_option('--trace_format', help='Save trace as chosen '
                              'format instead of the default HTML.',
                              dest='trace_format')
  output_options.add_option('--view', help='Open resulting trace file in a '
                            'browser.', action='store_true')
  return output_options

def ParseFormatFlags(options):
  # Assume that at most one of options.write_json or options.trace_format
  # have defaulted values (no flag input)
  kSupportedFormats = ['html', 'json', 'proto']
  if options.write_json and options.trace_format:
    raise ValueError("At most one parameter of --json or " +
                      "--trace_format should be provided")
  if not options.write_json and not options.trace_format:
    print("Using default format: html. Choose another format by specifying: " +
            "--format [html|json|proto] or -f [html|json|proto]")
  #trace_format parsing
  if not options.trace_format:
    options.trace_format = 'json' if options.write_json else 'html'
  if options.trace_format not in kSupportedFormats:
    raise ValueError("Format '{}' is not supported." \
                          .format(options.trace_format))
