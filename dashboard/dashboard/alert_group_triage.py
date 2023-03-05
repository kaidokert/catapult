from flask import make_response, request

from dashboard.models import alert_group_workflow

def AlertGroupTriagePost():
  """Triages new regressions.

  Request parameters:
    anomaly
    update
    group
  Outputs:
  """

  group_key = request.values.get('group_key')
  verification = request.values.get('verification')
  update = request.values.get('update')

  workflow = alert_group_workflow.AlertGroupWorkflow(group_key, verification=verification)
  logging.info('Processing verified group: %s', group_key.string_id())
  workflow.Process(update=update)

  return make_response('OK')
