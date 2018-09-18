import json

from services import request


class Api(object):
  SERVICE_URL = 'https://pinpoint-dot-chromeperf.appspot.com/api'

  def __init__(self, credentials):
    self._credentials = credentials

  def Request(self, endpoint):
    return json.loads(request.Request(
        self.SERVICE_URL + endpoint, credentials=self._credentials))

  def Jobs(self):
    return self.Request('/jobs')
