# Copyright 2018 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest
import mock

from telemetry.internal.backends.chrome import chrome_startup_args
from telemetry.internal.browser import browser_options as browser_options_module
from telemetry.util import wpr_modes


class FakeBrowserOptions(browser_options_module.BrowserOptions):
  def __init__(self, wpr_mode=wpr_modes.WPR_OFF):
    super(FakeBrowserOptions, self).__init__()
    self.wpr_mode = wpr_mode
    self.browser_type = 'chrome'
    self.browser_user_agent_type = 'desktop'
    self.disable_background_networking = False
    self.disable_component_extensions_with_background_pages = False
    self.disable_default_apps = False


class StartupArgsTest(unittest.TestCase):
  """Test expected inputs for GetBrowserStartupArgs."""

  def testFlagsMerged(self):
    browser_options = FakeBrowserOptions()
    browser_options.AppendExtraBrowserArgs([
        '--disable-features=Feature1,Feature2',
        '--disable-features=Feature2,Feature3',
        '--enable-features=Feature4,Feature5',
        '--enable-features=Feature5,Feature6',
        '--force-fieldtrials=Group1/Exp1/Group2/Exp2',
        '--force-fieldtrials=Group3/Exp3/Group4/Exp4',
        '--force-fieldtrial-params=Group1.Exp1:id/abc,Group2.Exp2:id/bcd',
        '--force-fieldtrial-params=Group4.Exp4:id/cde',
        '--foo'])

    startup_args = chrome_startup_args.GetFromBrowserOptions(browser_options)
    self.assertTrue('--foo' in startup_args)
    # Make sure there's only once instance each of --enable-features,
    # --disable-features, --force-fieldtrials and --force-fieldtrial-params, and
    # they contain all values
    disable_count = 0
    enable_count = 0
    force_fieldtrials_count = 0
    force_fieldtrial_params_count = 0
    # Merging is done using using sets, so any order is correct
    for arg in startup_args:
      if arg.startswith('--disable-features='):
        split_arg = arg.split('=', 1)[1].split(',')
        self.assertEquals({'Feature1', 'Feature2', 'Feature3'}, set(split_arg))
        disable_count += 1
      elif arg.startswith('--enable-features='):
        split_arg = arg.split('=', 1)[1].split(',')
        self.assertEquals({'Feature4', 'Feature5', 'Feature6'}, set(split_arg))
        enable_count += 1
      elif arg.startswith('--force-fieldtrials='):
        # We only split by every second '/' as each pair defines a fieldtrial
        # experiment.  E.g. 'A/B/Foo/Bar' -> {'A/B', 'Foo/Bar'}
        pieces = arg.split('=', 1)[1].split('/')
        split_arg = ['/'.join(pair) for pair in zip(pieces[::2], pieces[1::2])]
        self.assertEquals(
            {'Group1/Exp1', 'Group2/Exp2', 'Group3/Exp3', 'Group4/Exp4'},
            set(split_arg))
        force_fieldtrials_count += 1
      elif arg.startswith('--force-fieldtrial-params='):
        split_arg = arg.split('=', 1)[1].split(',')
        self.assertEquals(
            {'Group1.Exp1:id/abc', 'Group2.Exp2:id/bcd', 'Group4.Exp4:id/cde'},
            set(split_arg))
    self.assertEqual(1, disable_count)
    self.assertEqual(1, enable_count)
    self.assertEqual(1, force_fieldtrials_count)
    self.assertEqual(1, force_fieldtrial_params_count)


class ReplayStartupArgsTest(unittest.TestCase):
  """Test expected inputs for GetReplayArgs."""
  def testReplayOffGivesEmptyArgs(self):
    network_backend = mock.Mock()
    network_backend.is_open = False
    network_backend.forwarder = None

    self.assertEqual([], chrome_startup_args.GetReplayArgs(network_backend))

  def testReplayArgsBasic(self):
    network_backend = mock.Mock()
    network_backend.is_open = True
    network_backend.use_live_traffic = False
    network_backend.forwarder.remote_port = 789

    expected_args = [
        '--proxy-server=socks://127.0.0.1:789',
        '--proxy-bypass-list=<-loopback>',
        '--ignore-certificate-errors-spki-list='
        'PhrPvGIaAMmd29hj8BCZOq096yj7uMpRNHpn5PDxI6I=']
    self.assertItemsEqual(
        expected_args,
        chrome_startup_args.GetReplayArgs(network_backend))

  def testReplayArgsNoSpkiSupport(self):
    network_backend = mock.Mock()
    network_backend.is_open = True
    network_backend.use_live_traffic = False
    network_backend.forwarder.remote_port = 789

    expected_args = [
        '--proxy-server=socks://127.0.0.1:789',
        '--proxy-bypass-list=<-loopback>',
        '--ignore-certificate-errors']
    self.assertItemsEqual(
        expected_args,
        chrome_startup_args.GetReplayArgs(network_backend, False))

  def testReplayArgsUseLiveTrafficWithSpkiSupport(self):
    network_backend = mock.Mock()
    network_backend.is_open = True
    network_backend.use_live_traffic = True
    network_backend.forwarder.remote_port = 789

    expected_args = [
        '--proxy-server=socks://127.0.0.1:789',
        '--proxy-bypass-list=<-loopback>']
    self.assertItemsEqual(
        expected_args,
        chrome_startup_args.GetReplayArgs(network_backend,
                                          supports_spki_list=True))

  def testReplayArgsUseLiveTrafficWithNoSpkiSupport(self):
    network_backend = mock.Mock()
    network_backend.is_open = True
    network_backend.use_live_traffic = True
    network_backend.forwarder.remote_port = 123

    expected_args = [
        '--proxy-server=socks://127.0.0.1:123',
        '--proxy-bypass-list=<-loopback>']
    self.assertItemsEqual(
        expected_args,
        chrome_startup_args.GetReplayArgs(network_backend,
                                          supports_spki_list=False))

