# Copyright 2019 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""A wrapper for common operations on a Fuchsia device"""

from __future__ import absolute_import
import logging
import os
import platform
import subprocess
import sys

# TODO(crbug.com/1267066): Remove when python2 is deprecated.
import six

from telemetry.core import util

TEST_SCRIPTS_ROOT = os.path.join(util.GetCatapultDir(), '..', '..', 'build',
                                 'fuchsia', 'test')
assert os.path.exists(TEST_SCRIPTS_ROOT)
sys.path.append(TEST_SCRIPTS_ROOT)
# pylint: disable=import-error,wrong-import-position
import common
from common import get_ssh_address
from compatible_utils import get_ssh_prefix
# pylint: enable=import-error,wrong-import-position

FUCHSIA_BROWSERS = [
    'fuchsia-chrome',
    'web-engine-shell',
    'cast-streaming-shell',
]

FUCHSIA_REPO = 'fuchsia.com'

SDK_ROOT = os.path.join(util.GetCatapultDir(), '..', 'fuchsia-sdk', 'sdk')
assert os.path.exists(SDK_ROOT)


def GetHostArchFromPlatform():
  host_arch = platform.machine()
  if host_arch in ['x86_64', 'AMD64']:
    return 'x64'
  if host_arch in ['arm64', 'aarch64']:
    return 'arm64'
  raise Exception('Unsupported host architecture: %s' % host_arch)


def run_ffx_command(cmd, target_id=None, check=True, **kwargs):
  # TODO(crbug.com/40935291): Remove this function in favor of using
  # common.run_ffx_command directly.
  return common.run_ffx_common(check=check,
                               cmd=cmd,
                               target_id=target_id,
                               **kwargs)


def run_continuous_ffx_command(cmd, target_id, **kwargs):
  # TODO(crbug.com/40935291): Remove this function in favor of using
  # common.run_continuous_ffx_command directly.
  return common.run_continous_ffx_command(cmd=cmd,
                                          target_id=target_id,
                                          **kwargs)


class CommandRunner():
  """Helper class used to execute commands on Fuchsia devices on a remote host
  over SSH."""

  def __init__(self, target_id):
    """Creates a CommandRunner that connects to the specified |host| and |port|
    using the ssh config at the specified |config_path|.

    Args:
      target_id: The target id used by ffx."""
    self._target_id = target_id
    self._ssh_prefix = get_ssh_prefix(get_ssh_address(target_id))

  def run_ffx_command(self, cmd, **kwargs):
    return run_ffx_command(cmd, self._target_id, **kwargs)

  def run_continuous_ffx_command(self, cmd, **kwargs):
    return run_continuous_ffx_command(cmd, self._target_id, **kwargs)

  def RunCommandPiped(self, command=None, ssh_args=None, **kwargs):
    """Executes an SSH command on the remote host and returns a process object
    with access to the command's stdio streams. Does not block.

    Args:
      command: A list of strings containing the command and its arguments.
      ssh_args: Arguments that will be passed to SSH.
      kwargs: A dictionary of parameters to be passed to subprocess.Popen().
          The parameters can be used to override stdin and stdout, for example.

    Returns:
      A subprocess.Popen object for the command."""
    if not command:
      command = []
    if not ssh_args:
      ssh_args = []

    # Having control master causes weird behavior in port_forwarding.
    ssh_args.append('-oControlMaster=no')
    ssh_command = self._ssh_prefix + ssh_args + ['--'] + command
    logging.debug(' '.join(ssh_command))
    if six.PY3:
      kwargs['text'] = True
    return subprocess.Popen(ssh_command, **kwargs)

  def RunCommand(self, command=None, ssh_args=None, **kwargs):
    """Executes an SSH command on the remote host and returns stdout, stderr,
    and return code of the command. Blocks."""
    cmd_proc = self.RunCommandPiped(command, ssh_args, **kwargs)
    stdout, stderr = cmd_proc.communicate()
    return cmd_proc.returncode, stdout, stderr


# TODO(crbug.com/40935291): Remove this function in favor of
# ffx_integration.run_symbolizer.
def StartSymbolizerForProcessIfPossible(input_file, output_file,
                                        build_id_files):
  """Starts a symbolizer process if possible.

    Args:
      input_file: Input file to be symbolized.
      output_file: Output file for symbolizer stdout and stderr.
      build_id_files: Path to the ids.txt files which maps build IDs to
          unstripped binaries on the filesystem.

    Returns:
      A subprocess.Popen object for the started process, None if symbolizer
      fails to start."""

  if build_id_files:
    symbolizer = os.path.join(SDK_ROOT, 'tools', GetHostArchFromPlatform(),
                              'symbolizer')
    symbolizer_cmd = [
        symbolizer, '--build-id-dir', os.path.join(SDK_ROOT, '.build-id')
    ]

    for build_id_file in build_id_files:
      if not os.path.isfile(build_id_file):
        logging.error(
            'Symbolizer cannot be started. %s is not a file' % build_id_file)
        return None
      symbolizer_cmd.extend(['--ids-txt', build_id_file])

    logging.debug('Running "%s".' % ' '.join(symbolizer_cmd))
    kwargs = {
        'stdin': input_file,
        'stdout': output_file,
        'stderr': subprocess.STDOUT,
        'close_fds': True
    }
    if six.PY3:
      kwargs['text'] = True
    return subprocess.Popen(symbolizer_cmd, **kwargs)
  logging.error('Symbolizer cannot be started.')
  return None
