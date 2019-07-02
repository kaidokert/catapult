"""Collect collects and prints chrome process and thread types from a CrOS device."""

import contextlib
import json
import re
import threading
import time
import urllib


class CollectProcessTypes(object):

  def __init__(self):
    self.process_thread_types_dict = {}
    self.line_regex = re.compile(
        r"""
        \s*(\d+)    # PID
        \s+(\d+)    # TID
        \s+(\S+)    # CMD
        \s+(.+)\n?  # COMMAND LINE
        """, re.VERBOSE)

    self.type_flag_regex = re.compile(r".*--type=(\S*)")

    self.chrome_exe_path_matcher = re.compile(r"/opt/google/chrome/chrome\s*")

  def get_process_type(self, name):
    if name is None:
      return "BROWSER PROCESS"
    elif name == "renderer":
      return "RENDERER PROCESS"
    elif name == "gpu-process":
      return "GPU PROCESS"
    elif name == "utility":
      return "UTILITY PROCESS"
    elif name == "zygote":
      return "ZYGOTE PROCESS"
    elif name == "ppapi":
      return "PPAPI PULGIN PROCESS"
    elif name == "ppapi-broker":
      return "PPAPI BROKER PROCESS"
    else:
      return "OTHER PROCESS"

  def get_thread_type(self, name):
    if name == "Chrome_IOThread" or name == "Chrome_ChildIOThread" [:15]:
      return "IO THREAD"
    elif name == "VizCompositorThread" [:15] or name == "Compositor":
      return "COMPOSITOR THREAD"
    elif name [:13] == "TaskScheduler":
      return "SCHEDULER WORKER THREAD"
    elif name == "CompositorTileW":
      return "COMPOSITOR TILE WORKER THREAD"
    else:
      return "OTHER THREAD"

  def parse(self, lines, seen):
    for l in lines.splitlines():
      m = self.line_regex.match(l)
      if m is None:
        continue

      pid, tid, cmd, cmd_line = m.groups()
      s = (pid, tid)

      if s in seen:
        continue

      seen[s] = True

      if self.chrome_exe_path_matcher.match(cmd_line) is None:
        continue
      type_flag = self.type_flag_regex.search(cmd_line)
      if type_flag is None:
        continue
      process_type = self.get_process_type(type_flag.groups()[0])

      if pid == tid:
        thread_type = "MAIN THREAD"
      else:
        thread_type = self.get_thread_type(cmd)

      if process_type not in self.process_thread_types_dict:
        self.process_thread_types_dict[process_type] = {}

      if thread_type == "OTHER THREAD":
        if thread_type not in self.process_thread_types_dict[process_type]:
          self.process_thread_types_dict[process_type][thread_type] = {}
        if cmd in self.process_thread_types_dict[process_type][thread_type]:
          self.process_thread_types_dict[process_type][thread_type][cmd] += 1
        else:
          self.process_thread_types_dict[process_type][thread_type][cmd] = 1
        continue

      if thread_type in self.process_thread_types_dict[process_type]:
        self.process_thread_types_dict[process_type][thread_type] += 1
      else:
        self.process_thread_types_dict[process_type][thread_type] = 1

  def collect(self, event, platform_backend):
    seen = {}
    while not event.is_set():
      output = platform_backend.RunCommand(["ps", "-ewwLo", "pid,lwp,comm,cmd"])
      self.parse(output, seen)
      # Wait for 500 milliseconds.
      time.sleep(.500)

  @contextlib.contextmanager
  def Start(self, action_runner):
    event = threading.Event()
    platform_backend = action_runner.tab.browser._platform_backend
    t = threading.Thread(name="CollectThread",
                         target=self.collect,
                         args=(event, platform_backend,))
    t.start()
    try:
      yield
    finally:
      event.set()

  def GetResults(self, results):
    if results.current_page_run.ok:
      file_safe_name = (
          urllib.quote(results.telemetry_info.benchmark_name, safe="")
          + "@@" + urllib.quote(results.current_page.name, safe="") + "@@")
      with results.CaptureArtifact(
          "types-%s.json" % (file_safe_name)) as dest_file:
        with open(dest_file, 'w') as outfile:
          json.dump(self.process_thread_types_dict, outfile)
