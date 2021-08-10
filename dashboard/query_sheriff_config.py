#!/usr/bin/python

import logging
import os
import sys
import imp


def _AddToPathIfNeeded(path):
  if path not in sys.path:
    sys.path.insert(0, path)

def Main():
  logging.debug('here')
  catapult_path = os.path.abspath(
      os.path.join(os.path.dirname(__file__), '..'))

  _AddToPathIfNeeded(os.path.join(catapult_path, 'dashboard'))
  import dashboard
  paths = dashboard.PathsForDeployment()
  #print("paths: %s", paths)
  for path in paths:
    _AddToPathIfNeeded(path)

  #_AddToPathIfNeeded(os.path.join(catapult_path, 'third_party/google-auth/google'))
  #print('\n'.join(sys.path))
  import pkgutil
  for module_loader, name, ispkg in pkgutil.walk_packages():
    if 'google' in name:
      print("%s: %s, %s" % (name, ispkg, module_loader))

  #imp.find_module('google.auth', '/usr/local/google/home/seanmccullough/code/chromium_src/src/third_party/catapult/third_party/google-auth')
  #import google.auth
  #print(google.auth.__path__)
  from dashboard import sheriff_config_client
  sconf = sheriff_config_client.GetSheriffConfigClient()

if __name__ == '__main__':
  logging.basicConfig(
      stream=sys.stdout,
      level=logging.INFO,
      format='[%(asctime)s - %(levelname)s]: \t%(message)s')
  Main()

