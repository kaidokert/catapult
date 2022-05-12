#!/usr/bin/env python3
# Copyright 2015 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


class MouseClickAction(object):

  def WillRunAction(self, tab):
    """Load the mouse click JS code prior to running the action."""
    super(MouseClickAction, self).WillRunAction(tab)
    utils.InjectJavaScript(tab, 'mouse_click.js')
    tab.ExecuteJavaScript("""
        window.__mouseClickActionDone = false;
        window.__mouseClickAction = new __MouseClickAction(function() {
          window.__mouseClickActionDone = true;
        });""")

  def RunAction(self, tab):
    code = '''
        function(element, info) {
          if (!element) {
            throw Error('Cannot find element: ' + info);
          }
          window.__mouseClickAction.start({
            element: element
          });
        }'''
    self.EvaluateCallback(tab, code)
    tab.WaitForJavaScriptCondition(
        'window.__mouseClickActionDone', timeout=self.timeout)
