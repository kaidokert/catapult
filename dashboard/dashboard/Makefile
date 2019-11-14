PROTOC=protoc

PROTOS=sheriff_pb2.py sheriff_config_pb2.py
all: $(PROTOS)

%_pb2.py: proto/%.proto
	$(PROTOC) -Iproto -I. --python_out=. $<

.PHONY: clean

clean:
	rm -f $(PROTOS)

