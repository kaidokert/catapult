#!/usr/bin/env bash
# CD to script directory
cd "${0%/*}"

rm -rf go
mkdir -p go
curl -s https://chromium.googlesource.com/infra/infra/+/refs/heads/main\?format\=JSON | tail -c +6 > VERSION_INFO
commit=$(python -c 'import json;print(json.load(open("VERSION_INFO"))["commit"])')
echo Updating to $commit.
curl https://chromium.googlesource.com/infra/infra/+archive/$commit/python_pb2/go.tar.gz | tar x -C go
