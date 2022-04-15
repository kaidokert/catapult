FROM google/cloud-sdk:326.0.0

ARG PROTOBUF_VERSION=3.6.1.3-2

# The latest version is in sid repo. So need to specify the
# version of dependency to avoid version conflix if you want
# to use "stable" one.

ENV PYTHONPATH=/usr/lib/google-cloud-sdk/platform/google_appengine
ENV PATH=/usr/bin/protoc:/usr/local/google/home/heiserya/depot_tools:${PATH}

COPY docker-entrypoint.sh /usr/local/bin/

ENTRYPOINT ["docker-entrypoint.sh"]