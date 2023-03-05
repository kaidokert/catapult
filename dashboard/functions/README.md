# Cloud Functions

This directory hosts the source code for production Cloud Functions in the chromeperf project.

# How To Deploy A Function
Here's an example on how to deploy/update a function from this directory:

```
gcloud functions deploy get-cabe-analysis --gen2 --runtime=python311 --region=us-west1 --source=. --entry-point=get_cabe_analysis --trigger-http --allow-unauthenticated --run-service-account=chromeperf@appspot.gserviceaccount.com
```
