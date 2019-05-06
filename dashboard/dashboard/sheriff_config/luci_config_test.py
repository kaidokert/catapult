"""Tests for the luci_config client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

try:
  from unittest.mock import MagicMock
except ImportError:
  from mock import MagicMock

import unittest
import luci_config


class LuciConfigTest(unittest.TestCase):

  def testCreateClient(self):
    service = luci_config.CreateConfigClient()

  def testFindingAllSheriffConfigs(self):
    service = MagicMock()
    service.configs.get_project_configs.execute.return_value = []
    self.assertEquals([], luci_config.FindAllSheriffConfigs(service))

    service.configs.assert_called_once()
    service.configs.get_project_configs.execute.assert_called_once()
