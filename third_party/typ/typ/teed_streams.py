# Copyright 2022 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import io
import os
import sys
import threading

def get_teed_stream(stream, host):
    # TODO: add other implementations
    return _PipeTeedStream(stream)
    #return _StringIoTeedStream(stream)


class _PipeThread(threading.Thread):
    """Thread to tee a stream using a pipe."""
    def __init__(self, read_pipe, original_stream, teed_stream, *args, **kwargs):
        super(_PipeThread, self).__init__(*args, **kwargs)
        self._read_pipe = read_pipe
        self._original_stream = original_stream
        self._teed_stream = teed_stream
        self._lock = threading.Lock()
        self._capturing = False
        self._diverting = False
        self._terminate_thread = True

    def run(self):
        while True:
            msg = self._read_pipe.read()
            sys.__stderr__.write('\n\nASDF got message, waiting for lock\n\n')
            with self._lock:
                sys.__stderr__.write('\n\nASDF thread got %s\n\n' % msg)
                if self._capturing:
                    if (sys.vesrion_info.major == 2 and
                            isinstance(msg, str)):  # pragma: python2
                        msg = unicode(msg)
                    self._teed_stream.write(msg)
                if not self._diverting:
                    self._original_stream.write(msg)
                if self._terminate_thread:
                    self._read_pipe.close()
                    return

    def terminate(self):
        with self._lock:
            self._terminate_thread = True

    def flush(self):
        with self._lock:
            if self._capturing:
                self._teed_stream.flush()
            if not self._diverting:
                self._original_stream.flush()

    def capture(self, divert):
        with self._lock:
            self._teed_stream.truncate(0)
            self._capturing = True
            self._diverting = divert

    def restore(self):
        with self._lock:
            msg = self._teed_stream.getvalue()
            sys.__stderr__.write('\n\nASDF teed string is %s\n\n' % msg)
            self._teed_stream.truncate(0)
            self._capturing = False
            self._diverting = False
            return msg


class _PipeTeedStream(object):
    """Pipe-based teed stream implementation.

    Does not support additional arguments when writing.
    """

    def __init__(self, stream):
        self._original_stream = stream
        self._read_fd, self._write_fd = os.pipe()
        self._read_pipe = os.fdopen(self._read_fd, 'r')
        self._write_pipe = os.fdopen(self._write_fd, 'w')
        self._string_io = io.StringIO()
        self._thread = _PipeThread(self._read_pipe, stream, self._string_io)
        self._thread.daemon = True
        self._thread.start()

    def __del__(self):
        self._thread.terminate()
        self._write_pipe.close()

    def fileno(self):
        return self._write_fd

    @property
    def stream(self):
        return self._original_stream

    def write(self, msg):
        sys.__stderr__.write('Writing message "%s"\n' % msg)
        self._write_pipe.write(msg)
        self._write_pipe.flush()

    def flush(self):
        self._thread.flush()

    def capture(self, divert=True):
        self._thread.capture(divert)

    def restore(self):
        self.flush()
        return self._thread.restore()


class _StringIoTeedStream(io.StringIO):
    """Legacy teed stream implementation based on StringIO.

    Simple, but does not work properly when used as a handle for subprocess'
    output.
    """

    def __init__(self, stream):
        super(_TeedStream, self).__init__()
        self.stream = stream
        self.capturing = False
        self.diverting = False

    def write(self, msg, *args, **kwargs):
        if self.capturing:
            if (sys.version_info.major == 2 and
                    isinstance(msg, str)):  # pragma: python2
                msg = unicode(msg)
            super(_TeedStream, self).write(msg, *args, **kwargs)
        if not self.diverting:
            self.stream.write(msg, *args, **kwargs)

    def flush(self):
        if self.capturing:
            super(_TeedStream, self).flush()
        if not self.diverting:
            self.stream.flush()

    def capture(self, divert=True):
        self.truncate(0)
        self.capturing = True
        self.diverting = divert

    def restore(self):
        msg = self.getvalue()
        self.truncate(0)
        self.capturing = False
        self.diverting = False
        return msg


TEED_STREAM_TYPES = (_StringIoTeedStream, _PipeTeedStream)
