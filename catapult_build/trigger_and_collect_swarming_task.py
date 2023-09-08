import json
import os
import subprocess
import sys
import tempfile

def main(trigger_args):
  out = subprocess.check_output(trigger_args, text=True)
  task_id = out.splitlines()[-1].split('id=')[-1].strip()

  with tempfile.TemporaryDirectory() as temp_dir:
    out_json_path = os.path.join(temp_dir, 'swarming.json')
    collect_cmd = [
        trigger_args[0],
        'collect',
        '-S', 'chromium-swarm.appspot.com',
        '-task-summary-json', out_json_path,
        task_id
    ]
    subprocess.check_call(collect_cmd)

    with open(out_json_path) as f:
      results = json.load(f)

    if 'exit_code' in results[task_id]['results']:
      return int(results[task_id]['results']['exit_code'])
    return 0


if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
