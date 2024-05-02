# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import json

from flask import make_response, request

from dashboard.common import cloud_metric
from dashboard.pinpoint.models import job as job_module


@cloud_metric.APIMetric("pinpoint", "/api/job")
def JobHandlerGet(job_id):
  try:
    job = job_module.JobFromId(job_id)
  except ValueError:
    return make_response(
        json.dumps({'error': 'Invalid job id: %s' % job_id}), 400)

  if not job:
    return make_response(
        json.dumps({'error': 'Unknown job id: %s' % job_id}), 404)

  opts = request.args.getlist('o')
  return make_response(json.dumps(job.AsDict(opts)))

def JobHandlerGetSample(job_id):
  try:
    return make_response(json.dumps(getData()))
  except:
    return make_response(
      json.dumps({'error': 'Unknown job id: %s' % job_id}), 404)

def getData():
  return {
    "job_id": "142784c0800000",
    "configuration": "linux-perf",
    "results_url": "https://storage.cloud.google.com/chromeperf-staging-results2-public/142784c0800000.html",
    "improvement_direction": 4,
    "arguments": {
      "comparison_mode": "performance",
      "target": "performance_test_suite",
      "start_git_hash": "e23f04cc817fe8869244e9b23b4d78f31edc7d59",
      "end_git_hash": "1d2f58d918347f16020dbb4e74149a99b0f2883b",
      "performance": "on",
      "initial_attempt_count": "10",
      "configuration": "linux-perf",
      "benchmark": "system_health.memory_desktop",
      "story": "load:search:taobao:2018",
      "story_tags": "",
      "chart": "memory:chrome:all_processes:reported_by_chrome:blink_gc:allocated_objects_size",
      "statistic": "avg",
      "comparison_magnitude": "2600000",
      "extra_test_args": "",
      "pin": "",
      "project": "chromium",
      "bug_id": "1475089",
      "batch_id": ""
    },
    "bug_id": 1475089,
    "project": "chromium",
    "comparison_mode": "performance",
    "name": "proof of concept",
    "user": "sunxiaodi@google.com",
    # "created": "2023-08-29T00:08:14.265005",
    # "updated": "2023-08-29T00:16:26.445010",
    # "started_time": "2023-08-29T00:09:01.431095",
    "created": "2024-05-01T21:37:33.238964",
    "updated": "2024-05-01T24:37:33.238964",
    "started_time": "2024-05-01T22:37:33.238964",
    "difference_count": 1,
    "exception": None,
    "status": "Completed",
    "cancel_reason": None,
    "batch_id": "ba165bb7-0792-427f-8474-23138729cf82",
    "bots": [
      "lin-10-g582",
      "lin-1-g582",
      "lin-7-g582",
      "lin-20-g582",
      "lin-2-g582",
      "lin-18-g582",
      "lin-11-g582",
      "lin-6-g582",
      "lin-17-g582",
      "lin-9-g582",
      "lin-8-g582",
      "lin-14-g582",
      "lin-4-g582",
      "lin-15-g582",
      "lin-12-g582",
      "lin-19-g582",
      "lin-5-g582",
      "lin-3-g582",
      "lin-13-g582",
      "lin-16-g582"
    ],
    "metric": "memory:chrome:all_processes:reported_by_chrome:blink_gc:allocated_objects_size",
    "quests": [
      "Build",
      "Test",
      "Get values"
    ],
    "state": [
      {
        "change": {
          "commits": [
            {
              "repository": "chromium",
              "git_hash": "e23f04cc817fe8869244e9b23b4d78f31edc7d59",
              "url": "https://chromium.googlesource.com/chromium/src/+/e23f04cc817fe8869244e9b23b4d78f31edc7d59",
              "author": "ktrajkovski@google.com",
              "created": "2023-07-14T14:39:48",
              "subject": "Add a test which checks username vote type and new vote type matcher",
              "message": "Add a test which checks username vote type and new vote type matcher\n\nThe currently available tests do not cover username changes:\noverwriting, editing, and reusing as thoroughly. Therefore a\nthree new tests were added together with a new matcher to detect an overwrite, reuse, or edit.\n\nTODO: confirm editing function\n\nBug: 1451740\nChange-Id: I76bc3a1c00e9d427eaeec730b7238c2e22bb08e2\nReviewed-on: https://chromium-review.googlesource.com/c/chromium/src/+/4679176\nCode-Coverage: Findit \nReviewed-by: Din Nezametdinov \nCommit-Queue: Kristina Trajkovski \nReviewed-by: Maxim Kolosovskiy \nCommit-Queue: Maxim Kolosovskiy \nCr-Commit-Position: refs/heads/main@{#1170506}\n",
              "commit_branch": "refs/heads/main",
              "commit_position": 1170506,
              "review_url": "https://chromium-review.googlesource.com/c/chromium/src/+/4679176",
              "change_id": "I76bc3a1c00e9d427eaeec730b7238c2e22bb08e2"
            }
          ]
        },
        "attempts": [
          {
            "executions": [
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "builder",
                    "value": "Linux Builder Perf"
                  },
                  {
                    "key": "isolate",
                    "value": "82771489827a7e8dc9bbe14a87dfaa62a9566fd7d8bddd7883f33aec77b3afda/1294",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/82771489827a7e8dc9bbe14a87dfaa62a9566fd7d8bddd7883f33aec77b3afda/1294/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "bot",
                    "value": "lin-4-g582",
                    "url": "https://chrome-swarming.appspot.com/bot?id=lin-4-g582"
                  },
                  {
                    "key": "task",
                    "value": "645772aba59ef710",
                    "url": "https://chrome-swarming.appspot.com/task?id=645772aba59ef710"
                  },
                  {
                    "key": "isolate",
                    "value": "f90acb9b8b8d46c859f5c09fefe579a730bc1112fdf78af92f2681e884dad3a7/189",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/f90acb9b8b8d46c859f5c09fefe579a730bc1112fdf78af92f2681e884dad3a7/189/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "trace",
                    "value": "load:search:taobao:2018",
                    "url": "https://storage.cloud.google.com/chrome-telemetry-output/chromium_e23f04c_20230829T001110_24301/system_health.memory_desktop/load_search_taobao_2018/retry_0/trace.html"
                  }
                ]
              }
            ]
          },
          {
            "executions": [
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "builder",
                    "value": "Linux Builder Perf"
                  },
                  {
                    "key": "isolate",
                    "value": "82771489827a7e8dc9bbe14a87dfaa62a9566fd7d8bddd7883f33aec77b3afda/1294",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/82771489827a7e8dc9bbe14a87dfaa62a9566fd7d8bddd7883f33aec77b3afda/1294/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "bot",
                    "value": "lin-19-g582",
                    "url": "https://chrome-swarming.appspot.com/bot?id=lin-19-g582"
                  },
                  {
                    "key": "task",
                    "value": "645772ac987afb10",
                    "url": "https://chrome-swarming.appspot.com/task?id=645772ac987afb10"
                  },
                  {
                    "key": "isolate",
                    "value": "0539c330eef7678ea116705e798af3e463ae5afc5cbf354c2e3c1ddc8c5a1c16/189",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/0539c330eef7678ea116705e798af3e463ae5afc5cbf354c2e3c1ddc8c5a1c16/189/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "trace",
                    "value": "load:search:taobao:2018",
                    "url": "https://storage.cloud.google.com/chrome-telemetry-output/chromium_e23f04c_20230829T001112_35382/system_health.memory_desktop/load_search_taobao_2018/retry_0/trace.html"
                  }
                ]
              }
            ]
          },
          {
            "executions": [
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "builder",
                    "value": "Linux Builder Perf"
                  },
                  {
                    "key": "isolate",
                    "value": "82771489827a7e8dc9bbe14a87dfaa62a9566fd7d8bddd7883f33aec77b3afda/1294",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/82771489827a7e8dc9bbe14a87dfaa62a9566fd7d8bddd7883f33aec77b3afda/1294/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "bot",
                    "value": "lin-6-g582",
                    "url": "https://chrome-swarming.appspot.com/bot?id=lin-6-g582"
                  },
                  {
                    "key": "task",
                    "value": "645772ae4214c310",
                    "url": "https://chrome-swarming.appspot.com/task?id=645772ae4214c310"
                  },
                  {
                    "key": "isolate",
                    "value": "20fdfeb2a35185d63ddf43a87cdc6a3f969f9b9d0128e6322593efb9a8128844/189",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/20fdfeb2a35185d63ddf43a87cdc6a3f969f9b9d0128e6322593efb9a8128844/189/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "trace",
                    "value": "load:search:taobao:2018",
                    "url": "https://storage.cloud.google.com/chrome-telemetry-output/chromium_e23f04c_20230829T001113_64517/system_health.memory_desktop/load_search_taobao_2018/retry_0/trace.html"
                  }
                ]
              }
            ]
          },
          {
            "executions": [
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "builder",
                    "value": "Linux Builder Perf"
                  },
                  {
                    "key": "isolate",
                    "value": "82771489827a7e8dc9bbe14a87dfaa62a9566fd7d8bddd7883f33aec77b3afda/1294",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/82771489827a7e8dc9bbe14a87dfaa62a9566fd7d8bddd7883f33aec77b3afda/1294/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "bot",
                    "value": "lin-15-g582",
                    "url": "https://chrome-swarming.appspot.com/bot?id=lin-15-g582"
                  },
                  {
                    "key": "task",
                    "value": "645772af823ee010",
                    "url": "https://chrome-swarming.appspot.com/task?id=645772af823ee010"
                  },
                  {
                    "key": "isolate",
                    "value": "eb2211fb9e4a95d8c067e1446f354f88c7915a23223d9b0b136d1db98ca0df92/189",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/eb2211fb9e4a95d8c067e1446f354f88c7915a23223d9b0b136d1db98ca0df92/189/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "trace",
                    "value": "load:search:taobao:2018",
                    "url": "https://storage.cloud.google.com/chrome-telemetry-output/chromium_e23f04c_20230829T001133_66547/system_health.memory_desktop/load_search_taobao_2018/retry_0/trace.html"
                  }
                ]
              }
            ]
          },
          {
            "executions": [
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "builder",
                    "value": "Linux Builder Perf"
                  },
                  {
                    "key": "isolate",
                    "value": "82771489827a7e8dc9bbe14a87dfaa62a9566fd7d8bddd7883f33aec77b3afda/1294",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/82771489827a7e8dc9bbe14a87dfaa62a9566fd7d8bddd7883f33aec77b3afda/1294/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "bot",
                    "value": "lin-2-g582",
                    "url": "https://chrome-swarming.appspot.com/bot?id=lin-2-g582"
                  },
                  {
                    "key": "task",
                    "value": "645772b1fac97b10",
                    "url": "https://chrome-swarming.appspot.com/task?id=645772b1fac97b10"
                  },
                  {
                    "key": "isolate",
                    "value": "d7ddbf6dbf88e19f83ddc2ee14053037bea135bbf4116dff5d8d3b573b21678c/189",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/d7ddbf6dbf88e19f83ddc2ee14053037bea135bbf4116dff5d8d3b573b21678c/189/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "trace",
                    "value": "load:search:taobao:2018",
                    "url": "https://storage.cloud.google.com/chrome-telemetry-output/chromium_e23f04c_20230829T001115_66437/system_health.memory_desktop/load_search_taobao_2018/retry_0/trace.html"
                  }
                ]
              }
            ]
          },
          {
            "executions": [
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "builder",
                    "value": "Linux Builder Perf"
                  },
                  {
                    "key": "isolate",
                    "value": "82771489827a7e8dc9bbe14a87dfaa62a9566fd7d8bddd7883f33aec77b3afda/1294",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/82771489827a7e8dc9bbe14a87dfaa62a9566fd7d8bddd7883f33aec77b3afda/1294/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "bot",
                    "value": "lin-13-g582",
                    "url": "https://chrome-swarming.appspot.com/bot?id=lin-13-g582"
                  },
                  {
                    "key": "task",
                    "value": "645772b2fdf43510",
                    "url": "https://chrome-swarming.appspot.com/task?id=645772b2fdf43510"
                  },
                  {
                    "key": "isolate",
                    "value": "1059861aae3bd1f881b81d580882fc2fa023eaf49bfbd5349e8ca202b2e64d08/189",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/1059861aae3bd1f881b81d580882fc2fa023eaf49bfbd5349e8ca202b2e64d08/189/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "trace",
                    "value": "load:search:taobao:2018",
                    "url": "https://storage.cloud.google.com/chrome-telemetry-output/chromium_e23f04c_20230829T001116_46030/system_health.memory_desktop/load_search_taobao_2018/retry_0/trace.html"
                  }
                ]
              }
            ]
          },
          {
            "executions": [
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "builder",
                    "value": "Linux Builder Perf"
                  },
                  {
                    "key": "isolate",
                    "value": "82771489827a7e8dc9bbe14a87dfaa62a9566fd7d8bddd7883f33aec77b3afda/1294",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/82771489827a7e8dc9bbe14a87dfaa62a9566fd7d8bddd7883f33aec77b3afda/1294/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "bot",
                    "value": "lin-16-g582",
                    "url": "https://chrome-swarming.appspot.com/bot?id=lin-16-g582"
                  },
                  {
                    "key": "task",
                    "value": "645772b3e0532b10",
                    "url": "https://chrome-swarming.appspot.com/task?id=645772b3e0532b10"
                  },
                  {
                    "key": "isolate",
                    "value": "22032074fe5323f0465ba73c57ab47e1425c6d5dbd3682102f031ddcce6e5ceb/189",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/22032074fe5323f0465ba73c57ab47e1425c6d5dbd3682102f031ddcce6e5ceb/189/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "trace",
                    "value": "load:search:taobao:2018",
                    "url": "https://storage.cloud.google.com/chrome-telemetry-output/chromium_e23f04c_20230829T001118_65348/system_health.memory_desktop/load_search_taobao_2018/retry_0/trace.html"
                  }
                ]
              }
            ]
          },
          {
            "executions": [
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "builder",
                    "value": "Linux Builder Perf"
                  },
                  {
                    "key": "isolate",
                    "value": "82771489827a7e8dc9bbe14a87dfaa62a9566fd7d8bddd7883f33aec77b3afda/1294",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/82771489827a7e8dc9bbe14a87dfaa62a9566fd7d8bddd7883f33aec77b3afda/1294/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "bot",
                    "value": "lin-14-g582",
                    "url": "https://chrome-swarming.appspot.com/bot?id=lin-14-g582"
                  },
                  {
                    "key": "task",
                    "value": "645772b523729410",
                    "url": "https://chrome-swarming.appspot.com/task?id=645772b523729410"
                  },
                  {
                    "key": "isolate",
                    "value": "b0feff690dbab51793a094c07620069011637ee43b647d44841b086a356ba2ff/189",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/b0feff690dbab51793a094c07620069011637ee43b647d44841b086a356ba2ff/189/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "trace",
                    "value": "load:search:taobao:2018",
                    "url": "https://storage.cloud.google.com/chrome-telemetry-output/chromium_e23f04c_20230829T001120_44538/system_health.memory_desktop/load_search_taobao_2018/retry_0/trace.html"
                  }
                ]
              }
            ]
          },
          {
            "executions": [
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "builder",
                    "value": "Linux Builder Perf"
                  },
                  {
                    "key": "isolate",
                    "value": "82771489827a7e8dc9bbe14a87dfaa62a9566fd7d8bddd7883f33aec77b3afda/1294",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/82771489827a7e8dc9bbe14a87dfaa62a9566fd7d8bddd7883f33aec77b3afda/1294/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "bot",
                    "value": "lin-20-g582",
                    "url": "https://chrome-swarming.appspot.com/bot?id=lin-20-g582"
                  },
                  {
                    "key": "task",
                    "value": "645772b6279cda10",
                    "url": "https://chrome-swarming.appspot.com/task?id=645772b6279cda10"
                  },
                  {
                    "key": "isolate",
                    "value": "43340c25dae117b07e000e7fbcbbb69162f3814fac771b60c4aff657aaa8b2ad/189",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/43340c25dae117b07e000e7fbcbbb69162f3814fac771b60c4aff657aaa8b2ad/189/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "trace",
                    "value": "load:search:taobao:2018",
                    "url": "https://storage.cloud.google.com/chrome-telemetry-output/chromium_e23f04c_20230829T001122_31394/system_health.memory_desktop/load_search_taobao_2018/retry_0/trace.html"
                  }
                ]
              }
            ]
          },
          {
            "executions": [
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "builder",
                    "value": "Linux Builder Perf"
                  },
                  {
                    "key": "isolate",
                    "value": "82771489827a7e8dc9bbe14a87dfaa62a9566fd7d8bddd7883f33aec77b3afda/1294",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/82771489827a7e8dc9bbe14a87dfaa62a9566fd7d8bddd7883f33aec77b3afda/1294/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "bot",
                    "value": "lin-10-g582",
                    "url": "https://chrome-swarming.appspot.com/bot?id=lin-10-g582"
                  },
                  {
                    "key": "task",
                    "value": "645772b78d15fc10",
                    "url": "https://chrome-swarming.appspot.com/task?id=645772b78d15fc10"
                  },
                  {
                    "key": "isolate",
                    "value": "826668c8989d254d1a786e70f993d942457ef1aedc1ab2087f3c8d3472ba2034/189",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/826668c8989d254d1a786e70f993d942457ef1aedc1ab2087f3c8d3472ba2034/189/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "trace",
                    "value": "load:search:taobao:2018",
                    "url": "https://storage.cloud.google.com/chrome-telemetry-output/chromium_e23f04c_20230829T001122_3688/system_health.memory_desktop/load_search_taobao_2018/retry_0/trace.html"
                  }
                ]
              }
            ]
          }
        ],
        "comparisons": {
          "next": "different"
        },
        "result_values": [
          3660464,
          3659464,
          3659720,
          3658808,
          3659672,
          3659240,
          3659328,
          3658896,
          3660352,
          3659600
        ]
      },
      {
        "change": {
          "commits": [
            {
              "repository": "chromium",
              "git_hash": "1d2f58d918347f16020dbb4e74149a99b0f2883b",
              "url": "https://chromium.googlesource.com/chromium/src/+/1d2f58d918347f16020dbb4e74149a99b0f2883b",
              "author": "chromium-autoroll@skia-public.iam.gserviceaccount.com",
              "created": "2023-06-28T20:09:20",
              "subject": "Roll Chromite from 10c93dae401a to 350ac15f852f (26 revisions)",
              "message": "Roll Chromite from 10c93dae401a to 350ac15f852f (26 revisions)\n\nhttps://chromium.googlesource.com/chromiumos/chromite.git/+log/10c93dae401a..350ac15f852f\n\n2023-06-28 chromeos-ci-prod@chromeos-bot.iam.gserviceaccount.com Automated Commit: Updated config generated by config-updater builder.\n2023-06-28 oka@google.com ide: Refactor platform2 e2e test with generator\n2023-06-28 oka@google.com ide: Fix or disable with reasons failing e2e tests\n2023-06-28 chromeos-ci-prod@chromeos-bot.iam.gserviceaccount.com Automated Commit: Updated config generated by config-updater builder.\n2023-06-28 oka@google.com ide: Add README to test/manual/ telling it's deprecated\n2023-06-28 oka@google.com ide: Add basic e2e tests for platform2 xrefs\n2023-06-28 oka@google.com ide: Add scaffolding of E2E tests suite\n2023-06-28 vapier@chromium.org cbuildbot: delete unused build_all_with_goma\n2023-06-28 kimjae@chromium.org lib: Add PaygenPayload `Run` tests for OS+miniOS\n2023-06-28 chromeos-ci-prod@chromeos-bot.iam.gserviceaccount.com Automated Commit: Updated config generated by config-updater builder.\n2023-06-27 vapier@chromium.org cbuildbot: delete unused chrome_sdk_goma\n2023-06-27 briannorris@chromium.org paygen: Correct paygen_payload_lib.GenerateUpdatePayload() signature\n2023-06-27 vapier@chromium.org config: drop EOL/dead boards\n2023-06-27 vapier@chromium.org cbuildbot: delete unused use_chrome_lkgm\n2023-06-27 vapier@chromium.org cbuildbot: delete unused GetChildConfigListMetadata\n2023-06-27 chromeos-ci-prod@chromeos-bot.iam.gserviceaccount.com Automated Commit: Updated config generated by config-updater builder.\n2023-06-27 vapier@chromium.org cbuildbot: delete unused ChildBuilderRun class\n2023-06-27 vapier@chromium.org lib: workon_helper: fix ebuild double parsing\n2023-06-27 vapier@chromium.org lib: remote_access: add a mkdir API\n2023-06-27 vapier@chromium.org fix a few more random lints\n2023-06-27 vapier@chromium.org cbuildbot: delete unused separate_debug_symbols\n2023-06-27 vapier@chromium.org cbuildbot: inline GetBuilderIds\n2023-06-27 vapier@chromium.org config: drop payload builders\n2023-06-27 vapier@chromium.org cbuildbot: delete unused paygen_skip_delta_payloads\n2023-06-27 gredelston@google.com SdkService/BuildSdkToolchain: Run inside chroot\n2023-06-27 vapier@chromium.org config: drop chell chrome uprev builder\n\nIf this roll has caused a breakage, revert this CL and stop the roller\nusing the controls here:\nhttps://autoroll.skia.org/r/chromite-chromium-autoroll\nPlease CC chrome-os-gardeners-reviews@google.com,chrome-os-gardeners@google.com,chromeos-velocity@google.com on the revert to ensure that a human\nis aware of the problem.\n\nTo file a bug in Chromium: https://bugs.chromium.org/p/chromium/issues/entry\n\nTo report a problem with the AutoRoller itself, please file a bug:\nhttps://bugs.chromium.org/p/skia/issues/entry?template=Autoroller+Bug\n\nDocumentation for the AutoRoller is here:\nhttps://skia.googlesource.com/buildbot/+doc/main/autoroll/README.md\n\nCq-Include-Trybots: luci.chrome.try:chromeos-betty-pi-arc-chrome\nTbr: chrome-os-gardeners-reviews@google.com\nChange-Id: I0a692addc45545569b2a97948353e5a59dee49df\nReviewed-on: https://chromium-review.googlesource.com/c/chromium/src/+/4653466\nCommit-Queue: chromium-autoroll \nBot-Commit: chromium-autoroll \nCr-Commit-Position: refs/heads/main@{#1163736}\n",
              "commit_branch": "refs/heads/main",
              "commit_position": 1163736,
              "review_url": "https://chromium-review.googlesource.com/c/chromium/src/+/4653466",
              "change_id": "I0a692addc45545569b2a97948353e5a59dee49df"
            }
          ]
        },
        "attempts": [
          {
            "executions": [
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "builder",
                    "value": "Linux Builder Perf"
                  },
                  {
                    "key": "isolate",
                    "value": "4b8d546ab5c0d8f2a8ca3297ae4baa7877a54555de659ba322e75060933f065a/1294",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/4b8d546ab5c0d8f2a8ca3297ae4baa7877a54555de659ba322e75060933f065a/1294/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "bot",
                    "value": "lin-8-g582",
                    "url": "https://chrome-swarming.appspot.com/bot?id=lin-8-g582"
                  },
                  {
                    "key": "task",
                    "value": "645772b8dc6e1610",
                    "url": "https://chrome-swarming.appspot.com/task?id=645772b8dc6e1610"
                  },
                  {
                    "key": "isolate",
                    "value": "5a32b38b9887fa965b27357336f43b012abc295a02eb06946828ee9c5498d0df/189",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/5a32b38b9887fa965b27357336f43b012abc295a02eb06946828ee9c5498d0df/189/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "trace",
                    "value": "load:search:taobao:2018",
                    "url": "https://storage.cloud.google.com/chrome-telemetry-output/chromium_1d2f58d_20230829T001124_94499/system_health.memory_desktop/load_search_taobao_2018/retry_0/trace.html"
                  }
                ]
              }
            ]
          },
          {
            "executions": [
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "builder",
                    "value": "Linux Builder Perf"
                  },
                  {
                    "key": "isolate",
                    "value": "4b8d546ab5c0d8f2a8ca3297ae4baa7877a54555de659ba322e75060933f065a/1294",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/4b8d546ab5c0d8f2a8ca3297ae4baa7877a54555de659ba322e75060933f065a/1294/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "bot",
                    "value": "lin-9-g582",
                    "url": "https://chrome-swarming.appspot.com/bot?id=lin-9-g582"
                  },
                  {
                    "key": "task",
                    "value": "645772ba45081e10",
                    "url": "https://chrome-swarming.appspot.com/task?id=645772ba45081e10"
                  },
                  {
                    "key": "isolate",
                    "value": "a7d27f4ca529a5d842ea4bed6d5c4bfdcb8b539c81d0b105fde7535bd90476b9/189",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/a7d27f4ca529a5d842ea4bed6d5c4bfdcb8b539c81d0b105fde7535bd90476b9/189/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "trace",
                    "value": "load:search:taobao:2018",
                    "url": "https://storage.cloud.google.com/chrome-telemetry-output/chromium_1d2f58d_20230829T001128_78819/system_health.memory_desktop/load_search_taobao_2018/retry_0/trace.html"
                  }
                ]
              }
            ]
          },
          {
            "executions": [
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "builder",
                    "value": "Linux Builder Perf"
                  },
                  {
                    "key": "isolate",
                    "value": "4b8d546ab5c0d8f2a8ca3297ae4baa7877a54555de659ba322e75060933f065a/1294",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/4b8d546ab5c0d8f2a8ca3297ae4baa7877a54555de659ba322e75060933f065a/1294/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "bot",
                    "value": "lin-3-g582",
                    "url": "https://chrome-swarming.appspot.com/bot?id=lin-3-g582"
                  },
                  {
                    "key": "task",
                    "value": "645772bb4bd29210",
                    "url": "https://chrome-swarming.appspot.com/task?id=645772bb4bd29210"
                  },
                  {
                    "key": "isolate",
                    "value": "181a3a6b6d31c7406205f1f6700e4826b425aae79d86b3f4381d849438616faf/189",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/181a3a6b6d31c7406205f1f6700e4826b425aae79d86b3f4381d849438616faf/189/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "trace",
                    "value": "load:search:taobao:2018",
                    "url": "https://storage.cloud.google.com/chrome-telemetry-output/chromium_1d2f58d_20230829T001128_45279/system_health.memory_desktop/load_search_taobao_2018/retry_0/trace.html"
                  }
                ]
              }
            ]
          },
          {
            "executions": [
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "builder",
                    "value": "Linux Builder Perf"
                  },
                  {
                    "key": "isolate",
                    "value": "4b8d546ab5c0d8f2a8ca3297ae4baa7877a54555de659ba322e75060933f065a/1294",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/4b8d546ab5c0d8f2a8ca3297ae4baa7877a54555de659ba322e75060933f065a/1294/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "bot",
                    "value": "lin-4-g582",
                    "url": "https://chrome-swarming.appspot.com/bot?id=lin-4-g582"
                  },
                  {
                    "key": "task",
                    "value": "645772bc5fba1510",
                    "url": "https://chrome-swarming.appspot.com/task?id=645772bc5fba1510"
                  },
                  {
                    "key": "isolate",
                    "value": "a3dadc278971c185a968485e95e961ffe368a567d1842b16b71bb7b8ee277829/189",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/a3dadc278971c185a968485e95e961ffe368a567d1842b16b71bb7b8ee277829/189/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "trace",
                    "value": "load:search:taobao:2018",
                    "url": "https://storage.cloud.google.com/chrome-telemetry-output/chromium_1d2f58d_20230829T001142_53876/system_health.memory_desktop/load_search_taobao_2018/retry_0/trace.html"
                  }
                ]
              }
            ]
          },
          {
            "executions": [
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "builder",
                    "value": "Linux Builder Perf"
                  },
                  {
                    "key": "isolate",
                    "value": "4b8d546ab5c0d8f2a8ca3297ae4baa7877a54555de659ba322e75060933f065a/1294",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/4b8d546ab5c0d8f2a8ca3297ae4baa7877a54555de659ba322e75060933f065a/1294/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "bot",
                    "value": "lin-12-g582",
                    "url": "https://chrome-swarming.appspot.com/bot?id=lin-12-g582"
                  },
                  {
                    "key": "task",
                    "value": "645772bd91c02910",
                    "url": "https://chrome-swarming.appspot.com/task?id=645772bd91c02910"
                  },
                  {
                    "key": "isolate",
                    "value": "d7e21dd7c7aaf3cb4b7695121f1566a6b80c0e4252fa6db7e50263b49bbdd48a/189",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/d7e21dd7c7aaf3cb4b7695121f1566a6b80c0e4252fa6db7e50263b49bbdd48a/189/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "trace",
                    "value": "load:search:taobao:2018",
                    "url": "https://storage.cloud.google.com/chrome-telemetry-output/chromium_1d2f58d_20230829T001144_15931/system_health.memory_desktop/load_search_taobao_2018/retry_0/trace.html"
                  }
                ]
              }
            ]
          },
          {
            "executions": [
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "builder",
                    "value": "Linux Builder Perf"
                  },
                  {
                    "key": "isolate",
                    "value": "4b8d546ab5c0d8f2a8ca3297ae4baa7877a54555de659ba322e75060933f065a/1294",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/4b8d546ab5c0d8f2a8ca3297ae4baa7877a54555de659ba322e75060933f065a/1294/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "bot",
                    "value": "lin-19-g582",
                    "url": "https://chrome-swarming.appspot.com/bot?id=lin-19-g582"
                  },
                  {
                    "key": "task",
                    "value": "645772bebe02e510",
                    "url": "https://chrome-swarming.appspot.com/task?id=645772bebe02e510"
                  },
                  {
                    "key": "isolate",
                    "value": "e6cb022f74c921145b0fc6cdd7ccd8126c3cd783a6c73a98556fa1c5a40ef22d/189",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/e6cb022f74c921145b0fc6cdd7ccd8126c3cd783a6c73a98556fa1c5a40ef22d/189/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "trace",
                    "value": "load:search:taobao:2018",
                    "url": "https://storage.cloud.google.com/chrome-telemetry-output/chromium_1d2f58d_20230829T001144_59535/system_health.memory_desktop/load_search_taobao_2018/retry_0/trace.html"
                  }
                ]
              }
            ]
          },
          {
            "executions": [
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "builder",
                    "value": "Linux Builder Perf"
                  },
                  {
                    "key": "isolate",
                    "value": "4b8d546ab5c0d8f2a8ca3297ae4baa7877a54555de659ba322e75060933f065a/1294",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/4b8d546ab5c0d8f2a8ca3297ae4baa7877a54555de659ba322e75060933f065a/1294/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "bot",
                    "value": "lin-2-g582",
                    "url": "https://chrome-swarming.appspot.com/bot?id=lin-2-g582"
                  },
                  {
                    "key": "task",
                    "value": "645772bfe8292f10",
                    "url": "https://chrome-swarming.appspot.com/task?id=645772bfe8292f10"
                  },
                  {
                    "key": "isolate",
                    "value": "14fbe69c57a3b2a6071cb47ac7fff4b8a130de345c939e2ac03cbb8caff78cb0/189",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/14fbe69c57a3b2a6071cb47ac7fff4b8a130de345c939e2ac03cbb8caff78cb0/189/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "trace",
                    "value": "load:search:taobao:2018",
                    "url": "https://storage.cloud.google.com/chrome-telemetry-output/chromium_1d2f58d_20230829T001145_17525/system_health.memory_desktop/load_search_taobao_2018/retry_0/trace.html"
                  }
                ]
              }
            ]
          },
          {
            "executions": [
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "builder",
                    "value": "Linux Builder Perf"
                  },
                  {
                    "key": "isolate",
                    "value": "4b8d546ab5c0d8f2a8ca3297ae4baa7877a54555de659ba322e75060933f065a/1294",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/4b8d546ab5c0d8f2a8ca3297ae4baa7877a54555de659ba322e75060933f065a/1294/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "bot",
                    "value": "lin-13-g582",
                    "url": "https://chrome-swarming.appspot.com/bot?id=lin-13-g582"
                  },
                  {
                    "key": "task",
                    "value": "645772c1497b0610",
                    "url": "https://chrome-swarming.appspot.com/task?id=645772c1497b0610"
                  },
                  {
                    "key": "isolate",
                    "value": "be58897876aa2369770a6e8218a10b28a833989b4cdc2e65912c53edc91f3919/189",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/be58897876aa2369770a6e8218a10b28a833989b4cdc2e65912c53edc91f3919/189/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "trace",
                    "value": "load:search:taobao:2018",
                    "url": "https://storage.cloud.google.com/chrome-telemetry-output/chromium_1d2f58d_20230829T001146_36180/system_health.memory_desktop/load_search_taobao_2018/retry_0/trace.html"
                  }
                ]
              }
            ]
          },
          {
            "executions": [
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "builder",
                    "value": "Linux Builder Perf"
                  },
                  {
                    "key": "isolate",
                    "value": "4b8d546ab5c0d8f2a8ca3297ae4baa7877a54555de659ba322e75060933f065a/1294",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/4b8d546ab5c0d8f2a8ca3297ae4baa7877a54555de659ba322e75060933f065a/1294/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "bot",
                    "value": "lin-16-g582",
                    "url": "https://chrome-swarming.appspot.com/bot?id=lin-16-g582"
                  },
                  {
                    "key": "task",
                    "value": "645772c2470a7f10",
                    "url": "https://chrome-swarming.appspot.com/task?id=645772c2470a7f10"
                  },
                  {
                    "key": "isolate",
                    "value": "3a88b3033449625b466c82deb214d5d6223044f253b43c7b9ecf6bc529f1173b/189",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/3a88b3033449625b466c82deb214d5d6223044f253b43c7b9ecf6bc529f1173b/189/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "trace",
                    "value": "load:search:taobao:2018",
                    "url": "https://storage.cloud.google.com/chrome-telemetry-output/chromium_1d2f58d_20230829T001149_73394/system_health.memory_desktop/load_search_taobao_2018/retry_0/trace.html"
                  }
                ]
              }
            ]
          },
          {
            "executions": [
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "builder",
                    "value": "Linux Builder Perf"
                  },
                  {
                    "key": "isolate",
                    "value": "4b8d546ab5c0d8f2a8ca3297ae4baa7877a54555de659ba322e75060933f065a/1294",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/4b8d546ab5c0d8f2a8ca3297ae4baa7877a54555de659ba322e75060933f065a/1294/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "bot",
                    "value": "lin-14-g582",
                    "url": "https://chrome-swarming.appspot.com/bot?id=lin-14-g582"
                  },
                  {
                    "key": "task",
                    "value": "645772c344206610",
                    "url": "https://chrome-swarming.appspot.com/task?id=645772c344206610"
                  },
                  {
                    "key": "isolate",
                    "value": "27d0f133a14ef178f9593e3c56c69c68b26059ed748b0011f4bf4dff19c0ff00/189",
                    "url": "https://cas-viewer.appspot.com/projects/chrome-swarming/instances/default_instance/blobs/27d0f133a14ef178f9593e3c56c69c68b26059ed748b0011f4bf4dff19c0ff00/189/tree"
                  }
                ]
              },
              {
                "completed": True,
                "exception": None,
                "details": [
                  {
                    "key": "trace",
                    "value": "load:search:taobao:2018",
                    "url": "https://storage.cloud.google.com/chrome-telemetry-output/chromium_1d2f58d_20230829T001150_42466/system_health.memory_desktop/load_search_taobao_2018/retry_0/trace.html"
                  }
                ]
              }
            ]
          }
        ],
        "comparisons": {
          "prev": "different"
        },
        "result_values": [
          3898208,
          3898216,
          3898240,
          3897464,
          3897608,
          3898448,
          3898376,
          3898360,
          3898408,
          3897800
        ]
      }
    ]
  }