# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# TODO(jbudorick): Delete this once catapult updates to a newer version
# of mock.

import imp

from devil import base_error
from devil import devil_env

# Import catapult's vendored version of pymock directly. Attempting to import
# mock normally just attempts to reimport this module.
f, p, d = imp.find_module('mock', [devil_env.PYMOCK_PATH])
pymock = imp.load_module('pymock', f, p, d)


class OldPymockVersionError(base_error.BaseError):
  def __init__(self, function_name):
    super(OldPymockVersionError, self).__init__(
        'The version of pymock used by catapult does not support %s.'
            % function_name)


def ForwardHostile(clazz):

  # pylint: disable=no-self-use

  class ForwardHostileX(clazz):

    def assert_called(self, *_args, **_kwargs):
      raise OldPymockVersionError('assert_called')

    def assert_called_once(self, *_args, **_kwargs):
      raise OldPymockVersionError('assert_called_once')

    def assert_not_called(self, *_args, **_kwargs):
      raise OldPymockVersionError('assert_not_called')

  return ForwardHostileX


ANY = pymock.ANY
call = pymock.call
patch = pymock.patch
MagicMock = ForwardHostile(pymock.MagicMock)
Mock = ForwardHostile(pymock.Mock)
NonCallableMock = pymock.NonCallableMock
PropertyMock = ForwardHostile(pymock.PropertyMock)
