# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import mock
import unittest

from telemetry.internal.results import artifact_results
from telemetry.internal.util import file_handle

class ArtifactResultsUnittest(unittest.TestCase):
  @mock.patch('telemetry.internal.results.artifact_results.shutil.move')
  @mock.patch('telemetry.internal.results.artifact_results.os.makedirs')
  def testAddBasic(self, make_patch, move_patch):
    ar = artifact_results.ArtifactResults('/foo')

    ar.AddArtifact('test', 'artifact_name', '/foo/artifacts/bar.log')
    move_patch.assert_not_called()
    make_patch.assert_called_with('/foo/artifacts')

    self.assertEqual({k: dict(v) for k, v in ar._test_artifacts.items()}, {
        'test': {
            'artifact_name': ['bar.log'],
        }
    })

  @mock.patch('telemetry.internal.results.artifact_results.shutil.move')
  @mock.patch('telemetry.internal.results.artifact_results.os.makedirs')
  def testAddFileHandle(self, make_patch, move_patch):
    ar = artifact_results.ArtifactResults('/foo')

    ar.AddArtifact('test', 'artifact_name', file_handle.FromFilePath(
        '/foo/artifacts/bar.log'))
    move_patch.assert_not_called()
    make_patch.assert_called_with('/foo/artifacts')

    self.assertEqual({k: dict(v) for k, v in ar._test_artifacts.items()}, {
        'test': {
            'artifact_name': ['bar.log'],
        }
    })

  @mock.patch('telemetry.internal.results.artifact_results.shutil.move')
  @mock.patch('telemetry.internal.results.artifact_results.os.makedirs')
  def testAddAndMove(self, make_patch, move_patch):
    ar = artifact_results.ArtifactResults('/foo')

    ar.AddArtifact('test', 'artifact_name', '/other/directory/bar.log')
    move_patch.assert_called_with('/other/directory/bar.log', '/foo/artifacts')
    make_patch.assert_called_with('/foo/artifacts')

    self.assertEqual({k: dict(v) for k, v in ar._test_artifacts.items()}, {
        'test': {
            'artifact_name': ['bar.log'],
        }
    })

  @mock.patch('telemetry.internal.results.artifact_results.shutil.move')
  @mock.patch('telemetry.internal.results.artifact_results.os.makedirs')
  def testAddMultiple(self, make_patch, move_patch):
    ar = artifact_results.ArtifactResults('/foo')

    ar.AddArtifact('test', 'artifact_name', '/foo/artifacts/bar.log')
    ar.AddArtifact('test', 'artifact_name', '/foo/artifacts/bam.log')
    move_patch.assert_not_called()
    make_patch.assert_called_with('/foo/artifacts')

    self.assertEqual({k: dict(v) for k, v in ar._test_artifacts.items()}, {
        'test': {
            'artifact_name': ['bar.log', 'bam.log'],
        }
    })
