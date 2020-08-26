# Copyright 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import base64
import gzip
import os
import StringIO

from devil import devil_env
from devil.android import device_errors
from devil.utils import cmd_helper

DEVICE_LIB_PATH = '/data/local/tmp/file_hasher'
DEVICE_BIN_PATH = DEVICE_LIB_PATH + '/file_hasher_bin'

# We need to cap how many paths we send to the binary at once because
# the ARG_MAX on Android devices is relatively small, typically 131072 bytes.
# However, the more paths we use per invocation, the lower the overhead of
# starting processes, so we want to maximize this number, but we can't compute
# it exactly as we don't know how well our paths will compress.
# 5000 is experimentally determined to be reasonable. 10000 fails, and 7500
# works with existing usage, so 5000 seems like a pretty safe compromise.
_MAX_PATHS_PER_INVOCATION = 5000


def CalculateHostHashes(paths):
  """Calculates a hash for all items in |paths|.

  All items must be files (no directories).

  Args:
    paths: A list of host paths to file_hasher.
  Returns:
    A dict mapping file paths to their respective file_hasher checksums.
    Missing files exist in the dict, but have '' as values.
  """
  assert isinstance(paths, list)

  file_hasher_bin_host_path = devil_env.config.FetchPath('file_hasher_host')
  if not os.path.exists(file_hasher_bin_host_path):
    raise IOError('File not built: %s' % file_hasher_bin_host_path)
  out = ""
  for i in range(0, len(paths), _MAX_PATHS_PER_INVOCATION):
    mem_file = StringIO.StringIO()
    compressed = gzip.GzipFile(fileobj=mem_file, mode="wb")
    compressed.write(";".join(
        [os.path.realpath(p) for p in paths[i:i + _MAX_PATHS_PER_INVOCATION]]))
    compressed.close()
    compressed_paths = base64.b64encode(mem_file.getvalue())
    out += cmd_helper.GetCmdOutput(
        [file_hasher_bin_host_path, "-gz", compressed_paths])

  return dict(zip(paths, out.splitlines()))


def CalculateDeviceHashes(paths, device):
  """Calculates a hash for all items in |paths|.

  All items must be files (no directories).

  Args:
    paths: A list of device paths to file_hasher.
  Returns:
    A dict mapping file paths to their respective file_hasher checksums.
    Missing files exist in the dict, but have '' as values.
  """
  assert isinstance(paths, list)
  if not paths:
    return {}

  file_hasher_dist_path = devil_env.config.FetchPath('file_hasher_device',
                                                     device=device)

  if os.path.isdir(file_hasher_dist_path):
    file_hasher_dist_bin_path = os.path.join(file_hasher_dist_path,
                                             'file_hasher_bin')
  else:
    file_hasher_dist_bin_path = file_hasher_dist_path

  if not os.path.exists(file_hasher_dist_path):
    raise IOError('File not built: %s' % file_hasher_dist_path)
  file_hasher_file_size = os.path.getsize(file_hasher_dist_bin_path)

  # For better performance, make the script as small as possible to try and
  # avoid needing to write to an intermediary file (which RunShellCommand will
  # do if necessary).
  file_hasher_script = 'a=%s;' % DEVICE_BIN_PATH
  # Check if the binary is missing or has changed (using its file size as an
  # indicator), and trigger a (re-)push via the exit code.
  file_hasher_script += '! [[ $(ls -l $a) = *%d* ]]&&exit 2;' % (
      file_hasher_file_size)
  # Make sure it can find libbase.so
  file_hasher_script += 'export LD_LIBRARY_PATH=%s;' % DEVICE_LIB_PATH
  for i in range(0, len(paths), _MAX_PATHS_PER_INVOCATION):
    mem_file = StringIO.StringIO()
    compressed = gzip.GzipFile(fileobj=mem_file, mode='wb')
    compressed.write(';'.join(paths[i:i + _MAX_PATHS_PER_INVOCATION]))
    compressed.close()
    compressed_paths = base64.b64encode(mem_file.getvalue())
    file_hasher_script += '$a -gz %s;' % compressed_paths
  try:
    # Each input file results in a 4-byte hex number being printed (plus \n).
    large_output = len(paths) * 9 > device.MAX_ADB_OUTPUT_LENGTH
    out = device.RunShellCommand(file_hasher_script,
                                 shell=True,
                                 check_return=True,
                                 large_output=large_output)
  except device_errors.AdbShellCommandFailedError as e:
    # Push the binary only if it is found to not exist
    # (faster than checking up-front).
    if e.status == 2:
      # If files were previously pushed as root (adbd running as root), trying
      # to re-push as non-root causes the push command to report success, but
      # actually fail. So, wipe the directory first.
      device.RunShellCommand(['rm', '-rf', DEVICE_LIB_PATH],
                             as_root=True,
                             check_return=True)
      if os.path.isdir(file_hasher_dist_path):
        device.adb.Push(file_hasher_dist_path, DEVICE_LIB_PATH)
      else:
        mkdir_cmd = 'a=%s;[[ -e $a ]] || mkdir $a' % DEVICE_LIB_PATH
        device.RunShellCommand(mkdir_cmd, shell=True, check_return=True)
        device.adb.Push(file_hasher_dist_bin_path, DEVICE_BIN_PATH)

      out = device.RunShellCommand(file_hasher_script,
                                   shell=True,
                                   check_return=True,
                                   large_output=True)
    else:
      raise

  # Filter out linker warnings like
  # 'WARNING: linker: unused DT entry: type 0x1d arg 0x15db'
  return dict(zip(paths, (l for l in out if ' ' not in l)))
