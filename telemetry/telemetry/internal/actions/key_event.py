# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import string

from telemetry.internal.actions import page_action


# Map from DOM key values
# (https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/key) to
# Windows virtual key codes
# (https://cs.chromium.org/chromium/src/third_party/WebKit/Source/platform/WindowsKeyboardCodes.h)
# and their printed representations (if available).
_KEY_MAP = {}

def _AddSpecialKey(key, windows_virtual_key_code, text=None):
  assert key not in _KEY_MAP, 'Duplicate key: %s' % key
  _KEY_MAP[key] = (windows_virtual_key_code, text)

def _AddRegularKey(keys, windows_virtual_key_code):
  for k in keys:
    assert k not in _KEY_MAP, 'Duplicate key: %s' % k
    _KEY_MAP[k] = (windows_virtual_key_code, k)

_AddSpecialKey('PageUp', 0x21)
_AddSpecialKey('PageDown', 0x22)
_AddSpecialKey('End', 0x23)
_AddSpecialKey('Home', 0x24)
_AddSpecialKey('ArrowLeft', 0x25)
_AddSpecialKey('ArrowUp', 0x26)
_AddSpecialKey('ArrowRight', 0x27)
_AddSpecialKey('ArrowDown', 0x28)

_AddSpecialKey('Return', 0x0D, text='\x0D')
_AddSpecialKey('Delete', 0x2E, text='\x7F')
_AddSpecialKey('Backspace', 0x08, text='\x08')
_AddSpecialKey('Tab', 0x09, text='\x09')

# Letter keys.
for c in string.ascii_uppercase:
  _AddRegularKey([c, c.lower()], ord(c))

# Symbol keys.
_AddRegularKey(';:', 0xBA)
_AddRegularKey('=+', 0xBB)
_AddRegularKey(',<', 0xBC)
_AddRegularKey('-_', 0xBD)
_AddRegularKey('.>', 0xBE)
_AddRegularKey('/?', 0xBF)
_AddRegularKey('`~', 0xC0)
_AddRegularKey('[{', 0xDB)
_AddRegularKey('\\|', 0xDC)
_AddRegularKey(']}', 0xDD)
_AddRegularKey('\'"', 0xDE)

# Numeric keys.
_AddRegularKey('0)', 0x30)
_AddRegularKey('1!', 0x31)
_AddRegularKey('2@', 0x32)
_AddRegularKey('3#', 0x33)
_AddRegularKey('4$', 0x34)
_AddRegularKey('5%', 0x35)
_AddRegularKey('6^', 0x36)
_AddRegularKey('7&', 0x37)
_AddRegularKey('8*', 0x38)
_AddRegularKey('9(', 0x39)

# Space.
_AddRegularKey(' ', 0x20)


class Modifiers(object):
  def __init__(self, *args):
    self._modifiers = list(*args)

  def encode(self, platform):
    result = 0
    for modifier in self._modifiers:
      result |= modifier.encode(platform)
    return result

  def __or__(self, modifier):
    self._modifiers.append(modifier)

  def __str__(self):
    return '+'.join(self._modifiers)


class Modifier(object):
  def __init__(self, name, code):
    self._name = name
    self._code = code

  def encode(self, platform):
    return self._code

  def __or__(self, modifier):
    return Modifiers(self, modifier)

  def __str__(self):
    return self._name


class PlatformModifier(Modifier):
  def __init__(self, name, win=None, mac=None, linux=None):
    super(PlatformModifier, self).__init__(name, code=None)
    self._modifier_win = win
    self._modifier_mac = mac
    self._modifier_linux = linux
    assert (win is not None) or (mac is not None) or (linux is not None), \
          'One platform must be specified'

  def encode(self, platform):
    if platform.GetOSName() == 'win':
      return self._modifier_win.encode(platform)
    if platform.GetOSName() == 'mac':
      return self._modifier_mac.encode(platform)
    assert platform.GetOSName() in (
        'linux', 'android', 'chromeos',
        'fuchsia'), 'Unsupported platform for Key Modifiers'
    # Assume linux keybindings for: linux, android, fuchsia
    return self._modifier_linux.encode(platform)


# Codes are match chrome inspector protocol.
ALT = Modifier('Alt', code=1)
CTRL = Modifier('Ctrl', code=2)
META = Modifier('Meta', code=4)
SHIFT = Modifier('Shift', code=8)

# Platform specific names for existing modifiers.
OPTION = PlatformModifier('Opt', mac=ALT)
COMMAND = PlatformModifier('Cmd', mac=META)
WINDOWS = PlatformModifier('Win', win=META)

# Virtual modifier keys, resolved to platform specific ones.
PRIMARY = PlatformModifier('Primary', win=CTRL, mac=META, linux=CTRL)
SECONDARY = PlatformModifier('Secondary', win=ALT, mac=CTRL, linux=ALT)


class KeyPressAction(page_action.PageAction):

  def __init__(
      self, dom_key, modifiers=None, timeout=page_action.DEFAULT_TIMEOUT):
    """
    Args:
      modifiers: a Modifers instance or None
    """
    super(KeyPressAction, self).__init__(timeout=timeout)
    char_code = 0 if len(dom_key) > 1 else ord(dom_key)
    self._dom_key = dom_key
    self._modifiers = modifiers
    # Check that ascii chars are allowed.
    use_key_map = len(dom_key) > 1 or char_code < 128
    if use_key_map and dom_key not in _KEY_MAP:
      raise ValueError('No mapping for key: %s (code=%s)' % (
          dom_key, char_code))
    self._windows_virtual_key_code, self._text = _KEY_MAP.get(
        dom_key, ('', dom_key))

  def RunAction(self, tab):
    # Note that this action does not handle self.timeout properly. Since each
    # command gets the whole timeout, the PageAction can potentially
    # take three times as long as it should.
    encoded_modifiers = 0
    if self._modifiers is not None:
      encoded_modifiers = self._modifiers.encode(tab.browser.platform)
    tab.DispatchKeyEvent(
        key_event_type='rawKeyDown',
        dom_key=self._dom_key,
        modifiers=encoded_modifiers,
        windows_virtual_key_code=self._windows_virtual_key_code,
        native_virtual_key_code=self._windows_virtual_key_code,
        timeout=self.timeout)
    if self._text:
      tab.DispatchKeyEvent(
          key_event_type='char',
          text=self._text,
          modifiers=encoded_modifiers,
          dom_key=self._dom_key,
          windows_virtual_key_code=ord(self._text),
          native_virtual_key_code=ord(self._text),
          timeout=self.timeout)
    tab.DispatchKeyEvent(
        key_event_type='keyUp',
        dom_key=self._dom_key,
        modifiers=encoded_modifiers,
        windows_virtual_key_code=self._windows_virtual_key_code,
        native_virtual_key_code=self._windows_virtual_key_code,
        timeout=self.timeout)

  def __str__(self):
    return "%s('%s%s')" % (
        self.__class__.__name__, self._modifiers, self._dom_key)
