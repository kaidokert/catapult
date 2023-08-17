#!/bin/bash

job_ids="job_input.txt"
while IFS= read -r job
do
  echo "job: " $job
  go run sandwich.go -pinpoint-job-id $job -dry-run=False
done < "$job_ids"

