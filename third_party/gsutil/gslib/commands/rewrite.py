# -*- coding: utf-8 -*-
# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Implementation of rewrite command (in-place cloud object transformation)."""

from __future__ import absolute_import

import sys
import time

from apitools.base.py import encoding

from gslib.cloud_api import EncryptionException
from gslib.command import Command
from gslib.command_argument import CommandArgument
from gslib.cs_api_map import ApiSelector
from gslib.encryption_helper import CryptoTupleFromKey
from gslib.encryption_helper import FindMatchingCryptoKey
from gslib.encryption_helper import GetEncryptionTupleAndSha256Hash
from gslib.exception import CommandException
from gslib.name_expansion import NameExpansionIterator
from gslib.name_expansion import SeekAheadNameExpansionIterator
from gslib.progress_callback import FileProgressCallbackHandler
from gslib.storage_url import StorageUrlFromString
from gslib.third_party.storage_apitools import storage_v1_messages as apitools_messages
from gslib.thread_message import FileMessage
from gslib.translation_helper import PreconditionsFromHeaders
from gslib.util import ConvertRecursiveToFlatWildcard
from gslib.util import GetCloudApiInstance
from gslib.util import NO_MAX
from gslib.util import NormalizeStorageClass
from gslib.util import StdinIterator
from gslib.util import UTF8

MAX_PROGRESS_INDICATOR_COLUMNS = 65

_SYNOPSIS = """
  gsutil rewrite -k [-f] [-r] url...
  gsutil rewrite -k [-f] [-r] -I
"""

_DETAILED_HELP_TEXT = ("""
<B>SYNOPSIS</B>
""" + _SYNOPSIS + """


<B>DESCRIPTION</B>
  The gsutil rewrite command rewrites cloud objects, applying the specified
  transformations to them. The transformation(s) are atomic and
  applied based on the input transformation flags. Object metadata values are
  preserved unless altered by a transformation.

  The -k flag is supported to add, rotate, or remove encryption keys on
  objects.  For example, the command:

    gsutil rewrite -k gs://bucket/**

  will update all objects in gs://bucket with the current encryption key
  from your boto config file.

  You can also use the -r option to specify recursive object transform; this is
  synonymous with the ** wildcard. Thus, either of the following two commands
  will perform encryption key transforms on gs://bucket/subdir and all objects
  and subdirectories under it:

    gsutil rewrite -k gs://bucket/subdir**
    gsutil rewrite -k -r gs://bucket/subdir

  The rewrite command acts only on live object versions, so specifying a
  URL with a generation will fail. If you want to rewrite an archived
  generation, first copy it to the live version, then rewrite it, for example:

    gsutil cp gs://bucket/object#123 gs://bucket/object
    gsutil rewrite -k gs://bucket/object

  You can use the -s option to specify a new storage class for objects.  For
  example, the command:

    gsutil rewrite -s nearline gs://bucket/foo

  will rewrite the object, changing its storage class to nearline.

  The rewrite command will skip objects that are already in the desired state.
  For example, if you run:

    gsutil rewrite -k gs://bucket/**

  and gs://bucket contains objects that already match the encryption
  configuration, gsutil will skip rewriting those objects and only rewrite
  objects that do not match the encryption configuration. If you specify
  multiple transformations, gsutil will only skip those that would not change
  the object's state. For example, if you run:

    gsutil rewrite -s nearline -k gs://bucket/**

  and gs://bucket contains objects that already match the encryption
  configuration but have a storage class of standard, the only transformation
  applied to those objects would be the change in storage class.

  You can pass a list of URLs (one per line) to rewrite on stdin instead of as
  command line arguments by using the -I option. This allows you to use gsutil
  in a pipeline to rewrite objects identified by a program, such as:

    some_program | gsutil -m rewrite -k -I

  The contents of stdin can name cloud URLs and wildcards of cloud URLs.

  The rewrite command requires OWNER permissions on each object to preserve
  object ACLs. You can bypass this by using the -O flag, which will cause
  gsutil not to read the object's ACL and instead apply the default object ACL
  to the rewritten object:

    gsutil rewrite -k -O gs://bucket/**


<B>OPTIONS</B>
  -f          Continues silently (without printing error messages) despite
              errors when rewriting multiple objects. If some of the objects
              could not be rewritten, gsutil's exit status will be non-zero
              even if this flag is set. This option is implicitly set when
              running "gsutil -m rewrite ...".

  -I          Causes gsutil to read the list of objects to rewrite from stdin.
              This allows you to run a program that generates the list of
              objects to rewrite.

  -k          Rewrite the objects to the current encryption key specific in
              your boto configuration file. If encryption_key is specified,
              encrypt all objects with this key. If encryption_key is
              unspecified, decrypt all objects. See `gsutil help encryption`
              for details on encryption configuration.

  -O          Rewrite objects with the bucket's default object ACL instead of
              the existing object ACL. This is needed if you do not have
              OWNER permission on the object.

  -R, -r      The -R and -r options are synonymous. Causes bucket or bucket
              subdirectory contents to be rewritten recursively.

  -s <class>  Rewrite objects using the specified storage class.
""")


def _RewriteExceptionHandler(cls, e):
  """Simple exception handler to allow post-completion status."""
  if not cls.continue_on_error:
    cls.logger.error(str(e))
  cls.op_failure_count += 1


def _RewriteFuncWrapper(cls, name_expansion_result, thread_state=None):
  cls.RewriteFunc(name_expansion_result, thread_state=thread_state)


def GenerationCheckGenerator(url_strs):
  """Generator function that ensures generation-less (live) arguments."""
  for url_str in url_strs:
    if StorageUrlFromString(url_str).generation is not None:
      raise CommandException(
          '"rewrite" called on URL with generation (%s).' % url_str)
    yield url_str


class _TransformTypes(object):
  """Enum class for valid transforms."""
  CRYPTO_KEY = 'crypto_key'
  STORAGE_CLASS = 'storage_class'


class RewriteCommand(Command):
  """Implementation of gsutil rewrite command."""

  # Command specification. See base class for documentation.
  command_spec = Command.CreateCommandSpec(
      'rewrite',
      command_name_aliases=[],
      usage_synopsis=_SYNOPSIS,
      min_args=0,
      max_args=NO_MAX,
      supported_sub_args='fkIrROs:',
      file_url_ok=False,
      provider_url_ok=False,
      urls_start_arg=0,
      gs_api_support=[ApiSelector.JSON],
      gs_default_api=ApiSelector.JSON,
      argparse_arguments=[
          CommandArgument.MakeZeroOrMoreCloudURLsArgument()
      ]
  )
  # Help specification. See help_provider.py for documentation.
  help_spec = Command.HelpSpec(
      help_name='rewrite',
      help_name_aliases=['rekey', 'rotate'],
      help_type='command_help',
      help_one_line_summary='Rewrite objects',
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={},
  )

  def CheckProvider(self, url):
    if url.scheme != 'gs':
      raise CommandException(
          '"rewrite" called on URL with unsupported provider: %s' % str(url))

  def RunCommand(self):
    """Command entry point for the rewrite command."""
    self.continue_on_error = self.parallel_operations
    self.dest_storage_class = None
    self.no_preserve_acl = False
    self.read_args_from_stdin = False
    self.supported_transformation_flags = ['-k', '-s']
    self.transform_types = set()

    self.op_failure_count = 0
    self.boto_file_encryption_tuple, self.boto_file_encryption_sha256 = (
        GetEncryptionTupleAndSha256Hash())

    if self.sub_opts:
      for o, a in self.sub_opts:
        if o == '-f':
          self.continue_on_error = True
        elif o == '-k':
          self.transform_types.add(_TransformTypes.CRYPTO_KEY)
        elif o == '-I':
          self.read_args_from_stdin = True
        elif o == '-O':
          self.no_preserve_acl = True
        elif o == '-r' or o == '-R':
          self.recursion_requested = True
          self.all_versions = True
        elif o == '-s':
          self.transform_types.add(_TransformTypes.STORAGE_CLASS)
          self.dest_storage_class = NormalizeStorageClass(a)

    if self.read_args_from_stdin:
      if self.args:
        raise CommandException('No arguments allowed with the -I flag.')
      url_strs = StdinIterator()
    else:
      if not self.args:
        raise CommandException('The rewrite command (without -I) expects at '
                               'least one URL.')
      url_strs = self.args

    if not self.transform_types:
      raise CommandException(
          'rewrite command requires at least one transformation flag. '
          'Currently supported transformation flags: %s' %
          self.supported_transformation_flags)

    self.preconditions = PreconditionsFromHeaders(self.headers or {})

    url_strs_generator = GenerationCheckGenerator(url_strs)

    # Convert recursive flag to flat wildcard to avoid performing multiple
    # listings.
    if self.recursion_requested:
      url_strs_generator = ConvertRecursiveToFlatWildcard(url_strs_generator)

    # Expand the source argument(s).
    name_expansion_iterator = NameExpansionIterator(
        self.command_name, self.debug, self.logger, self.gsutil_api,
        url_strs_generator, self.recursion_requested,
        project_id=self.project_id,
        continue_on_error=self.continue_on_error or self.parallel_operations,
        bucket_listing_fields=['name', 'size'])

    seek_ahead_iterator = None
    # Cannot seek ahead with stdin args, since we can only iterate them
    # once without buffering in memory.
    if not self.read_args_from_stdin:
      # Perform the same recursive-to-flat conversion on original url_strs so
      # that it is as true to the original iterator as possible.
      seek_ahead_url_strs = ConvertRecursiveToFlatWildcard(url_strs)
      seek_ahead_iterator = SeekAheadNameExpansionIterator(
          self.command_name, self.debug, self.GetSeekAheadGsutilApi(),
          seek_ahead_url_strs, self.recursion_requested,
          all_versions=self.all_versions, project_id=self.project_id)

    # Perform rewrite requests in parallel (-m) mode, if requested.
    self.Apply(_RewriteFuncWrapper, name_expansion_iterator,
               _RewriteExceptionHandler,
               fail_on_error=(not self.continue_on_error),
               shared_attrs=['op_failure_count'],
               seek_ahead_iterator=seek_ahead_iterator)

    if self.op_failure_count:
      plural_str = 's' if self.op_failure_count else ''
      raise CommandException('%d file%s/object%s could not be rewritten.' % (
          self.op_failure_count, plural_str, plural_str))

    return 0

  def RewriteFunc(self, name_expansion_result, thread_state=None):
    gsutil_api = GetCloudApiInstance(self, thread_state=thread_state)
    transform_url = name_expansion_result.expanded_storage_url
    # Make a local copy of the requested transformations for each thread. As
    # a redundant transformation for one object might not be redundant for
    # another, we wouldn't want to remove it from the transform_types set that
    # all threads share.
    transforms_to_perform = set(self.transform_types)

    self.CheckProvider(transform_url)

    # Get all fields so that we can ensure that the target metadata is
    # specified correctly.
    src_metadata = gsutil_api.GetObjectMetadata(
        transform_url.bucket_name, transform_url.object_name,
        generation=transform_url.generation, provider=transform_url.scheme)

    if self.no_preserve_acl:
      # Leave ACL unchanged.
      src_metadata.acl = []
    elif not src_metadata.acl:
      raise CommandException(
          'No OWNER permission found for object %s. OWNER permission is '
          'required for rewriting objects, (otherwise their ACLs would be '
          'reset).' % transform_url)

    # Note: If other transform types are added, they must ensure that the
    # encryption key configuration matches the boto configuration, because
    # gsutil maintains an invariant that all objects it writes use the
    # encryption_key value (including decrypting if no key is present).
    src_encryption_sha256 = None
    if (src_metadata.customerEncryption and
        src_metadata.customerEncryption.keySha256):
      src_encryption_sha256 = src_metadata.customerEncryption.keySha256

    should_encrypt_target = self.boto_file_encryption_sha256 is not None
    source_was_encrypted = src_encryption_sha256 is not None
    using_same_encryption_key_value = (
        src_encryption_sha256 == self.boto_file_encryption_sha256)

    # Prevent accidental key rotation.
    if (_TransformTypes.CRYPTO_KEY not in transforms_to_perform and
        not using_same_encryption_key_value):
      raise EncryptionException(
          'The "-k" flag was not passed to the rewrite command, but the '
          'encryption_key value in your boto config file did not match the key '
          'used to encrypt the object "%s" (hash: %s). To encrypt the object '
          'using a different key, you must specify the "-k" flag.' %
          (transform_url, src_encryption_sha256))

    # Remove any redundant changes.

    # STORAGE_CLASS transform should be skipped if the target storage class
    # matches the existing storage class.
    if (_TransformTypes.STORAGE_CLASS in transforms_to_perform and
        self.dest_storage_class == NormalizeStorageClass(
            src_metadata.storageClass)):
      transforms_to_perform.remove(_TransformTypes.STORAGE_CLASS)
      self.logger.info('Redundant transform: %s already had storage class of '
                       '%s.' % (transform_url, src_metadata.storageClass))

    # CRYPTO_KEY transform should be skipped if we're using the same encryption
    # key (if any) that was used to encrypt the source.
    if (_TransformTypes.CRYPTO_KEY in transforms_to_perform and
        using_same_encryption_key_value):
      if self.boto_file_encryption_sha256 is None:
        log_msg = '%s is already decrypted.' % transform_url
      else:
        log_msg = '%s already has current encryption key.' % transform_url
      transforms_to_perform.remove(_TransformTypes.CRYPTO_KEY)
      self.logger.info('Redundant transform: %s' % log_msg)

    if not transforms_to_perform:
      self.logger.info(
          'Skipping %s, all transformations were redundant.' % transform_url)
      return

    # Make a deep copy of the source metadata.
    dst_metadata = encoding.PyValueToMessage(
        apitools_messages.Object, encoding.MessageToPyValue(src_metadata))

    # Remove some unnecessary/invalid fields.
    dst_metadata.customerEncryption = None
    dst_metadata.generation = None
    # Service has problems if we supply an ID, but it is responsible for
    # generating one, so it is not necessary to include it here.
    dst_metadata.id = None
    decryption_tuple = None
    # Use a generic operation name by default - this can be altered below for
    # specific transformations (encryption changes, etc.).
    operation_name = 'Rewriting'

    if source_was_encrypted:
      decryption_key = FindMatchingCryptoKey(src_encryption_sha256)
      if not decryption_key:
        raise EncryptionException(
            'Missing decryption key with SHA256 hash %s. No decryption key '
            'matches object %s' % (src_encryption_sha256, transform_url))
      decryption_tuple = CryptoTupleFromKey(decryption_key)

    if _TransformTypes.CRYPTO_KEY in transforms_to_perform:
      if not source_was_encrypted:
        operation_name = 'Encrypting'
      elif not should_encrypt_target:
        operation_name = 'Decrypting'
      else:
        operation_name = 'Rotating'

    if _TransformTypes.STORAGE_CLASS in transforms_to_perform:
      dst_metadata.storageClass = self.dest_storage_class

    # TODO: Remove this call (used to verify tests) and make it processed by
    # the UIThread.
    sys.stderr.write(
        _ConstructAnnounceText(operation_name, transform_url.url_string))

    # Message indicating beginning of operation.
    gsutil_api.status_queue.put(
        FileMessage(transform_url, None, time.time(), finished=False,
                    size=src_metadata.size,
                    message_type=FileMessage.FILE_REWRITE))

    progress_callback = FileProgressCallbackHandler(
        gsutil_api.status_queue, src_url=transform_url,
        operation_name=operation_name).call

    gsutil_api.CopyObject(
        src_metadata, dst_metadata, src_generation=transform_url.generation,
        preconditions=self.preconditions, progress_callback=progress_callback,
        decryption_tuple=decryption_tuple,
        encryption_tuple=self.boto_file_encryption_tuple,
        provider=transform_url.scheme, fields=[])

    # Message indicating end of operation.
    gsutil_api.status_queue.put(
        FileMessage(transform_url, None, time.time(), finished=True,
                    size=src_metadata.size,
                    message_type=FileMessage.FILE_REWRITE))


def _ConstructAnnounceText(operation_name, url_string):
  """Constructs announce text for ongoing operations on url_string.

  This truncates the text to a maximum of MAX_PROGRESS_INDICATOR_COLUMNS, and
  informs the rewrite-related operation ('Encrypting', 'Rotating', or
  'Decrypting').

  Args:
    operation_name: String describing the operation, i.e.
        'Rotating' or 'Encrypting'.
    url_string: String describing the file/object being processed.

  Returns:
    Formatted announce text for outputting operation progress.
  """
  # Operation name occupies 10 characters (enough for 'Encrypting'), plus a
  # space. The rest is used for url_string. If a longer operation name is
  # used, it will be truncated. We can revisit this size if we need to support
  # a longer operation, but want to make sure the terminal output is meaningful.
  justified_op_string = operation_name[:10].ljust(11)
  start_len = len(justified_op_string)
  end_len = len(': ')
  if (start_len + len(url_string) + end_len >
      MAX_PROGRESS_INDICATOR_COLUMNS):
    ellipsis_len = len('...')
    url_string = '...%s' % url_string[
        -(MAX_PROGRESS_INDICATOR_COLUMNS - start_len - end_len - ellipsis_len):]
  base_announce_text = '%s%s:' % (justified_op_string, url_string)
  format_str = '{0:%ds}' % MAX_PROGRESS_INDICATOR_COLUMNS
  return format_str.format(base_announce_text.encode(UTF8))
