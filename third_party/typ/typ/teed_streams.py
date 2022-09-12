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

import contextlib
import io
import os
import sys
import threading


_DRAIN_PIPE_MESSAGE = '_$!DRAIN_PIPE!$_\n'


def get_teed_stream(stream, host):
    return _PipeTeedStream(stream)


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
        self._terminate_thread = False

        self.drain_message_received_event = threading.Event()
        self.continue_running_event = threading.Event()

    def shutdown(self):
        with self._lock:
            self._terminate_thread = True

    def run(self):
        handle_sync_after_forwarding = False
        handle_drain_after_forwarding = False
        for msg in self._read_pipe:
            if msg == _DRAIN_PIPE_MESSAGE:
                self._handle_drain_message()
                continue
            if msg.endswith(_DRAIN_PIPE_MESSAGE):
                # This will be hit if the message preceding the drain message
                # did not end with a newline, causing the drain message to be
                # appended to it. In this case, forward the message first before
                # signalling that the pipe is drained.
                msg = msg[:-1 * len(_DRAIN_PIPE_MESSAGE)]
                handle_drain_after_forwarding = True

            with self._lock:
                if self._terminate_thread:
                    return
                if self._capturing:
                    if (sys.version_info.major == 2 and
                            isinstance(msg, str)):  # pragma: python2
                        msg = unicode(msg)
                    self._teed_stream.write(msg)
                    self._teed_stream.flush()
                if not self._diverting:
                    self._original_stream.write(msg)
                    self._original_stream.flush()

            if handle_drain_after_forwarding:
                handle_drain_after_forwarding = False
                self._handle_drain_message()

    def _handle_drain_message(self):
        self.drain_message_received_event.set()
        self.continue_running_event.wait()

    def flush(self):
        with self._lock:
            if self._capturing:
                self._teed_stream.flush()
            if not self._diverting:
                self._original_stream.flush()

    def capture(self, divert):
        with self._lock:
            self._teed_stream.truncate(0)
            self._teed_stream.seek(0)
            self._capturing = True
            self._diverting = divert

    def restore(self):
        with self._lock:
            msg = self._teed_stream.getvalue()
            self._teed_stream.truncate(0)
            self._teed_stream.seek(0)
            self._capturing = False
            self._diverting = False
            return msg


class _PipeTeedStream(object):
    """Pipe-based teed stream implementation.

    Does not support additional arguments when writing.
    """

    def __init__(self, stream):
        self._original_stream = stream
        self._capture_count = 0
        self._read_fd, self._write_fd = os.pipe()
        if sys.version_info.major == 3:
            os.set_inheritable(self._write_fd, True)
        # These opens can specify newline=X to change how newlines work (default
        # is universal newlines), but I have been unable to find a combination
        # that works as we'd hope. '\n' for both seems to at least partially
        # preserve carriage returns, but still doesn't let overwriting work
        # properly.
        self._read_pipe = os.fdopen(self._read_fd, 'r')
        self._write_pipe = os.fdopen(self._write_fd, 'w')
        self._string_io = io.StringIO()
        self._thread = _PipeThread(
                self._read_pipe, self._original_stream, self._string_io)
        self._thread.daemon = True
        self._thread.start()

    def __del__(self):
        self.close()

    def _reset_drain_events(self):
        self._thread.drain_message_received_event.clear()
        self._thread.continue_running_event.clear()

    def _drain_and_wait(self):
        self._write_pipe.write(_DRAIN_PIPE_MESSAGE)
        self._write_pipe.flush()
        self._thread.drain_message_received_event.wait()

    def _resume_after_drain(self):
        self._thread.continue_running_event.set()

    @contextlib.contextmanager
    def _drain_pipe_context(self):
        try:
            self._reset_drain_events()
            self._drain_and_wait()
            yield
        finally:
            self._resume_after_drain()

    def close(self):
        if self._write_pipe:
            with self._drain_pipe_context():
                self._thread.shutdown()
                self._write_pipe.close()
            self._write_pipe = None

    def fileno(self):
        return self._write_fd

    def isatty(self):
        return self._original_stream.isatty()

    @property
    def stream(self):
        return self._original_stream

    def write(self, msg):
        self._write_pipe.write(msg)
        self._write_pipe.flush()

    def flush(self):
        self._write_pipe.flush()
        self._thread.flush()

    def capture(self, divert=True):
        if self._capture_count == 0:
            with self._drain_pipe_context():
                self._thread.capture(divert)
        self._capture_count += 1

    def restore(self):
        self._capture_count -= 1
        if self._capture_count == 0:
            with self._drain_pipe_context():
                retval = self._thread.restore()
            return retval


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
