# Copyright (c) 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import json
import requests
import shutil
import sys
from io import BytesIO

from telemetry.core import util
from telemetry.internal.browser import browser_finder


def _TransmitLargeJSONToTab(tab, json_obj, js_holder_name):
  tab.ExecuteJavaScript(
      'var {{ @js_holder_name }} = "";', js_holder_name=js_holder_name)

  # To avoid crashing devtool connection (details in crbug.com/763119#c16),
  # we break down the json string to chunks which each chunk has a maximum
  # size of 100000 characters (100000 seems to not break the connection and
  # makes sending data reasonably fast).
  k = 0
  step_size = 100000
  json_obj_string = json.dumps(json_obj)
  while k < len(json_obj_string):
    sub_string_chunk = json_obj_string[k: k + step_size]
    k += step_size
    tab.ExecuteJavaScript(
        '{{ @js_holder_name }} += {{ sub_string_chunk }};',
        js_holder_name=js_holder_name, sub_string_chunk=sub_string_chunk)

  tab.ExecuteJavaScript(
      '{{ @js_holder_name }} = JSON.parse({{ @js_holder_name }});',
      js_holder_name=js_holder_name)


def _FetchImages(snapshot_path, external_images):
  if (len(external_images) == 0):
    return

  image_dir_relpath = os.path.basename(snapshot_path)
  image_dir = os.path.abspath(image_dir_relpath[:image_dir_relpath.rfind('.html')])

  image_count = len(external_images)
  sys.stdout.write('Fetching external images [local_dir=%s, image_count=%d].\n' % (image_dir, image_count))

  for i in xrange(image_count):
    sys.stdout.write('Fetching image #%i / %i\r' % (i, image_count))
    sys.stdout.flush()
    [ element_id, image_url ] = external_images[i]

    # TODO(wkorman): Handle http or file i/o errors gracefully.
    image_request = requests.get(image_url)
    _, image_file_extension = os.path.splitext(image_url)
    # TODO(wkorman): May need to include frame index to uniquify by element id safely.
    image_file = os.path.join(image_dir, element_id + image_file_extension)
    sys.stdout.write('Fetch image [local_file=%s, url=%s].\n' % (image_file, image_url))

    if not os.path.exists(image_dir):
      os.mkdir(image_dir)

    with open(image_file, 'wb') as image_file_handle:
      shutil.copyfileobj(BytesIO(image_request.content), image_file_handle)


def SnapPage(finder_options, url, interactive, snapshot_path, snapshot_file):
  """ Save the HTML snapshot of the page whose address is |url| to
  |snapshot_file|.
  """
  possible_browser = browser_finder.FindBrowser(finder_options)
  browser = possible_browser.Create(finder_options)
  try:
    tab = browser.tabs[0]
    tab.Navigate(url)
    if interactive:
      raw_input(
          'Activating interactive mode. Press enter after you finish '
          "interacting with the page to snapshot the page's DOM content.")

    sys.stdout.write(
        'Snapshotting content of %s. This could take a while...\n' % url)
    tab.WaitForDocumentReadyStateToBeComplete()
    tab.action_runner.WaitForNetworkQuiescence()

    with open(os.path.join(util.GetCatapultThirdPartyDir(), 'snap-it',
                           'HTMLSerializer.js')) as f:
      snapit_script = f.read()

    with open(os.path.join(util.GetCatapultThirdPartyDir(), 'snap-it',
                           'popup.js')) as f:
      dom_combining_script = f.read()

    serialized_doms = []
    external_images = []

    # Serialize the dom in each frame.
    for context_id in tab.EnableAllContexts():
      tab.ExecuteJavaScript(snapit_script, context_id=context_id)
      tab.ExecuteJavaScript(
          '''
          var serializedDom;
          var htmlSerializer = new HTMLSerializer();
          htmlSerializer.processDocument(document);
          htmlSerializer.fillHolesAsync(document, function(s) {
            serializedDom = s.asDict();
          });
          ''', context_id=context_id)
      tab.WaitForJavaScriptCondition(
          'serializedDom !== undefined', context_id=context_id)
      serialized_doms.append(tab.EvaluateJavaScript(
          'serializedDom', context_id=context_id))
      external_images.append(tab.EvaluateJavaScript(
          'htmlSerializer.externalImages', context_id=context_id))

    # Execute doms combining code in blank page to minimize the chance of V8
    # OOM.
    tab.Navigate('about:blank')
    tab.WaitForDocumentReadyStateToBeComplete()

    # Sending all the serialized doms back to tab execution context.
    tab.ExecuteJavaScript('var serializedDoms = [];')
    for i in xrange(len(serialized_doms)):
      sys.stdout.write('Processing dom of frame #%i / %i\r' %
                       (i, len(serialized_doms)))
      sys.stdout.flush()
      _TransmitLargeJSONToTab(tab, serialized_doms[i], 'sub_dom')
      tab.ExecuteJavaScript('serializedDoms.push(sub_dom);')

    # Combine all the doms to one HTML string.
    tab.EvaluateJavaScript(dom_combining_script)
    page_snapshot = tab.EvaluateJavaScript('outputHTMLString(serializedDoms);')

    sys.stdout.write('Writing page snapshot [path=%s].\n' % (snapshot_path))
    snapshot_file.write(page_snapshot)

    for i in xrange(len(external_images)):
      _FetchImages(snapshot_path, external_images[i])

  finally:
    browser.Close()
