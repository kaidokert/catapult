FROM google/cloud-sdk:272.0.0

ARG PROTOBUF_VERSION=3.6.1.3-2

RUN apt-get install -y \
  libprotoc17=${PROTOBUF_VERSION} \
  protobuf-compiler=${PROTOBUF_VERSION}

ENV PYTHONPATH=/usr/lib/google-cloud-sdk/platform/google_appengine 