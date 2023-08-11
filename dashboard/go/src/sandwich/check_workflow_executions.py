import json
import os

# from dashboard.dashboard.services import workflow_service

# execution = workflow_service.GetExecution("992f451a-b37c-4f8f-9c72-be2d87c3a1c8")
# results_dict = json.loads(execution['result'])
# print(results_dict)

f = open("executions.txt", "r")

jobs = []
exec_ids = []
executions = []
for line in f:
	line = line.strip()
	if line.startswith('job: \n'):
		jobs.append(line.split(' ')[-1])
	if line.startswith('gcloud'):
		executions.append(line)
		exec_ids.append(line.split('/')[-1])

f.close()

for job, exec_id, exec in zip(jobs, exec_ids, executions):
	os.system("""%s --location=us-central1 > workflow_output.txt""" % exec)
	# print(exec)
	f = open("workflow_output.txt", "r")
	decision, statistic = None, None
	for line in f:
		if line.startswith('result'):
			res = line[9:-2]
			res = json.loads(res)
			decision = res['decision']
			statistic = res['statistic']
			break
	print(job, exec_id, "Decision: ", decision, statistic)

	f.close()
