#!/usr/bin/env python
# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import os
import logging
import subprocess
import platform
import time


_DISPLAY = ':99'
_SCREENSHOT_FILE = '/tmp/dev-server-test-screenshot.png'


def ShouldStartXvfb():
  # TODO(crbug.com/973847): Note that you can locally change this to return
  # False to diagnose timeouts for dev server tests.
  return platform.system() == 'Linux'


def StartXvfb():
  xvfb_command = ['Xvfb', _DISPLAY, '-screen', '0', '1280x1024x24', '-ac']
  xvfb_process = subprocess.Popen(
      xvfb_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  time.sleep(0.2)
  returncode = xvfb_process.poll()
  if returncode is None:
    os.environ['DISPLAY'] = _DISPLAY
  else:
    logging.error('Xvfb did not start, returncode: %s, stdout:\n%s',
                  returncode, xvfb_process.stdout.read())
    xvfb_process = None
  return xvfb_process


def DumpBase64PngScreenshotToStdout():
  if not ShouldStartXvfb():
    return

  # xwd -display _DISPLAY -root -silent | convert xwd:- png:_SCREENSHOT_FILE
  p1 = subprocess.Popen(['xwd', '-display', _DISPLAY, '-root', '-silent'],
                        stdout=subprocess.PIPE)
  p2 = subprocess.Popen(['convert', 'xwd:-', 'png:' + _SCREENSHOT_FILE],
                        stdin=p1.stdout, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
  (stdout, stderr) = p2.communicate()
  print "Saved screenshot in /tmp/screenshot.png"
  print "Xvfb log stdout:", stdout
  print "Xvfb log stderr:", stderr
  with open('/tmp/screenshot.png', 'rb') as f:
    print "Dumping base64 png below:"
    print f.read().encode('base64')
  try:
    os.remove(_SCREENSHOT_FILE)
  except OSError:
    pass
  else:
    print "Removed screenshot file at " + _SCREENSHOT_FILE
