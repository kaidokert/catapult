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
import random
import traceback
import sys
import tempfile
import threading

# Tells the thread to flush its streams.
_FLUSH_PIPE_MESSAGE = '_$!FLUSH_PIPE!$_'
# Tells the thread to pause execution and wait for a signal to continue, e.g.
# to ensure that all previously written data is forwarded to the streams before
# starting/stopping capturing.
_DRAIN_PIPE_MESSAGE = '_$!DRAIN_PIPE!$_'


# def get_teed_stream(stream, host):
#     return _PipeTeedStream(stream)


class _PipeThread(threading.Thread):
    """Thread to tee a stream using a pipe."""
    def __init__(self, read_pipe, original_stream, teed_stream, always_flush, *args, **kwargs):
        super(_PipeThread, self).__init__(*args, **kwargs)
        self._read_pipe = read_pipe
        self._original_stream = original_stream
        self._teed_stream = teed_stream
        self._always_flush = always_flush
        self._lock = threading.Lock()
        self._capturing = False
        self._diverting = False
        self._terminate_thread = False
        self._id = None

        self.drain_message_received_event = threading.Event()
        self.continue_running_event = threading.Event()

    def shutdown(self):
        with self._lock:
            self._terminate_thread = True

    def run(self):
        handle_drain_after_forwarding = False
        flush_streams = self._always_flush
        buffer_string = ''
        while True:
            msg = self._read_pipe.read(1)
            buffer_string += msg

            if buffer_string == _DRAIN_PIPE_MESSAGE:
                buffer_string = ''
                self._handle_drain_message()
                continue

            if buffer_string == _FLUSH_PIPE_MESSAGE:
                buffer_string = ''
                with self._lock:
                    if self._capturing:
                        self._teed_stream.flush()
                    if not self._diverting:
                        self._original_stream.flush()
                continue

            if (_DRAIN_PIPE_MESSAGE.startswith(buffer_string) or
                _FLUSH_PIPE_MESSAGE.startswith(buffer_string)):
                continue

            if msg in ('\r', '\n'):
                flush_streams = True

            with self._lock:
                if self._terminate_thread:
                    return
                # if not self._original_stream.isatty() and self._always_flush:
                #     sys.__stderr__.write('ASDF should be writing character to inner stderr "%s" capturing:%s %d\n' % (buffer_string, self._capturing, self._id))
                if self._capturing:
                    if (sys.version_info.major == 2 and
                            isinstance(msg, str)):  # pragma: python2
                        msg = unicode(msg)
                    self._teed_stream.write(buffer_string)
                    if flush_streams:
                        self._teed_stream.flush()
                if not self._diverting:
                    self._original_stream.write(buffer_string)
                    if flush_streams:
                        self._original_stream.flush()
            buffer_string = ''
            flush_streams = self._always_flush

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

    def get_current_captured_output(self):
        with self._lock:
            return self._teed_stream.getvalue()


class PipeTeedStream(object):
    """Pipe-based teed stream implementation.

    Does not support additional arguments when writing.
    """

    def __init__(self, stream, always_flush=False):
        self._id = random.randint(0, 1000)
        # sys.__stderr__.write('ASDF creating stream with ID %d\n' % self._id)
        self._original_stream = stream
        self._capture_count = 0
        self._read_fd, self._write_fd = os.pipe()
        if sys.version_info.major == 3:
            os.set_inheritable(self._write_fd, True)
        # We specify newline='\n' to preserve carriage returns, e.g. for
        # overwriting intermediate messages.
        self._read_wrapper = io.TextIOWrapper(
                os.fdopen(self._read_fd, 'rb'), encoding='utf-8', newline='\n')
        self._write_wrapper = io.TextIOWrapper(
                os.fdopen(self._write_fd, 'wb'), write_through=True,
                line_buffering=True, encoding='utf-8', newline='\n')
        self._string_io = io.StringIO()
        self._thread = _PipeThread(
                self._read_wrapper, self._original_stream, self._string_io,
                always_flush)
        self._thread._id = self._id
        self._thread.daemon = True
        self._thread.start()

    def __del__(self):
        self.close()

    def _reset_drain_events(self):
        self._thread.drain_message_received_event.clear()
        self._thread.continue_running_event.clear()

    def _drain_and_wait(self):
        self._write_wrapper.write(_DRAIN_PIPE_MESSAGE)
        self._write_wrapper.flush()
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
        if self._write_wrapper:
            with self._drain_pipe_context():
                self._thread.shutdown()
                self._write_wrapper.close()
            self._write_wrapper = None

    def fileno(self):
        return self._write_fd

    def isatty(self):
        return self._original_stream.isatty()

    @property
    def stream(self):
        return self._original_stream

    def write(self, msg):
        self._write_wrapper.write(msg)

    def flush(self):
        if self._write_wrapper:
            self._write_wrapper.write(_FLUSH_PIPE_MESSAGE)
            self._write_wrapper.flush()

    def capture(self, divert=True):
        # sys.__stderr__.write('ASDF capturing %d\n' % self._id)
        #traceback.print_stack(file=sys.__stderr__)
        if self._capture_count == 0:
            with self._drain_pipe_context():
                self._thread.capture(divert)
        self._capture_count += 1

    def restore(self):
        # sys.__stderr__.write('ASDF restoring %d\n' % self._id)
        #traceback.print_stack(file=sys.__stderr__)
        self._capture_count -= 1
        if self._capture_count == 0:
            with self._drain_pipe_context():
                retval = self._thread.restore()
            return retval
        return ''


# class _StringIoTeedStream(io.StringIO):
#     """Legacy teed stream implementation based on StringIO.

#     Simple, but does not work properly when used as a handle for subprocess'
#     output.
#     """

#     def __init__(self, stream):
#         super(_StringIoTeedStream, self).__init__()
#         self.stream = stream
#         self.capturing = False
#         self.diverting = False

#     def write(self, msg, *args, **kwargs):
#         if self.capturing:
#             if (sys.version_info.major == 2 and
#                     isinstance(msg, str)):  # pragma: python2
#                 msg = unicode(msg)
#             super(_TeedStream, self).write(msg, *args, **kwargs)
#         if not self.diverting:
#             self.stream.write(msg, *args, **kwargs)

#     def flush(self):
#         if self.capturing:
#             super(_StringIoTeedStream, self).flush()
#         if not self.diverting:
#             self.stream.flush()

#     def capture(self, divert=True):
#         self.truncate(0)
#         self.capturing = True
#         self.diverting = divert

#     def restore(self):
#         msg = self.getvalue()
#         self.truncate(0)
#         self.capturing = False
#         self.diverting = False
#         return msg


#TEED_STREAM_TYPES = (_StringIoTeedStream, _PipeTeedStream)
