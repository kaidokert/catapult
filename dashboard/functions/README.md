# Cloud Functions

This directory hosts the source code for production Cloud Functions in the chromeperf project.

# How To Deploy Functions
To manually deploy all functions in this library, call:

```
gcloud builds submit --region=us-central1 --config cloudbuild.yaml .
```

This will execute cloudbuild.yaml and will deploy all functions in parallel.

# How To Test Locally

Prerequisites for this method:

- Install `functions-framework`: https://cloud.google.com/functions/docs/running/function-frameworks
  - This method is not intended to play nicely with vpython or venv or other python package resolution hacks.  It just uses pip.
  - you may need to install `pip` first (e.g. on a cloudtop where it may not be there already)
  - you may need to run the `pip install` command with `--break-system-packages` to get around an error message
  - e.g. `pip install -r requirements.txt --break-system-packages` from this directory
- `curl`: should be installed already on most workstation environments
- Install `gcloud` and whatever else it requires these days.
- Run `gcloud auth application-default login` so that the `functions-framework` dev server can add
  auth credentials to cabe.skia.org grpc requests (you'll get some cryptic errors if you don't do this).

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
some server-side activity visible in the GCP console page for cabe.skia.org. The
request logs for the `cabeserver` pod should also contain some evidence of it
handling the request from your local `functions-framework` devserver.
