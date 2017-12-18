# -*- coding: utf-8 -*-
# Copyright 2013 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Additional help about CRC32C and installing crcmod."""

from __future__ import absolute_import

from gslib.help_provider import HelpProvider

_DETAILED_HELP_TEXT = ("""
<B>OVERVIEW</B>
  Google Cloud Storage provides a cyclic redundancy check (CRC) header that
  allows clients to verify the integrity of object contents. For non-composite
  objects Google Cloud Storage also provides an MD5 header to allow clients to
  verify object integrity, but for composite objects only the CRC is available.
  gsutil automatically performs integrity checks on all uploads and downloads.
  Additionally, you can use the "gsutil hash" command to calculate a CRC for
  any local file.

  The CRC variant used by Google Cloud Storage is called CRC32C (Castagnoli),
  which is not available in the standard Python distribution. The implementation
  of CRC32C used by gsutil is provided by a third-party Python module called
  `crcmod <https://pypi.python.org/pypi/crcmod>`_.

  The crcmod module contains a pure-Python implementation of CRC32C, but using
  it results in very poor performance. A Python C extension is also provided by
  crcmod, which requires compiling into a binary module for use. gsutil ships
  with a precompiled crcmod C extension for Mac OS X; for other platforms, see
  the installation instructions below.

  At the end of each copy operation, the gsutil cp and rsync commands validate
  that the checksum of the source file/object matches the checksum of the
  destination file/object. If the checksums do not match, gsutil will delete
  the invalid copy and print a warning message. This very rarely happens, but
  if it does, please contact gs-team@google.com.


<B>CONFIGURATION</B>
  To determine if the compiled version of crcmod is available in your Python
  environment, you can inspect the output of the gsutil version command for the
  "compiled crcmod" entry::

    $ gsutil version -l
    ...
    compiled crcmod: True
    ...

  If your crcmod library is compiled to a native binary, this value will be
  True. If using the pure-Python version, the value will be False.

  To control gsutil's behavior in response to crcmod's status, you can set the
  "check_hashes" configuration variable. For details on this variable, see the
  surrounding comments in your gsutil configuration file. If check_hashes is not
  present in your configuration file, rerun gsutil config to regenerate the
  file.


<B>INSTALLATION</B>
  CentOS, RHEL, and Fedora
  ------------------------

  To compile and install crcmod:

    sudo yum install gcc python-devel python-setuptools redhat-rpm-config
    sudo easy_install -U pip
    sudo pip uninstall crcmod
    sudo pip install -U crcmod

  Debian and Ubuntu
  -----------------

  To compile and install crcmod:

    sudo apt-get install gcc python-dev python-setuptools
    sudo easy_install -U pip
    sudo pip uninstall crcmod
    sudo pip install -U crcmod

  Mac OS X
  --------

  gsutil distributes a pre-compiled version of crcmod for OS X, so you shouldn't
  need to compile and install it yourself. If for some reason the pre-compiled
  version is not being detected, please let the Google Cloud Storage team know
  (see "gsutil help support").

  To compile manually on OS X, you will first need to install
  `XCode <https://developer.apple.com/xcode/>`_ and then run:

    sudo easy_install -U pip
    sudo pip install -U crcmod

  Windows
  -------

  An installer is available for the compiled version of crcmod from the Python
  Package Index (PyPi) at the following URL:

  https://pypi.python.org/pypi/crcmod/1.7

  MSI installers are available for the 32-bit versions of Python 2.7.
  Make sure to install to a 32-bit Python directory. If you're using 64-bit
  Python it won't work with 32-bit crcmod, and instead you'll need to install
  32-bit Python in order to use crcmod.

  Note: If you have installed crcmod and gsutil hasn't detected it, it may have
  been installed to the wrong directory. It should be located at
  <python_dir>\\files\\Lib\\site-packages\\crcmod\\

  In some cases the installer will incorrectly install to
  <python_dir>\\Lib\\site-packages\\crcmod\\

  Manually copying the crcmod directory to the correct location should resolve
  the issue.
""")


class CommandOptions(HelpProvider):
  """Additional help about CRC32C and installing crcmod."""

  # Help specification. See help_provider.py for documentation.
  help_spec = HelpProvider.HelpSpec(
      help_name='crc32c',
      help_name_aliases=['crc32', 'crc', 'crcmod'],
      help_type='additional_help',
      help_one_line_summary='CRC32C and Installing crcmod',
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={},
  )
