# sheriff config proto python bindings

To update the sheriff config python bindings for python, run this from your catapult checkout root directory:
```
docker run -v $(pwd):/catapult  gcr.io/chromeperf/protoc -I /catapult/dashboard --python_out /catapult/dashboard /catapult/dashboard/dashboard/protobuf/sheriff.proto /catapult/dashboard/dashboard/protobuf/sheriff_config.proto
```