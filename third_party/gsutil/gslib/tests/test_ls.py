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
"""Tests for ls command."""

from __future__ import absolute_import
from datetime import datetime
import posixpath
import re
import subprocess
import sys
import time

import gslib
from gslib.cs_api_map import ApiSelector
from gslib.project_id import PopulateProjectId
import gslib.tests.testcase as testcase
from gslib.tests.testcase.integration_testcase import SkipForS3
from gslib.tests.testcase.integration_testcase import SkipForXML
from gslib.tests.util import CaptureStdout
from gslib.tests.util import ObjectToURI as suri
from gslib.tests.util import SetBotoConfigForTest
from gslib.tests.util import TEST_ENCRYPTION_CONTENT1
from gslib.tests.util import TEST_ENCRYPTION_CONTENT1_CRC32C
from gslib.tests.util import TEST_ENCRYPTION_CONTENT1_MD5
from gslib.tests.util import TEST_ENCRYPTION_CONTENT2
from gslib.tests.util import TEST_ENCRYPTION_CONTENT2_CRC32C
from gslib.tests.util import TEST_ENCRYPTION_CONTENT2_MD5
from gslib.tests.util import TEST_ENCRYPTION_CONTENT3
from gslib.tests.util import TEST_ENCRYPTION_CONTENT3_CRC32C
from gslib.tests.util import TEST_ENCRYPTION_CONTENT3_MD5
from gslib.tests.util import TEST_ENCRYPTION_CONTENT4
from gslib.tests.util import TEST_ENCRYPTION_CONTENT4_CRC32C
from gslib.tests.util import TEST_ENCRYPTION_CONTENT4_MD5
from gslib.tests.util import TEST_ENCRYPTION_CONTENT5
from gslib.tests.util import TEST_ENCRYPTION_CONTENT5_CRC32C
from gslib.tests.util import TEST_ENCRYPTION_CONTENT5_MD5
from gslib.tests.util import TEST_ENCRYPTION_KEY1
from gslib.tests.util import TEST_ENCRYPTION_KEY1_SHA256_B64
from gslib.tests.util import TEST_ENCRYPTION_KEY2
from gslib.tests.util import TEST_ENCRYPTION_KEY2_SHA256_B64
from gslib.tests.util import TEST_ENCRYPTION_KEY3
from gslib.tests.util import TEST_ENCRYPTION_KEY3_SHA256_B64
from gslib.tests.util import TEST_ENCRYPTION_KEY4
from gslib.tests.util import TEST_ENCRYPTION_KEY4_SHA256_B64
from gslib.tests.util import unittest
from gslib.third_party.storage_apitools import storage_v1_messages as apitools_messages
from gslib.util import IS_WINDOWS
from gslib.util import PrintFullInfoAboutObject
from gslib.util import Retry
from gslib.util import UTF8
import mock

KMS_XML_SKIP_MSG = ('gsutil does not support KMS operations for S3 buckets, '
                    'or listing KMS keys with the XML API.')


class TestLsUnit(testcase.GsUtilUnitTestCase):
  """Unit tests for ls command."""

  def test_one_object_with_L_storage_class_update(self):
    """Tests the JSON storage class update time field."""
    if self.test_api == ApiSelector.XML:
      return unittest.skip(
          'XML API has no concept of storage class update time')
    # Case 1: Create an object message where Storage class update time is the
    # same as Creation time.
    current_time = datetime(2017, 1, 2, 3, 4, 5, 6, tzinfo=None)
    obj_metadata = apitools_messages.Object(
        name='foo', bucket='bar', timeCreated=current_time,
        updated=current_time, timeStorageClassUpdated=current_time,
        etag='12345')
    # Create mock object to point to obj_metadata.
    obj_ref = mock.Mock()
    obj_ref.root_object = obj_metadata
    obj_ref.url_string = 'foo'

    # Print out attributes of object message.
    with CaptureStdout() as output:
      PrintFullInfoAboutObject(obj_ref)
    output = '\n'.join(output)

    # Verify that no Storage class update time field displays since it's the
    # same as Creation time.
    find_stor_update_re = re.compile(
        r'^\s*Storage class update time:+(?P<stor_update_time_val>.+)$',
        re.MULTILINE)
    stor_update_time_match = re.search(find_stor_update_re, output)
    self.assertIsNone(stor_update_time_match)

    # Case 2: Create an object message where Storage class update time differs
    # from Creation time.
    new_update_time = datetime(2017, 2, 3, 4, 5, 6, 7, tzinfo=None)
    obj_metadata2 = apitools_messages.Object(
        name='foo2', bucket='bar2', timeCreated=current_time,
        updated=current_time,
        timeStorageClassUpdated=new_update_time,
        etag='12345')
    # Create mock object to point to obj_metadata2.
    obj_ref2 = mock.Mock()
    obj_ref2.root_object = obj_metadata2
    obj_ref2.url_string = 'foo2'

    # Print out attributes of object message.
    with CaptureStdout() as output2:
      PrintFullInfoAboutObject(obj_ref2)
    output2 = '\n'.join(output2)

    # Verify that Creation time and Storage class update time fields display and
    # are the same as the times set in the object message.
    find_time_created_re = re.compile(
        r'^\s*Creation time:\s+(?P<time_created_val>.+)$',
        re.MULTILINE)
    time_created_match = re.search(find_time_created_re, output2)
    self.assertIsNotNone(time_created_match)
    time_created = time_created_match.group('time_created_val')
    self.assertEqual(time_created, datetime.strftime(
        current_time, '%a, %d %b %Y %H:%M:%S GMT'))
    find_stor_update_re_2 = re.compile(
        r'^\s*Storage class update time:+(?P<stor_update_time_val_2>.+)$',
        re.MULTILINE)
    stor_update_time_match_2 = re.search(find_stor_update_re_2, output2)
    self.assertIsNotNone(stor_update_time_match_2)
    stor_update_time = stor_update_time_match_2.group('stor_update_time_val_2')
    self.assertEqual(stor_update_time, datetime.strftime(
        new_update_time, '%a, %d %b %Y %H:%M:%S GMT'))


class TestLs(testcase.GsUtilIntegrationTestCase):
  """Integration tests for ls command."""

  def test_blank_ls(self):
    self.RunGsUtil(['ls'])

  def test_empty_bucket(self):
    bucket_uri = self.CreateBucket()
    self.AssertNObjectsInBucket(bucket_uri, 0)

  def test_empty_bucket_with_b(self):
    bucket_uri = self.CreateBucket()
    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      stdout = self.RunGsUtil(['ls', '-b', suri(bucket_uri)],
                              return_stdout=True)
      self.assertEqual('%s/\n' % suri(bucket_uri), stdout)
    _Check1()

  def test_bucket_with_Lb(self):
    """Tests ls -Lb."""
    bucket_uri = self.CreateBucket()
    stdout = self.RunGsUtil(['ls', '-Lb', suri(bucket_uri)],
                            return_stdout=True)
    # Check that the bucket URI is displayed.
    self.assertIn(suri(bucket_uri), stdout)
    # Check that we don't see output corresponding to listing objects rather
    # than buckets.
    self.assertNotIn('TOTAL:', stdout)

    # Toggle versioning on the bucket so that the modification time will be
    # greater than the creation time.
    self.RunGsUtil(['versioning', 'set', 'on', suri(bucket_uri)])
    self.RunGsUtil(['versioning', 'set', 'off', suri(bucket_uri)])
    stdout = self.RunGsUtil(['ls', '-Lb', suri(bucket_uri)],
                            return_stdout=True)
    find_metageneration_re = re.compile(
        r'^\s*Metageneration:\s+(?P<metageneration_val>.+)$', re.MULTILINE)
    find_time_created_re = re.compile(
        r'^\s*Time created:\s+(?P<time_created_val>.+)$', re.MULTILINE)
    find_time_updated_re = re.compile(
        r'^\s*Time updated:\s+(?P<time_updated_val>.+)$', re.MULTILINE)
    metageneration_match = re.search(find_metageneration_re, stdout)
    time_created_match = re.search(find_time_created_re, stdout)
    time_updated_match = re.search(find_time_updated_re, stdout)
    if self.test_api == ApiSelector.XML:
      # Check that lines for JSON-specific fields are not displayed.
      self.assertIsNone(metageneration_match)
      self.assertIsNone(time_created_match)
      self.assertIsNone(time_updated_match)
    elif self.test_api == ApiSelector.JSON:
      # Check that time created/updated lines are displayed.
      self.assertIsNotNone(metageneration_match)
      self.assertIsNotNone(time_created_match)
      self.assertIsNotNone(time_updated_match)
      # Check that updated time > created time.
      time_created = time_created_match.group('time_created_val')
      time_created = time.strptime(time_created, '%a, %d %b %Y %H:%M:%S %Z')
      time_updated = time_updated_match.group('time_updated_val')
      time_updated = time.strptime(time_updated, '%a, %d %b %Y %H:%M:%S %Z')
      self.assertGreater(time_updated, time_created)

  def test_bucket_with_lb(self):
    """Tests ls -lb."""
    bucket_uri = self.CreateBucket()
    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      stdout = self.RunGsUtil(['ls', '-lb', suri(bucket_uri)],
                              return_stdout=True)
      self.assertIn(suri(bucket_uri), stdout)
      self.assertNotIn('TOTAL:', stdout)
    _Check1()

  def test_bucket_list_wildcard(self):
    """Tests listing multiple buckets with a wildcard."""
    random_prefix = self.MakeRandomTestString()
    bucket1_name = self.MakeTempName('bucket', prefix=random_prefix)
    bucket2_name = self.MakeTempName('bucket', prefix=random_prefix)
    bucket1_uri = self.CreateBucket(bucket_name=bucket1_name)
    bucket2_uri = self.CreateBucket(bucket_name=bucket2_name)
    # This just double checks that the common prefix of the two buckets is what
    # we think it should be (based on implementation detail of CreateBucket).
    # We want to be careful when setting a wildcard on buckets to make sure we
    # don't step outside the test buckets to affect other buckets.
    common_prefix = posixpath.commonprefix([suri(bucket1_uri),
                                            suri(bucket2_uri)])
    self.assertTrue(common_prefix.startswith(
        '%s://%sgsutil-test-test_bucket_list_wildcard-bucket-' %
        (self.default_provider, random_prefix)))
    wildcard = '%s*' % common_prefix

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      stdout = self.RunGsUtil(['ls', '-b', wildcard], return_stdout=True)
      expected = set([suri(bucket1_uri) + '/', suri(bucket2_uri) + '/'])
      actual = set(stdout.split())
      self.assertEqual(expected, actual)
    _Check1()

  def test_nonexistent_bucket_with_ls(self):
    """Tests a bucket that is known not to exist."""
    stderr = self.RunGsUtil(
        ['ls', '-lb', 'gs://%s' % self.nonexistent_bucket_name],
        return_stderr=True, expected_status=1)
    self.assertIn('404', stderr)

    stderr = self.RunGsUtil(
        ['ls', '-Lb', 'gs://%s' % self.nonexistent_bucket_name],
        return_stderr=True, expected_status=1)
    self.assertIn('404', stderr)

    stderr = self.RunGsUtil(
        ['ls', '-b', 'gs://%s' % self.nonexistent_bucket_name],
        return_stderr=True, expected_status=1)
    self.assertIn('404', stderr)

  def test_list_missing_object(self):
    """Tests listing a non-existent object."""
    bucket_uri = self.CreateBucket()
    stderr = self.RunGsUtil(['ls', suri(bucket_uri, 'missing')],
                            return_stderr=True, expected_status=1)
    self.assertIn('matched no objects', stderr)

  def test_with_one_object(self):
    bucket_uri = self.CreateBucket()
    obj_uri = self.CreateObject(bucket_uri=bucket_uri, contents='foo')
    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      stdout = self.RunGsUtil(['ls', suri(bucket_uri)], return_stdout=True)
      self.assertEqual('%s\n' % obj_uri, stdout)
    _Check1()

  def test_one_object_with_l(self):
    """Tests listing one object with -l."""
    obj_uri = self.CreateObject(contents='foo')
    stdout = self.RunGsUtil(['ls', '-l', suri(obj_uri)], return_stdout=True)
    output_items = stdout.split()
    self.assertTrue(output_items[0].isdigit())
    # Throws exception if time string is not formatted correctly.
    time.strptime(stdout.split()[1], '%Y-%m-%dT%H:%M:%SZ')
    self.assertEqual(output_items[2], suri(obj_uri))

  def test_one_object_with_L(self):
    """Tests listing one object with -L."""
    obj_uri = self.CreateObject(contents='foo')
    # Ensure that creation and update don't take place in the same second.
    time.sleep(2)
    # Check that the creation time, rather than the updated time, is displayed.
    self.RunGsUtil(['setmeta', '-h', 'x-goog-meta-foo:bar', suri(obj_uri)])
    find_time_created_re = re.compile(
        r'^\s*Creation time:\s+(?P<time_created_val>.+)$', re.MULTILINE)
    find_time_updated_re = re.compile(
        r'^\s*Update time:\s+(?P<time_updated_val>.+)$', re.MULTILINE)
    stdout = self.RunGsUtil(['ls', '-L', suri(obj_uri)], return_stdout=True)

    time_created_match = re.search(find_time_created_re, stdout)
    time_updated_match = re.search(find_time_updated_re, stdout)
    time_created = time_created_match.group('time_created_val')
    self.assertIsNotNone(time_created)
    time_created = time.strptime(time_created, '%a, %d %b %Y %H:%M:%S %Z')
    if self.test_api == ApiSelector.XML:
      # XML API has no concept of updated time.
      self.assertIsNone(time_updated_match)
    elif self.test_api == ApiSelector.JSON:
      time_updated = time_updated_match.group('time_updated_val')
      self.assertIsNotNone(time_updated)
      time_updated = time.strptime(time_updated, '%a, %d %b %Y %H:%M:%S %Z')
      self.assertGreater(time_updated, time_created)

  def test_subdir(self):
    """Tests listing a bucket subdirectory."""
    bucket_uri = self.CreateBucket(test_objects=1)
    k1_uri = bucket_uri.clone_replace_name('foo')
    k1_uri.set_contents_from_string('baz')
    k2_uri = bucket_uri.clone_replace_name('dir/foo')
    k2_uri.set_contents_from_string('bar')
    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      stdout = self.RunGsUtil(['ls', '%s/dir' % suri(bucket_uri)],
                              return_stdout=True)
      self.assertEqual('%s\n' % suri(k2_uri), stdout)
      stdout = self.RunGsUtil(['ls', suri(k1_uri)], return_stdout=True)
      self.assertEqual('%s\n' % suri(k1_uri), stdout)
    _Check1()

  def test_subdir_nocontents(self):
    """Tests listing a bucket subdirectory using -d.

    Result will display subdirectory names instead of contents. Uses a wildcard
    to show multiple matching subdirectories.
    """
    bucket_uri = self.CreateBucket(test_objects=1)
    k1_uri = bucket_uri.clone_replace_name('foo')
    k1_uri.set_contents_from_string('baz')
    k2_uri = bucket_uri.clone_replace_name('dir/foo')
    k2_uri.set_contents_from_string('bar')
    k3_uri = bucket_uri.clone_replace_name('dir/foo2')
    k3_uri.set_contents_from_string('foo')
    k4_uri = bucket_uri.clone_replace_name('dir2/foo3')
    k4_uri.set_contents_from_string('foo2')
    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      stdout = self.RunGsUtil(['ls', '-d', '%s/dir*' % suri(bucket_uri)],
                              return_stdout=True)
      self.assertEqual('%s/dir/\n%s/dir2/\n' %
                       (suri(bucket_uri), suri(bucket_uri)), stdout)
      stdout = self.RunGsUtil(['ls', suri(k1_uri)], return_stdout=True)
      self.assertEqual('%s\n' % suri(k1_uri), stdout)
    _Check1()

  def test_versioning(self):
    """Tests listing a versioned bucket."""
    bucket1_uri = self.CreateBucket(test_objects=1)
    bucket2_uri = self.CreateVersionedBucket(test_objects=1)
    self.AssertNObjectsInBucket(bucket1_uri, 1, versioned=True)
    bucket_list = list(bucket1_uri.list_bucket())

    objuri = [bucket1_uri.clone_replace_key(key).versionless_uri
              for key in bucket_list][0]
    self.RunGsUtil(['cp', objuri, suri(bucket2_uri)])
    self.RunGsUtil(['cp', objuri, suri(bucket2_uri)])
    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check2():
      stdout = self.RunGsUtil(['ls', '-a', suri(bucket2_uri)],
                              return_stdout=True)
      self.assertNumLines(stdout, 3)
      stdout = self.RunGsUtil(['ls', '-la', suri(bucket2_uri)],
                              return_stdout=True)
      self.assertIn('%s#' % bucket2_uri.clone_replace_name(bucket_list[0].name),
                    stdout)
      self.assertIn('metageneration=', stdout)
    _Check2()

  def test_etag(self):
    """Tests that listing an object with an etag."""
    bucket_uri = self.CreateBucket()
    obj_uri = self.CreateObject(bucket_uri=bucket_uri, contents='foo')
    # TODO: When testcase setup can use JSON, match against the exact JSON
    # etag.
    etag = obj_uri.get_key().etag.strip('"\'')
    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      stdout = self.RunGsUtil(['ls', '-l', suri(bucket_uri)],
                              return_stdout=True)
      if self.test_api == ApiSelector.XML:
        self.assertNotIn(etag, stdout)
      else:
        self.assertNotIn('etag=', stdout)
    _Check1()

    def _Check2():
      stdout = self.RunGsUtil(['ls', '-le', suri(bucket_uri)],
                              return_stdout=True)
      if self.test_api == ApiSelector.XML:
        self.assertIn(etag, stdout)
      else:
        self.assertIn('etag=', stdout)
    _Check2()

    def _Check3():
      stdout = self.RunGsUtil(['ls', '-ale', suri(bucket_uri)],
                              return_stdout=True)
      if self.test_api == ApiSelector.XML:
        self.assertIn(etag, stdout)
      else:
        self.assertIn('etag=', stdout)
    _Check3()

  def test_labels(self):
    """Tests listing on a bucket with a label/tagging configuration."""
    bucket_uri = self.CreateBucket()
    bucket_suri = suri(bucket_uri)

    stdout = self.RunGsUtil(['ls', '-Lb', bucket_suri],
                            return_stdout=True)
    # No labels are present by default.
    self.assertRegexpMatches(stdout, r'Labels:\s+None')

    # Add a label and check that it shows up.
    self.RunGsUtil(['label', 'ch', '-l', 'labelkey:labelvalue', bucket_suri])
    stdout = self.RunGsUtil(['ls', '-Lb', bucket_suri],
                            return_stdout=True)
    label_regex = re.compile(
        r'Labels:\s+\{\s+"labelkey":\s+"labelvalue"\s+\}', re.MULTILINE)
    self.assertRegexpMatches(stdout, label_regex)

  @SkipForS3('S3 bucket configuration values are not supported via ls.')
  def test_location(self):
    """Tests listing a bucket with location constraint."""
    bucket_uri = self.CreateBucket()
    bucket_suri = suri(bucket_uri)

    # No location info
    stdout = self.RunGsUtil(['ls', '-lb', bucket_suri],
                            return_stdout=True)
    self.assertNotIn('Location constraint', stdout)

    # Default location constraint is US
    stdout = self.RunGsUtil(['ls', '-Lb', bucket_suri],
                            return_stdout=True)
    self.assertIn('Location constraint:\t\tUS', stdout)

  @SkipForS3('S3 bucket configuration values are not supported via ls.')
  def test_logging(self):
    """Tests listing a bucket with logging config."""
    bucket_uri = self.CreateBucket()
    bucket_suri = suri(bucket_uri)

    # No logging info
    stdout = self.RunGsUtil(['ls', '-lb', bucket_suri],
                            return_stdout=True)
    self.assertNotIn('Logging configuration', stdout)

    # Logging configuration is absent by default
    stdout = self.RunGsUtil(['ls', '-Lb', bucket_suri],
                            return_stdout=True)
    self.assertIn('Logging configuration:\t\tNone', stdout)

    # Enable and check
    self.RunGsUtil(['logging', 'set', 'on', '-b', bucket_suri,
                    bucket_suri])
    stdout = self.RunGsUtil(['ls', '-Lb', bucket_suri],
                            return_stdout=True)
    self.assertIn('Logging configuration:\t\tPresent', stdout)

    # Disable and check
    self.RunGsUtil(['logging', 'set', 'off', bucket_suri])
    stdout = self.RunGsUtil(['ls', '-Lb', bucket_suri],
                            return_stdout=True)
    self.assertIn('Logging configuration:\t\tNone', stdout)

  @SkipForS3('S3 bucket configuration values are not supported via ls.')
  def test_web(self):
    """Tests listing a bucket with website config."""
    bucket_uri = self.CreateBucket()
    bucket_suri = suri(bucket_uri)

    # No website configuration
    stdout = self.RunGsUtil(['ls', '-lb', bucket_suri],
                            return_stdout=True)
    self.assertNotIn('Website configuration', stdout)

    # Website configuration is absent by default
    stdout = self.RunGsUtil(['ls', '-Lb', bucket_suri],
                            return_stdout=True)
    self.assertIn('Website configuration:\t\tNone', stdout)

    # Initialize and check
    self.RunGsUtil(['web', 'set', '-m', 'google.com', bucket_suri])
    stdout = self.RunGsUtil(['ls', '-Lb', bucket_suri],
                            return_stdout=True)
    self.assertIn('Website configuration:\t\tPresent', stdout)

    # Clear and check
    self.RunGsUtil(['web', 'set', bucket_suri])
    stdout = self.RunGsUtil(['ls', '-Lb', bucket_suri],
                            return_stdout=True)
    self.assertIn('Website configuration:\t\tNone', stdout)

  @SkipForS3('S3 bucket configuration values are not supported via ls.')
  @SkipForXML('Requester Pays is not supported for the XML API.')
  def test_requesterpays(self):
    """Tests listing a bucket with requester pays (billing) config."""
    bucket_uri = self.CreateBucket()
    bucket_suri = suri(bucket_uri)

    # No requester pays configuration
    stdout = self.RunGsUtil(['ls', '-lb', bucket_suri],
                            return_stdout=True)
    self.assertNotIn('Requester Pays enabled', stdout)

    # Requester Pays configuration is absent by default
    stdout = self.RunGsUtil(['ls', '-Lb', bucket_suri],
                            return_stdout=True)
    self.assertIn('Requester Pays enabled:\t\tNone', stdout)

    # Initialize and check
    self.RunGsUtil(['requesterpays', 'set', 'on', bucket_suri])
    stdout = self.RunGsUtil(['ls', '-Lb', bucket_suri],
                            return_stdout=True)
    self.assertIn('Requester Pays enabled:\t\tTrue', stdout)

    # Clear and check
    self.RunGsUtil(['requesterpays', 'set', 'off', bucket_suri])
    stdout = self.RunGsUtil(['ls', '-Lb', bucket_suri],
                            return_stdout=True)
    self.assertIn('Requester Pays enabled:\t\tFalse', stdout)

  def test_list_sizes(self):
    """Tests various size listing options."""
    bucket_uri = self.CreateBucket()
    self.CreateObject(bucket_uri=bucket_uri, contents='x' * 2048)

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      stdout = self.RunGsUtil(['ls', '-l', suri(bucket_uri)],
                              return_stdout=True)
      self.assertIn('2048', stdout)
    _Check1()

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check2():
      stdout = self.RunGsUtil(['ls', '-L', suri(bucket_uri)],
                              return_stdout=True)
      self.assertIn('2048', stdout)
    _Check2()

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check3():
      stdout = self.RunGsUtil(['ls', '-al', suri(bucket_uri)],
                              return_stdout=True)
      self.assertIn('2048', stdout)
    _Check3()

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check4():
      stdout = self.RunGsUtil(['ls', '-lh', suri(bucket_uri)],
                              return_stdout=True)
      self.assertIn('2 KiB', stdout)
    _Check4()

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check5():
      stdout = self.RunGsUtil(['ls', '-alh', suri(bucket_uri)],
                              return_stdout=True)
      self.assertIn('2 KiB', stdout)
    _Check5()

  @unittest.skipIf(IS_WINDOWS,
                   'Unicode handling on Windows requires mods to site-packages')
  def test_list_unicode_filename(self):
    """Tests listing an object with a unicode filename."""
    # Note: This test fails on Windows (command.exe). I was able to get ls to
    # output Unicode filenames correctly by hacking the UniStream class code
    # shown at
    # http://stackoverflow.com/questions/878972/windows-cmd-encoding-change-causes-python-crash/3259271
    # into the start of gslib/commands/ls.py, along with no-op flush and
    # isastream functions (as an experiment).  However, even with that change,
    # the current test still fails, since it also needs to run that
    # stdout/stderr-replacement code. That UniStream class replacement really
    # needs to be added to the site-packages on Windows python.
    object_name = u'Аудиоархив'
    object_name_bytes = object_name.encode(UTF8)
    bucket_uri = self.CreateVersionedBucket()
    key_uri = self.CreateObject(bucket_uri=bucket_uri, contents='foo',
                                object_name=object_name)
    self.AssertNObjectsInBucket(bucket_uri, 1, versioned=True)
    stdout = self.RunGsUtil(['ls', '-ael', suri(key_uri)],
                            return_stdout=True)
    self.assertIn(object_name_bytes, stdout)
    if self.default_provider == 'gs':
      self.assertIn(str(key_uri.generation), stdout)
      self.assertIn(
          'metageneration=%s' % key_uri.get_key().metageneration, stdout)
      if self.test_api == ApiSelector.XML:
        self.assertIn(key_uri.get_key().etag.strip('"\''), stdout)
      else:
        # TODO: When testcase setup can use JSON, match against the exact JSON
        # etag.
        self.assertIn('etag=', stdout)
    elif self.default_provider == 's3':
      self.assertIn(key_uri.version_id, stdout)
      self.assertIn(key_uri.get_key().etag.strip('"\''), stdout)

  def test_list_acl(self):
    """Tests that long listing includes an ACL."""
    key_uri = self.CreateObject(contents='foo')
    stdout = self.RunGsUtil(['ls', '-L', suri(key_uri)], return_stdout=True)
    self.assertIn('ACL:', stdout)
    self.assertNotIn('ACCESS DENIED', stdout)

  def test_list_gzip_content_length(self):
    """Tests listing a gzipped object."""
    file_size = 10000
    file_contents = 'x' * file_size
    fpath = self.CreateTempFile(contents=file_contents, file_name='foo.txt')
    key_uri = self.CreateObject()
    self.RunGsUtil(['cp', '-z', 'txt', suri(fpath), suri(key_uri)])

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      stdout = self.RunGsUtil(['ls', '-L', suri(key_uri)], return_stdout=True)
      self.assertRegexpMatches(stdout, r'Content-Encoding:\s+gzip')
      find_content_length_re = r'Content-Length:\s+(?P<num>\d)'
      self.assertRegexpMatches(stdout, find_content_length_re)
      m = re.search(find_content_length_re, stdout)
      content_length = int(m.group('num'))
      self.assertGreater(content_length, 0)
      self.assertLess(content_length, file_size)
    _Check1()

  def test_output_chopped(self):
    """Tests that gsutil still succeeds with a truncated stdout."""
    bucket_uri = self.CreateBucket(test_objects=2)

    # Run Python with the -u flag so output is not buffered.
    gsutil_cmd = [
        sys.executable, '-u', gslib.GSUTIL_PATH, 'ls', suri(bucket_uri)]
    # Set bufsize to 0 to make sure output is not buffered.
    p = subprocess.Popen(gsutil_cmd, stdout=subprocess.PIPE, bufsize=0)
    # Immediately close the stdout pipe so that gsutil gets a broken pipe error.
    p.stdout.close()
    p.wait()
    # Make sure it still exited cleanly.
    self.assertEqual(p.returncode, 0)

  def test_recursive_list_trailing_slash(self):
    """Tests listing an object with a trailing slash."""
    bucket_uri = self.CreateBucket()
    self.CreateObject(bucket_uri=bucket_uri, object_name='/', contents='foo')
    self.AssertNObjectsInBucket(bucket_uri, 1)
    stdout = self.RunGsUtil(['ls', '-R', suri(bucket_uri)], return_stdout=True)
    # Note: The suri function normalizes the URI, so the double slash gets
    # removed.
    self.assertIn(suri(bucket_uri) + '/', stdout)

  def test_recursive_list_trailing_two_slash(self):
    """Tests listing an object with two trailing slashes."""
    bucket_uri = self.CreateBucket()
    self.CreateObject(bucket_uri=bucket_uri, object_name='//', contents='foo')
    self.AssertNObjectsInBucket(bucket_uri, 1)
    stdout = self.RunGsUtil(['ls', '-R', suri(bucket_uri)], return_stdout=True)
    # Note: The suri function normalizes the URI, so the double slash gets
    # removed.
    self.assertIn(suri(bucket_uri) + '//', stdout)

  def test_wildcard_prefix(self):
    """Tests that an object name with a wildcard does not infinite loop."""
    bucket_uri = self.CreateBucket()
    wildcard_folder_object = 'wildcard*/'
    object_matching_folder = 'wildcard10/foo'
    self.CreateObject(bucket_uri=bucket_uri, object_name=wildcard_folder_object,
                      contents='foo')
    self.CreateObject(bucket_uri=bucket_uri, object_name=object_matching_folder,
                      contents='foo')
    self.AssertNObjectsInBucket(bucket_uri, 2)
    stderr = self.RunGsUtil(['ls', suri(bucket_uri, 'wildcard*')],
                            return_stderr=True, expected_status=1)
    self.assertIn('Cloud folder %s%s contains a wildcard' %
                  (suri(bucket_uri), '/wildcard*/'), stderr)

    # Listing with a flat wildcard should still succeed.
    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check():
      stdout = self.RunGsUtil(['ls', '-l', suri(bucket_uri, '**')],
                              return_stdout=True)
      self.assertNumLines(stdout, 3)  # 2 object lines, one summary line.
    _Check()

  @SkipForS3('S3 anonymous access is not supported.')
  def test_get_object_without_list_bucket_permission(self):
    # Bucket is not publicly readable by default.
    bucket_uri = self.CreateBucket()
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='permitted', contents='foo')
    # Set this object to be publicly readable.
    self.RunGsUtil(['acl', 'set', 'public-read', suri(object_uri)])
    # Drop credentials.
    with self.SetAnonymousBotoCreds():
      stdout = self.RunGsUtil(['ls', '-L', suri(object_uri)],
                              return_stdout=True)
      self.assertIn(suri(object_uri), stdout)

  @SkipForS3('S3 customer-supplied encryption keys are not supported.')
  def test_list_encrypted_object(self):
    if self.test_api == ApiSelector.XML:
      return unittest.skip(
          'gsutil does not support encryption with the XML API')
    object_uri = self.CreateObject(object_name='foo',
                                   contents=TEST_ENCRYPTION_CONTENT1,
                                   encryption_key=TEST_ENCRYPTION_KEY1)

    # Listing object with key should return unencrypted hashes.
    with SetBotoConfigForTest([
        ('GSUtil', 'encryption_key', TEST_ENCRYPTION_KEY1)]):
      # Use @Retry as hedge against bucket listing eventual consistency.
      @Retry(AssertionError, tries=3, timeout_secs=1)
      def _ListExpectDecrypted():
        stdout = self.RunGsUtil(['ls', '-L', suri(object_uri)],
                                return_stdout=True)
        self.assertIn(TEST_ENCRYPTION_CONTENT1_MD5, stdout)
        self.assertIn(TEST_ENCRYPTION_CONTENT1_CRC32C, stdout)
        self.assertIn(TEST_ENCRYPTION_KEY1_SHA256_B64, stdout)
      _ListExpectDecrypted()

    # Listing object without a key should return encrypted hashes.
    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _ListExpectEncrypted():
      stdout = self.RunGsUtil(['ls', '-L', suri(object_uri)],
                              return_stdout=True)
      self.assertNotIn(TEST_ENCRYPTION_CONTENT1_MD5, stdout)
      self.assertNotIn(TEST_ENCRYPTION_CONTENT1_CRC32C, stdout)
      self.assertIn('encrypted', stdout)
      self.assertIn(TEST_ENCRYPTION_KEY1_SHA256_B64, stdout)
    _ListExpectEncrypted()

    # Listing object with a non-matching key should return encrypted hashes.
    with SetBotoConfigForTest([
        ('GSUtil', 'encryption_key', TEST_ENCRYPTION_KEY2)]):
      _ListExpectEncrypted()

  @SkipForS3('S3 customer-supplied encryption keys are not supported.')
  def test_list_mixed_encryption(self):
    """Tests listing objects with various encryption interactions."""
    bucket_uri = self.CreateBucket()

    self.CreateObject(
        bucket_uri=bucket_uri, object_name='foo',
        contents=TEST_ENCRYPTION_CONTENT1, encryption_key=TEST_ENCRYPTION_KEY1)
    self.CreateObject(
        bucket_uri=bucket_uri, object_name='foo2',
        contents=TEST_ENCRYPTION_CONTENT2, encryption_key=TEST_ENCRYPTION_KEY2)
    self.CreateObject(
        bucket_uri=bucket_uri, object_name='foo3',
        contents=TEST_ENCRYPTION_CONTENT3, encryption_key=TEST_ENCRYPTION_KEY3)
    self.CreateObject(
        bucket_uri=bucket_uri, object_name='foo4',
        contents=TEST_ENCRYPTION_CONTENT4, encryption_key=TEST_ENCRYPTION_KEY4)
    self.CreateObject(
        bucket_uri=bucket_uri, object_name='foo5',
        contents=TEST_ENCRYPTION_CONTENT5)

    # List 5 objects, one encrypted with each of four keys, and one
    # unencrypted. Supplying keys [1,3,4] should result in four unencrypted
    # listings and one encrypted listing (for key 2).
    with SetBotoConfigForTest([
        ('GSUtil', 'encryption_key', TEST_ENCRYPTION_KEY1),
        ('GSUtil', 'decryption_key1', TEST_ENCRYPTION_KEY3),
        ('GSUtil', 'decryption_key2', TEST_ENCRYPTION_KEY4)
        ]):
      # Use @Retry as hedge against bucket listing eventual consistency.
      @Retry(AssertionError, tries=3, timeout_secs=1)
      def _ListExpectMixed():
        """Validates object listing."""
        stdout = self.RunGsUtil(['ls', '-L', suri(bucket_uri)],
                                return_stdout=True)
        self.assertIn(TEST_ENCRYPTION_CONTENT1_MD5, stdout)
        self.assertIn(TEST_ENCRYPTION_CONTENT1_CRC32C, stdout)
        self.assertIn(TEST_ENCRYPTION_KEY1_SHA256_B64, stdout)
        self.assertNotIn(TEST_ENCRYPTION_CONTENT2_MD5, stdout)
        self.assertNotIn(TEST_ENCRYPTION_CONTENT2_CRC32C, stdout)
        self.assertIn('encrypted', stdout)
        self.assertIn(TEST_ENCRYPTION_KEY2_SHA256_B64, stdout)
        self.assertIn(TEST_ENCRYPTION_CONTENT3_MD5, stdout)
        self.assertIn(TEST_ENCRYPTION_CONTENT3_CRC32C, stdout)
        self.assertIn(TEST_ENCRYPTION_KEY3_SHA256_B64, stdout)
        self.assertIn(TEST_ENCRYPTION_CONTENT4_MD5, stdout)
        self.assertIn(TEST_ENCRYPTION_CONTENT4_CRC32C, stdout)
        self.assertIn(TEST_ENCRYPTION_KEY4_SHA256_B64, stdout)
        self.assertIn(TEST_ENCRYPTION_CONTENT5_MD5, stdout)
        self.assertIn(TEST_ENCRYPTION_CONTENT5_CRC32C, stdout)

      _ListExpectMixed()

  def test_non_ascii_project_fails(self):
    stderr = self.RunGsUtil(['ls', '-p', 'ã', 'gs://fobarbaz'],
                            expected_status=1,
                            return_stderr=True)
    self.assertIn('Invalid non-ASCII', stderr)

  def set_default_kms_key_on_bucket(self, bucket_uri):
    # Make sure our keyRing and cryptoKey exist.
    keyring_fqn = self.kms_api.CreateKeyRing(
        PopulateProjectId(None), testcase.KmsTestingResources.KEYRING_NAME,
        location=testcase.KmsTestingResources.KEYRING_LOCATION)
    key_fqn = self.kms_api.CreateCryptoKey(
        keyring_fqn, testcase.KmsTestingResources.CONSTANT_KEY_NAME)
    # Make sure that the service account for the desired bucket's parent project
    # is authorized to encrypt with the key above.
    self.RunGsUtil(['kms', 'encryption', '-k', key_fqn, suri(bucket_uri)])
    return key_fqn

  @SkipForXML(KMS_XML_SKIP_MSG)
  @SkipForS3(KMS_XML_SKIP_MSG)
  def test_default_kms_key_listed_for_bucket(self):
    bucket_uri = self.CreateBucket()

    # Default KMS key is not set by default.
    stdout = self.RunGsUtil(['ls', '-Lb', suri(bucket_uri)], return_stdout=True)
    self.assertRegexpMatches(stdout, r'Default KMS key:\s+None')

    # Default KMS key's name should be listed after being set on the bucket.
    key_fqn = self.set_default_kms_key_on_bucket(bucket_uri)
    stdout = self.RunGsUtil(['ls', '-Lb', suri(bucket_uri)], return_stdout=True)
    self.assertRegexpMatches(stdout, r'Default KMS key:\s+%s' % key_fqn)

  @SkipForXML(KMS_XML_SKIP_MSG)
  @SkipForS3(KMS_XML_SKIP_MSG)
  def test_kms_key_listed_for_kms_encrypted_object(self):
    bucket_uri = self.CreateBucket()
    key_fqn = self.set_default_kms_key_on_bucket(bucket_uri)
    # Copy an object into our bucket and encrypt using the key from above.
    obj_uri = self.CreateObject(
        bucket_uri=bucket_uri, object_name='foo', contents='foo',
        kms_key_name=key_fqn)

    stdout = self.RunGsUtil(['ls', '-L', suri(obj_uri)], return_stdout=True)

    self.assertRegexpMatches(stdout, r'KMS key:\s+%s' % key_fqn)

