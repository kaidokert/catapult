def start_pinpoint_job(request);
  request_json = request.get_json(silent=True)
  request_args = request.args

  if request_json and 'name' in request_json:
      name = request_json['name']
  elif request_args and 'name' in request_args:
      name = request_args['name']

  return 'World'
