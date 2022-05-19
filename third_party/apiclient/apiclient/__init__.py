"""Retain apiclient as an alias for googleapiclient."""

from __future__ import absolute_import

from six import iteritems

import apiclient.googleapiclient as googleapiclient

try:
  import oauth2client.oauth2client
except ImportError:
  raise RuntimeError(
      'Previous version of google-api-python-client detected; due to a '
      'packaging issue, we cannot perform an in-place upgrade. To repair, '
      'remove and reinstall this package, along with oauth2client and '
      'uritemplate. One can do this with pip via\n'
      '  pip install -I google-api-python-client'
  )

from apiclient.googleapiclient import channel
from apiclient.googleapiclient import discovery
from apiclient.googleapiclient import errors
from apiclient.googleapiclient import http
from apiclient.googleapiclient import mimeparse
from apiclient.googleapiclient import model
from apiclient.googleapiclient import sample_tools
from apiclient.googleapiclient import schema

__version__ = googleapiclient.__version__

_SUBMODULES = {
    'channel': channel,
    'discovery': discovery,
    'errors': errors,
    'http': http,
    'mimeparse': mimeparse,
    'model': model,
    'sample_tools': sample_tools,
    'schema': schema,
}

import sys
for module_name, module in iteritems(_SUBMODULES):
  sys.modules['apiclient.%s' % module_name] = module
