# Copyright (c) 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Module containing utilities for apk packages."""

import glob
import logging
import os
import re
import tempfile
import xml.etree.ElementTree
import zipfile

from devil import base_error
from devil.android.ndk import abis
from devil.android.sdk import aapt
from devil.android.sdk import bundletool
from devil.android.sdk import split_select
from devil.utils import cmd_helper
from py_utils import tempfile_ext

_logger = logging.getLogger(__name__)


_MANIFEST_ATTRIBUTE_RE = re.compile(
    r'\s*A: ([^\(\)= ]*)(?:\([^\(\)= ]*\))?='
    r'(?:"(.*)" \(Raw: .*\)|\(type.*?\)(.*))$')
_MANIFEST_ELEMENT_RE = re.compile(r'\s*(?:E|N): (\S*) .*$')


def GetPackageName(apk_path):
  """Returns the package name of the apk."""
  return ApkHelper(apk_path).GetPackageName()


# TODO(jbudorick): Deprecate and remove this function once callers have been
# converted to ApkHelper.GetInstrumentationName
def GetInstrumentationName(apk_path):
  """Returns the name of the Instrumentation in the apk."""
  return ApkHelper(apk_path).GetInstrumentationName()


def ToHelper(path_or_helper, split_apks=None):
  """Creates an ApkHelper unless one is already given."""
  if not split_apks:
    if not isinstance(path_or_helper, basestring):
      return path_or_helper
    elif path_or_helper.endswith('.apk'):
      return ApkHelper(path_or_helper)
    elif path_or_helper.endswith('.apks'):
      return ApksHelper(path_or_helper)
    elif path_or_helper.endswith('_bundle'):
      return BundleScriptHelper(path_or_helper)
  elif isinstance(path_or_helper,
                  basestring) and path_or_helper.endswith('.apk'):
    return SplitApkHelper(path_or_helper, split_apks)

  raise Exception(
      'Unrecognized APK format %s, %s' % (path_or_helper, split_apks))


# To parse the manifest, the function uses a node stack where at each level of
# the stack it keeps the currently in focus node at that level (of indentation
# in the xmltree output, ie. depth in the tree). The height of the stack is
# determinded by line indentation. When indentation is increased so is the stack
# (by pushing a new empty node on to the stack). When indentation is decreased
# the top of the stack is popped (sometimes multiple times, until indentation
# matches the height of the stack). Each line parsed (either an attribute or an
# element) is added to the node at the top of the stack (after the stack has
# been popped/pushed due to indentation).
def _ParseManifestFromApk(apk_path):
  aapt_output = aapt.Dump('xmltree', apk_path, 'AndroidManifest.xml')
  parsed_manifest = {}
  node_stack = [parsed_manifest]
  indent = '  '

  if aapt_output[0].startswith('N'):
    # if the first line is a namespace then the root manifest is indented, and
    # we need to add a dummy namespace node, then skip the first line (we dont
    # care about namespaces).
    node_stack.insert(0, {})
    output_to_parse = aapt_output[1:]
  else:
    output_to_parse = aapt_output

  for line in output_to_parse:
    if len(line) == 0:
      continue

    # If namespaces are stripped, aapt still outputs the full url to the
    # namespace and appends it to the attribute names.
    line = line.replace('http://schemas.android.com/apk/res/android:', 'android:')

    indent_depth = 0
    while line[(len(indent) * indent_depth):].startswith(indent):
      indent_depth += 1

    # Pop the stack until the height of the stack is the same is the depth of
    # the current line within the tree.
    node_stack = node_stack[:indent_depth + 1]
    node = node_stack[-1]

    # Element nodes are a list of python dicts while attributes are just a dict.
    # This is because multiple elements, at the same depth of tree and the same
    # name, are all added to the same list keyed under the element name.
    m = _MANIFEST_ELEMENT_RE.match(line[len(indent) * indent_depth:])
    if m:
      manifest_key = m.group(1)
      if manifest_key in node:
        node[manifest_key] += [{}]
      else:
        node[manifest_key] = [{}]
      node_stack += [node[manifest_key][-1]]
      continue

    m = _MANIFEST_ATTRIBUTE_RE.match(line[len(indent) * indent_depth:])
    if m:
      manifest_key = m.group(1)
      if manifest_key in node:
        raise base_error.BaseError(
            "A single attribute should have one key and one value: {}"
            .format(line))
      else:
        node[manifest_key] = m.group(2) or m.group(3)
      continue

  return parsed_manifest


def ParseManifestFromXml(xml_str):
  """Parse an android bundle manifest.

    As ParseManifestFromAapt, but uses the xml output from bundletool. Each
    element is a dict, mapping attribute or children by name. Attributes map to
    a dict (as they are unique), children map to a list of dicts (as there may
    be multiple children with the same name).

  Args:
    xml_str (str) An xml string that is an android manifest.

  Returns:
    A dict holding the parsed manifest, as with ParseManifestFromAapt.
  """
  root = xml.etree.ElementTree.fromstring(xml_str)
  return {root.tag: [_ParseManifestXMLNode(root)]}


def _ParseManifestXMLNode(node):
  out = {}
  for name, value in node.attrib.items():
    cleaned_name = name.replace(
        '{http://schemas.android.com/apk/res/android}',
        'android:').replace(
            '{http://schemas.android.com/tools}',
            'tools:')
    out[cleaned_name] = value
  for child in node:
    out.setdefault(child.tag, []).append(_ParseManifestXMLNode(child))
  return out


def _ParseNumericKey(obj, key, default=0):
  val = obj.get(key)
  if val is None:
    return default
  return int(val, 0)


class _ExportedActivity(object):
  def __init__(self, name):
    self.name = name
    self.actions = set()
    self.categories = set()
    self.schemes = set()


def _IterateExportedActivities(manifest_info):
  app_node = manifest_info['manifest'][0]['application'][0]
  activities = app_node.get('activity', []) + app_node.get('activity-alias', [])
  for activity_node in activities:
    # Presence of intent filters make an activity exported by default.
    has_intent_filter = 'intent-filter' in activity_node
    if not _ParseNumericKey(
        activity_node, 'android:exported', default=has_intent_filter):
      continue

    activity = _ExportedActivity(activity_node.get('android:name'))
    # Merge all intent-filters into a single set because there is not
    # currently a need to keep them separate.
    for intent_filter in activity_node.get('intent-filter', []):
      for action in intent_filter.get('action', []):
        activity.actions.add(action.get('android:name'))
      for category in intent_filter.get('category', []):
        activity.categories.add(category.get('android:name'))
      for data in intent_filter.get('data', []):
        activity.schemes.add(data.get('android:scheme'))
    yield activity


class BaseApkHelper(object):
  """Abstract base class representing an installable Android app."""

  def __init__(self):
    self._manifest = None

  # TODO(tiborg): Remove. We should use GetBaseApkPath instead to indicate that
  # getting the APK path may require some work.
  @property
  def path(self):
    _logger.warning('BaseApkHelper.path is deprecated. '
                    'Use BaseApkHelper.GetBaseApkPath() instead.')
    return self.GetBaseApkPath()

  def GetActivityName(self):
    """Returns the name of the first launcher Activity in the apk."""
    manifest_info = self._GetManifest()
    for activity in _IterateExportedActivities(manifest_info):
      if ('android.intent.action.MAIN' in activity.actions and
          'android.intent.category.LAUNCHER' in activity.categories):
        return self._ResolveName(activity.name)
    return None

  def GetViewActivityName(self):
    """Returns name of the first action=View Activity that can handle http."""
    manifest_info = self._GetManifest()
    for activity in _IterateExportedActivities(manifest_info):
      if ('android.intent.action.VIEW' in activity.actions and
          'http' in activity.schemes):
        return self._ResolveName(activity.name)
    return None

  def GetInstrumentationName(
      self, default='android.test.InstrumentationTestRunner'):
    """Returns the name of the Instrumentation in the apk."""
    all_instrumentations = self.GetAllInstrumentations(default=default)
    if len(all_instrumentations) != 1:
      raise base_error.BaseError(
          'There is more than one instrumentation. Expected one.')
    else:
      return self._ResolveName(all_instrumentations[0]['android:name'])

  def GetAllInstrumentations(
      self, default='android.test.InstrumentationTestRunner'):
    """Returns a list of all Instrumentations in the apk."""
    try:
      return self._GetManifest()['manifest'][0]['instrumentation']
    except KeyError:
      return [{'android:name': default}]

  def GetPackageName(self):
    """Returns the package name of the apk."""
    manifest_info = self._GetManifest()
    try:
      return manifest_info['manifest'][0]['package']
    except KeyError:
      raise Exception(
          'Failed to determine package name of %s' % self.GetBaseApkPath())

  def GetPermissions(self):
    manifest_info = self._GetManifest()
    try:
      return [p['android:name'] for
              p in manifest_info['manifest'][0]['uses-permission']]
    except KeyError:
      return []

  def GetSplitName(self):
    """Returns the name of the split of the apk."""
    manifest_info = self._GetManifest()
    try:
      return manifest_info['manifest'][0]['split']
    except KeyError:
      return None

  def HasIsolatedProcesses(self):
    """Returns whether any services exist that use isolatedProcess=true."""
    manifest_info = self._GetManifest()
    try:
      application = manifest_info['manifest'][0]['application'][0]
      services = application['service']
      return any(
          _ParseNumericKey(s, 'android:isolatedProcess') for s in services)
    except KeyError:
      return False

  def GetAllMetadata(self):
    """Returns a list meta-data tags as (name, value) tuples."""
    manifest_info = self._GetManifest()
    try:
      application = manifest_info['manifest'][0]['application'][0]
      metadata = application['meta-data']
      return [(x.get('android:name'), x.get('android:value')) for x in metadata]
    except KeyError:
      return []

  def GetVersionCode(self):
    """Returns the versionCode as an integer, or None if not available."""
    manifest_info = self._GetManifest()
    try:
      version_code = manifest_info['manifest'][0]['android:versionCode']
      return int(version_code, 16)
    except KeyError:
      return None

  def GetVersionName(self):
    """Returns the versionName as a string."""
    manifest_info = self._GetManifest()
    try:
      version_name = manifest_info['manifest'][0]['android:versionName']
      return version_name
    except KeyError:
      return ''

  def GetMinSdkVersion(self):
    """Returns the minSdkVersion as a string, or None if not available.

    Note: this cannot always be cast to an integer."""
    manifest_info = self._GetManifest()
    try:
      uses_sdk = manifest_info['manifest'][0]['uses-sdk'][0]
      min_sdk_version = uses_sdk['android:minSdkVersion']
      try:
        # The common case is for this to be an integer. Convert to decimal
        # notation (rather than hexadecimal) for readability, but convert back
        # to a string for type consistency with the general case.
        return str(int(min_sdk_version, 16))
      except ValueError:
        # In general (ex. apps with minSdkVersion set to pre-release Android
        # versions), minSdkVersion can be a string (usually, the OS codename
        # letter). For simplicity, don't do any validation on the value.
        return min_sdk_version
    except KeyError:
      return None

  def GetTargetSdkVersion(self):
    """Returns the targetSdkVersion as a string, or None if not available.

    Note: this cannot always be cast to an integer."""
    manifest_info = self._GetManifest()
    try:
      uses_sdk = manifest_info['manifest'][0]['uses-sdk'][0]
      target_sdk_version = uses_sdk['android:targetSdkVersion']
      try:
        # The common case is for this to be an integer. Convert to decimal
        # notation (rather than hexadecimal) for readability, but convert back
        # to a string for type consistency with the general case.
        return str(int(target_sdk_version, 16))
      except ValueError:
        # In general (ex. apps targeting pre-release Android versions),
        # targetSdkVersion can be a string (usually, the OS codename letter).
        # For simplicity, don't do any validation on the value.
        return target_sdk_version
    except KeyError:
      return None

  def _GetManifest(self):
    if not self._manifest:
      self._manifest = _ParseManifestFromApk(self.GetBaseApkPath())
    return self._manifest

  def _ResolveName(self, name):
    name = name.lstrip('.')
    if '.' not in name:
      return '%s.%s' % (self.GetPackageName(), name)
    return name

  def _ListApkPaths(self):
    with zipfile.ZipFile(self.GetBaseApkPath()) as z:
      return z.namelist()

  def GetAbis(self):
    """Returns a list of ABIs in the apk (empty list if no native code)."""
    # Use lib/* to determine the compatible ABIs.
    libs = set()
    for path in self._ListApkPaths():
      path_tokens = path.split('/')
      if len(path_tokens) >= 2 and path_tokens[0] == 'lib':
        libs.add(path_tokens[1])
    lib_to_abi = {
        abis.ARM: [abis.ARM, abis.ARM_64],
        abis.ARM_64: [abis.ARM_64],
        abis.X86: [abis.X86, abis.X86_64],
        abis.X86_64: [abis.X86_64]
    }
    try:
      output = set()
      for lib in libs:
        for abi in lib_to_abi[lib]:
          output.add(abi)
      return sorted(output)
    except KeyError:
      raise base_error.BaseError('Unexpected ABI in lib/* folder.')

  def GetSplits(self, device, modules=None, allow_cached_props=False):
    """Returns list of split APK paths to installed on |device|.

    Must be implemented by subclasses.

    args:
      device: The device for which to return split APKs.
      modules: Extra feature modules to install.
      allow_cached_props: Allow using cache when querying propery values from
        |device|.
    """
    # pylint: disable=unused-argument
    raise Exception('Not implemented for %s' % type(self).__name__)

  def GetBaseApkPath(self):
    """Returns path to this app's base APK.

    Must be implemented by subclasses.
    """
    raise Exception('Not implemented for %s' % type(self).__name__)


class ApkHelper(BaseApkHelper):
  """Represents a single APK Android app."""

  def __init__(self, apk_path):
    super(ApkHelper, self).__init__()
    self._apk_path = apk_path

  def GetBaseApkPath(self):
    return self._apk_path

  def GetSplits(self, device, modules=None, allow_cached_props=False):
    if modules:
      raise Exception('Cannot install modules when installing single APK')
    return [self._apk_path]


class SplitApkHelper(BaseApkHelper):
  """Represents a multi APK Android app."""

  def __init__(self, base_apk_path, split_apk_paths):
    super(SplitApkHelper, self).__init__()
    self._base_apk_path = base_apk_path
    self._split_apk_paths = split_apk_paths

  def GetBaseApkPath(self):
    return self._base_apk_path

  def GetSplits(self, device, modules=None, allow_cached_props=False):
    if modules:
      raise Exception('Cannot install modules when installing single APK')
    splits = split_select.SelectSplits(
        device,
        self.GetBaseApkPath(),
        self._split_apk_paths,
        allow_cached_props=allow_cached_props)
    if len(splits) == 1:
      _logger.warning('split-select did not select any from %s', splits)
    return [self.GetBaseApkPath()] + splits


class BaseBundleHelper(BaseApkHelper):
  """Abstract base class representing an Android app bundle."""

  def __init__(self):
    super(BaseBundleHelper, self).__init__()
    self._splits_dir = None
    self._base_apk_path = None

  def _GetApksPath(self):
    """Returns path the bundle's APKS archive.

    Must be implemented by subclasses.
    """
    raise Exception('Not implemented for %s' % type(self).__name__)

  def _GetSplitsDir(self):
    if not self._splits_dir:
      extract_dir = tempfile.mkdtemp()
      with zipfile.ZipFile(self._GetApksPath(), 'r') as zip_file:
        zip_file.extractall(extract_dir)
      self._splits_dir = os.path.join(extract_dir, 'splits')
    return self._splits_dir

  def _ExtractSplits(self, apks_path, all_abis, locales, features,
                     pixel_density, sdk_version, modules):
    # pylint: disable=no-self-use
    # TODO(crbug.com/993345): Don't extract splits every time.
    with tempfile_ext.NamedTemporaryDirectory() as output_dir:
      bundletool.ExtractApks(output_dir, apks_path, all_abis, locales, features,
                             pixel_density, sdk_version, modules)
      return os.listdir(output_dir)

  def GetBaseApkPath(self):
    if not self._base_apk_path:
      base_apks = glob.glob(
          os.path.join(self._GetSplitsDir(), 'base-master*.apk'))
      if len(base_apks) < 1:
        raise Exception('Cannot find base APK in %s' % self._GetApksPath())
      self._base_apk_path = base_apks[0]
    return self._base_apk_path

  def GetSplits(self, device, modules=None, allow_cached_props=False):
    # TODO(tiborg): Support all locales.
    splits = self._ExtractSplits(self._GetApksPath(),
                                 device.product_cpu_abis, [device.GetLocale()],
                                 device.GetFeatures(), device.pixel_density,
                                 device.build_version_sdk, modules)
    return [
        os.path.join(self._GetSplitsDir(), os.path.basename(s)) for s in splits
    ]


class ApksHelper(BaseBundleHelper):
  """Represents a bundle's APKS archive."""

  def __init__(self, apks_path):
    super(ApksHelper, self).__init__()
    self._apks_path = apks_path

  def _GetApksPath(self):
    return self._apks_path


class BundleScriptHelper(BaseBundleHelper):
  """Represents a bundle install script."""

  def __init__(self, bundle_script_path):
    super(BundleScriptHelper, self).__init__()
    self._bundle_script_path = bundle_script_path
    self._apks_path = None

  def _GetApksPath(self):
    if not self._apks_path:
      self._apks_path = tempfile.mkstemp()
      cmd = [
          self._bundle_script_path,
          'build-bundle-apks',
          '--output-apks',
          self._apks_path,
      ]
      status, stdout, stderr = cmd_helper.GetCmdStatusOutputAndError(cmd)
      if status != 0:
        raise Exception('Failed running {} with output\n{}\n{}'.format(
            ' '.join(cmd), stdout, stderr))
    return self._apks_path
