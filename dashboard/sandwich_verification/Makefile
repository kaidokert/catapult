# NOTE: For this makefile to work, you *must* have the following cloned into ../../.. :
# - https://github.com/googleapis/googleapis
# - https://skia.googlesource.com/buildbot.git

generate_pb_grpc:
	python3 -m grpc_tools.protoc \
	-I ../../../skia/buildbot \
	-I ../../../skia/buildbot/cabe/proto/v1 \
	-I ../../../googleapis \
	--python_out=./cabe_grpc \
	--grpc_python_out=./cabe_grpc \
	service.proto

generate_spec_pb:
	python3 -m grpc_tools.protoc \
	-I ../../../skia/buildbot/cabe/proto/v1 \
	--python_out=./cabe_grpc \
	spec.proto

generate_analysis_pb:
	python3 -m grpc_tools.protoc \
	-I ../../../skia/buildbot \
	-I ../../../skia/buildbot/cabe/proto/v1 \
	--python_out=./cabe_grpc \
	analysis.proto

generate_pb: generate_spec_pb generate_analysis_pb

# The `sed` fixup is necessary because python and/or protoc is garbage:
# https://github.com/protocolbuffers/protobuf/issues/1491
generate: generate_pb generate_pb_grpc
	sed -i 's/from cabe.proto.v1 //g' cabe_grpc/*.py

deploy_staging:
	gcloud builds submit \
	--region=us-central1 \
	--config=cloudbuild.yaml \
	--substitutions=_VERSION=$(USER) \
	--project=chromeperf .
