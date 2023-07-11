package main

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"sort"

	"google.golang.org/api/appengine/v1"
)

var (
	trafficYamls = map[string]string{
		"api":                "dashboard/cloudbuild_traffic/api.yaml",
		"default":            "dashboard/cloudbuild_traffic/default.yaml",
		"perf-issue-service": "perf_issue_service/cloudbuild-perf-issue-service-traffic.yaml",
		"pinpoint":           "dashboard/cloudbuild_traffic/pinpoint.yaml",
		"skia-bridge":        "skia_bridge/skia-bridge-traffic.yaml",
		"upload-processing":  "dashboard/cloudbuild_traffic/upload-processing.yaml",
		"upload":             "dashboard/cloudbuild_traffic/upload.yaml",
	}
	checkoutBase = "/usr/local/google/home/seanmccullough/code/catapult"
)

func gitHash(id string) string {
	return id[len("cloud-build-"):]
}

// Sort Versions by CreateTime such that versions[0] is the latest.
type byCreateTime []*appengine.Version

func (s byCreateTime) Len() int           { return len(s) }
func (s byCreateTime) Swap(i, j int)      { s[i], s[j] = s[j], s[i] }
func (s byCreateTime) Less(i, j int) bool { return s[i].CreateTime > s[j].CreateTime }

func liveVersion(service *appengine.Service, versions []*appengine.Version) *appengine.Version {
	for _, v := range versions {
		split := service.Split.Allocations[v.Id]
		if split == 1.0 {
			return v
		}
	}
	return nil
}

type serviceUpdate struct {
	serviceId        string
	fromHash, toHash string
	fromDate, toDate string
}

func main() {
	ctx := context.Background()
	appengineService, err := appengine.NewService(ctx)
	if err != nil {
		panic(err)
	}
	serviceListCall := appengineService.Apps.Services.List("chromeperf")
	serviceListResp, err := serviceListCall.Do()
	if err != nil {
		panic(err)
	}

	updates := []serviceUpdate{}
	for _, service := range serviceListResp.Services {
		versionsListCall := appengineService.Apps.Services.Versions.List("chromeperf", service.Id)
		versionsListResp, err := versionsListCall.Do()
		if err != nil {
			panic(err)
		}
		versions := versionsListResp.Versions
		live := liveVersion(service, versions)
		sort.Sort(byCreateTime(versions))
		latest := versions[1]

		updates = append(updates, serviceUpdate{
			serviceId: service.Id,
			fromHash:  gitHash(live.Id),
			fromDate:  live.CreateTime,
			toHash:    gitHash(latest.Id),
			toDate:    latest.CreateTime,
		})
	}

	re := regexp.MustCompile(`_SERVICE_VERSION: 'cloud-build-.*'`)

	for _, update := range updates {
		current := update.fromHash == update.toHash
		trafficYaml, ok := trafficYamls[update.serviceId]
		if !ok {
			fmt.Printf("unrecognized service, no known yaml file: %s\n", update.serviceId)
			continue
		}
		if current {
			fmt.Printf("%s\tOK\t%s:\t%s\t(%s)\n", update.serviceId, update.toHash, update.toDate)
		} else {
			yamlPath := filepath.Join(checkoutBase, trafficYaml)
			yamlBytes, err := os.ReadFile(yamlPath)
			if err != nil {
				panic(err)
			}
			yamlStr := string(yamlBytes)
			newVersionStr := fmt.Sprintf("_SERVICE_VERSION: 'cloud-build-%s'", update.toHash)
			yamlStr = re.ReplaceAllLiteralString(yamlStr, newVersionStr)
			if err := os.WriteFile(yamlPath, []byte(yamlStr), 0666); err != nil {
				panic(err)
			}
			fmt.Printf("updated %s _SERVICE_VERSION to `cloud-build-%s`\n", yamlPath, update.toHash)
		}
	}
}
