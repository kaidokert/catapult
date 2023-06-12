# Sandwich Verification

This directory hosts the source code for the Sandwich Verification module.

Before running any of the commands below, ensure you're in the
sandwich_verification folder. From the catapult root, you can run

```
cd dashboard/sandwich_verification
```

# How To Deploy To Prod
To deploy local code to production, call:

```
gcloud builds submit --region=us-central1 --config cloudbuild.yaml .
```

This will execute cloudbuild.yaml and will deploy the Cloud Workflow and all
Cloud functions in parallel. The deployed resources will have the "-prod"
suffix. (e.g. start-pinpoint-job-prod).

# Test Changes on Staging Version

## Deploying to Staging

To test local changes on your own version, you can specify a substitution for.
_VERSION. Example:

```
gcloud builds submit --region=us-central1 --config=cloudbuild.yaml --substitutions=_VERSION=eduardoyap .
```

This will deploy a workflows and functions with the provided suffix version
(e.g. sandwich-verification-workflow-eduardoyap, start-pinpoint-job-eduardoyap). You should be able to see your deployed
functions in the [Cloud Functions
dashboard](https://pantheon.corp.google.com/functions/list?referrer=search&project=chromeperf)
and [Cloud Workflow dashboard](https://pantheon.corp.google.com/workflows?referrer=search&project=chromeperf).

## Running Staging Cloud Workflow

From the Cloud Workflow dashboard, you can click on your deployed workflow
version and then on the Execute button. You can provide test data for the
Workflow to execute. For example:

```
{
    "anomaly": {
        "benchmark": "speedometer2",
        "bot_name": "mac-m1_mini_2020-perf",
        "chart": "",
        "end_git_hash": "777f2001441e9d82bad279fa84a3cb0d21eb2a9c",
        "start_git_hash": "777f2001441e9d82bad279fa84a3cb0d21eb2a9c",
        "story": "Speedometer2",
        "target": "performance_test_suite"
    },
    "mode": "testing"
}
```

Specifying the mode as "testing" will let handler callback to just log the final
results instead of sending them to a Chromeperf handler.

## Running Staging Cloud Functions

To test individual functions, you can click on the target function from the
Cloud Functions dashboard and then click on the Testing tab. You can provide
test data and the Test Command window will show you a command you can run from
your workstation. Example:

```
curl -m 70 -X POST https://poll-pinpoint-job-eduardoyap-kkdem5ntpa-uw.a.run.app \
-H "Authorization: bearer $(gcloud auth print-identity-token)" \
-H "Content-Type: application/json" \
-d '{
  "job_id": "15d9633dfa0000"
}'
```

# How To Test Locally

Prerequisites for this method:

- `functions-framework`: https://cloud.google.com/functions/docs/running/function-frameworks
- `curl`: should be installed already on most workstation environments

In one terminal window, run the following:
```
functions-framework --target GetCabeAnalysis --debug
```
This should start up a local emulation of the cloud functions environment. It
should also log some diagnostic/debug info including the http port that it's
listening on. We'll assume that port is `8080` here.

In a second terminal window, run this command (the `-d` json payload is just
some dummy data; edit as necessary for your use case):
```
curl localhost:8080 -X POST  -H "Content-Type: application/json"  -d '{"job_id":"123", "anomaly":{"chart":"AngularJS-TodoMVC"}}'
```

This should produce some output in both terminal windows, as well as generate
some server-side activity visible in the GCP console page for cabe.skia.org.
