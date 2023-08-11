package main

import (
	"bufio"
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"os"

	executions "cloud.google.com/go/workflows/executions/apiv1beta"
	executionspb "cloud.google.com/go/workflows/executions/apiv1beta/executionspb"
)

var (
	app              = flag.String("app", "chromeperf", "GAE project app name")
	location         = flag.String("location", "us-central1", "location for workflow execution")
	workflowName     = flag.String("workflow", "sandwich-verification-workflow-prod", "name of workflow to execute")
	execID					 = flag.String("execution-id", "", "execution id of the workflow")
	execTextName		 = flag.String("execution-txt", "", "text file containing workflow execution IDs")
	attemptCount     = flag.Int("attempt-count", 30, "iterations verification job will run")
	dryRun           = flag.Bool("dry-run", true, "dry run; just print CreateExecutionRequest to stdout")
)

func exitWithError(err error) {
	fmt.Printf("error: %v\n", err)
	os.Exit(1)
}

func readFile(fn string) ([]string, error) {
	readFile, err := os.Open(fn)
	if err != nil {
		exitWithError(err)
	}
	
	fileScanner := bufio.NewScanner(readFile)
	fileScanner.Split(bufio.ScanLines)

	var fileLines []string
	for fileScanner.Scan() {
			fileLines = append(fileLines, fileScanner.Text())
	}

	readFile.Close()

	return fileLines, nil
}

func main() {
	flag.Parse()

	// var (
	// 	job_ids []string
	// 	exec_ids []string
	// )

	// if *execTextName != "" {
	// 	lines, err := readFile(*execTextName)
	// 	if err != nil {
	// 		exitWithError(err)
	// 	}

	// 	for _, line := range lines {
	// 		if strings.HasPrefix(line, "job"){ 
	// 			append(job_ids, line)
	// 		}
	// 		if strings.HasPrefix(line, "gcloud") { 
	// 			s := strings.Split(line, "/")
	// 			append(exec_ids, s[len(s)-1])
	// 		}
			
	// 	}
	// }

	// print(exec_ids)

	ctx := context.Background()
	executionsClient, err := executions.NewClient(ctx)
	if err != nil {
		exitWithError(err)
	}
	defer executionsClient.Close()

	req := &executionspb.GetExecutionRequest{
		// See https://pkg.go.dev/cloud.google.com/go/workflows/executions/apiv1beta/executionspb#GetExecutionRequest.
		Name: fmt.Sprintf("projects/%s/locations/%s/workflows/%s/executions/%s", 
							*app, *location, *workflowName, *execID),
	}
	resp, err := executionsClient.GetExecution(ctx, req)
	if err != nil {
		fmt.Printf("executionsClient failed to get execution %v\n", err)
	}

	var result map[string]interface{}
	err = json.Unmarshal([]byte(resp.Result), &result)
	if err != nil{
		exitWithError(err)
	}

	fmt.Printf("exec_id: %v, verification job: %v, decision: %v, statistic: %v\n",
							*execID,
							result["job_id"],
							result["decision"],
							result["statistic"])
}
