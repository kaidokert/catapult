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

def _add_special_key(key, windows_virtual_key_code, text=None):
  assert key not in _KEY_MAP, 'Duplicate key: %s' % key
  _KEY_MAP[key] = (windows_virtual_key_code, text)

def _add_regular_key(keys, windows_virtual_key_code):
  for k in keys:
    assert k not in _KEY_MAP, 'Duplicate key: %s' % k
    _KEY_MAP[k] = (windows_virtual_key_code, k)

_add_special_key('PageUp', 0x21)
_add_special_key('PageDown', 0x22)
_add_special_key('End', 0x23)
_add_special_key('Home', 0x24)
_add_special_key('ArrowLeft', 0x25)
_add_special_key('ArrowUp', 0x26)
_add_special_key('ArrowRight', 0x27)
_add_special_key('ArrowDown', 0x28)

_add_special_key('Return', 0x0D, text='\x0D')
_add_special_key('Delete', 0x2E, text='\x7F')
_add_special_key('Backspace', 0x08, text='\x08')
_add_special_key('Tab', 0x09, text='\x09')

# Letter keys.
for c in string.ascii_uppercase:
  _add_regular_key([c, c.lower()], ord(c))

# Symbol keys.
_add_regular_key(';:', 0xBA)
_add_regular_key('=+', 0xBB)
_add_regular_key(',<', 0xBC)
_add_regular_key('-_', 0xBD)
_add_regular_key('.>', 0xBE)
_add_regular_key('/?', 0xBF)
_add_regular_key('`~', 0xC0)
_add_regular_key('[{', 0xDB)
_add_regular_key('\\|', 0xDC)
_add_regular_key(']}', 0xDD)
_add_regular_key('\'"', 0xDE)

# Numeric keys.
_add_regular_key('0)', 0x30)
_add_regular_key('1!', 0x31)
_add_regular_key('2@', 0x32)
_add_regular_key('3#', 0x33)
_add_regular_key('4$', 0x34)
_add_regular_key('5%', 0x35)
_add_regular_key('6^', 0x36)
_add_regular_key('7&', 0x37)
_add_regular_key('8*', 0x38)
_add_regular_key('9(', 0x39)

# Space.
_add_regular_key(' ', 0x20)


class KeyPressAction(page_action.PageAction):

  def __init__(self, dom_key, timeout=page_action.DEFAULT_TIMEOUT):
    super(KeyPressAction, self).__init__(timeout=timeout)
    char_code = 0 if len(dom_key) > 1 else ord(dom_key)
    self._dom_key = dom_key
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
    tab.DispatchKeyEvent(
        key_event_type='rawKeyDown',
        dom_key=self._dom_key,
        windows_virtual_key_code=self._windows_virtual_key_code,
        timeout=self.timeout)
    if self._text:
      tab.DispatchKeyEvent(
          key_event_type='char',
          text=self._text,
          dom_key=self._dom_key,
          windows_virtual_key_code=ord(self._text),
          timeout=self.timeout)
    tab.DispatchKeyEvent(
        key_event_type='keyUp',
        dom_key=self._dom_key,
        windows_virtual_key_code=self._windows_virtual_key_code,
        timeout=self.timeout)

  def __str__(self):
    return "%s('%s')" % (self.__class__.__name__, self._dom_key)
