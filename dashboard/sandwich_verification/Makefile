generate_pb_grpc:
	python3 -m grpc_tools.protoc \
	-I ../../../skia/buildbot/ \
	--proto_path=../../../googleapis \
	--python_out=./cabe_grpc \
	--grpc_python_out=./cabe_grpc \
	../../../skia/buildbot/cabe/proto/v1/service.proto

generate_pb:
	python3 -m grpc_tools.protoc \
	-I ../../../skia/buildbot/ \
	--python_out=./cabe_grpc \
	../../../skia/buildbot/cabe/proto/v1/spec.proto \
	../../../skia/buildbot/cabe/proto/v1/analysis.proto

generate: generate_pb generate_pb_grpc
