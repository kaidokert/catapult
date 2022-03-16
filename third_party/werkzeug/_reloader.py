import fnmatch
import os
import subprocess
import sys
import threading
import time
import typing as t
from itertools import chain
from pathlib import PurePath

from ._internal import _log

# The various system prefixes where imports are found. Base values are
# different when running in a virtualenv. The stat reloader won't scan
# these directories, it would be too inefficient.
prefix = {sys.prefix, sys.base_prefix, sys.exec_prefix, sys.base_exec_prefix}

if hasattr(sys, "real_prefix"):
    # virtualenv < 20
    prefix.add(sys.real_prefix)  # type: ignore

_ignore_prefixes = tuple(prefix)
del prefix


def _iter_module_paths() -> t.Iterator[str]:
    """Find the filesystem paths associated with imported modules."""
    # List is in case the value is modified by the app while updating.
    for module in list(sys.modules.values()):
        name = getattr(module, "__file__", None)

        if name is None:
            continue

        while not os.path.isfile(name):
            # Zip file, find the base file without the module path.
            old = name
            name = os.path.dirname(name)

            if name == old:  # skip if it was all directories somehow
                break
        else:
            yield name


def _remove_by_pattern(paths: t.Set[str], exclude_patterns: t.Set[str]) -> None:
    for pattern in exclude_patterns:
        paths.difference_update(fnmatch.filter(paths, pattern))


def _find_stat_paths(
    extra_files: t.Set[str], exclude_patterns: t.Set[str]
) -> t.Iterable[str]:
    """Find paths for the stat reloader to watch. Returns imported
    module files, Python files under non-system paths. Extra files and
    Python files under extra directories can also be scanned.

    System paths have to be excluded for efficiency. Non-system paths,
    such as a project root or ``sys.path.insert``, should be the paths
    of interest to the user anyway.
    """
    paths = set()

    for path in chain(list(sys.path), extra_files):
        path = os.path.abspath(path)

        if os.path.isfile(path):
            # zip file on sys.path, or extra file
            paths.add(path)

        for root, dirs, files in os.walk(path):
            # Ignore system prefixes for efficience. Don't scan
            # __pycache__, it will have a py or pyc module at the import
            # path. As an optimization, ignore .git and .hg since
            # nothing interesting will be there.
            if root.startswith(_ignore_prefixes) or os.path.basename(root) in {
                "__pycache__",
                ".git",
                ".hg",
            }:
                dirs.clear()
                continue

            for name in files:
                if name.endswith((".py", ".pyc")):
                    paths.add(os.path.join(root, name))

    paths.update(_iter_module_paths())
    _remove_by_pattern(paths, exclude_patterns)
    return paths


def _find_watchdog_paths(
    extra_files: t.Set[str], exclude_patterns: t.Set[str]
) -> t.Iterable[str]:
    """Find paths for the stat reloader to watch. Looks at the same
    sources as the stat reloader, but watches everything under
    directories instead of individual files.
    """
    dirs = set()

    for name in chain(list(sys.path), extra_files):
        name = os.path.abspath(name)

        if os.path.isfile(name):
            name = os.path.dirname(name)

        dirs.add(name)

    for name in _iter_module_paths():
        dirs.add(os.path.dirname(name))

    _remove_by_pattern(dirs, exclude_patterns)
    return _find_common_roots(dirs)


def _find_common_roots(paths: t.Iterable[str]) -> t.Iterable[str]:
    root: t.Dict[str, dict] = {}

    for chunks in sorted((PurePath(x).parts for x in paths), key=len, reverse=True):
        node = root

        for chunk in chunks:
            node = node.setdefault(chunk, {})

        node.clear()

    rv = set()

    def _walk(node: t.Mapping[str, dict], path: t.Tuple[str, ...]) -> None:
        for prefix, child in node.items():
            _walk(child, path + (prefix,))

        if not node:
            rv.add(os.path.join(*path))

    _walk(root, ())
    return rv


def _get_args_for_reloading() -> t.List[str]:
    """Determine how the script was executed, and return the args needed
    to execute it again in a new process.
    """
    rv = [sys.executable]
    py_script = sys.argv[0]
    args = sys.argv[1:]
    # Need to look at main module to determine how it was executed.
    __main__ = sys.modules["__main__"]

    # The value of __package__ indicates how Python was called. It may
    # not exist if a setuptools script is installed as an egg. It may be
    # set incorrectly for entry points created with pip on Windows.
    if getattr(__main__, "__package__", None) is None or (
        os.name == "nt"
        and __main__.__package__ == ""
        and not os.path.exists(py_script)
        and os.path.exists(f"{py_script}.exe")
    ):
        # Executed a file, like "python app.py".
        py_script = os.path.abspath(py_script)

        if os.name == "nt":
            # Windows entry points have ".exe" extension and should be
            # called directly.
            if not os.path.exists(py_script) and os.path.exists(f"{py_script}.exe"):
                py_script += ".exe"

            if (
                os.path.splitext(sys.executable)[1] == ".exe"
                and os.path.splitext(py_script)[1] == ".exe"
            ):
                rv.pop(0)

        rv.append(py_script)
    else:
        # Executed a module, like "python -m werkzeug.serving".
        if sys.argv[0] == "-m":
            # Flask works around previous behavior by putting
            # "-m flask" in sys.argv.
            # TODO remove this once Flask no longer misbehaves
            args = sys.argv
        else:
            if os.path.isfile(py_script):
                # Rewritten by Python from "-m script" to "/path/to/script.py".
                py_module = t.cast(str, __main__.__package__)
                name = os.path.splitext(os.path.basename(py_script))[0]

                if name != "__main__":
                    py_module += f".{name}"
            else:
                # Incorrectly rewritten by pydevd debugger from "-m script" to "script".
                py_module = py_script

            rv.extend(("-m", py_module.lstrip(".")))

    rv.extend(args)
    return rv


class ReloaderLoop:
    name = ""

    def __init__(
        self,
        extra_files: t.Optional[t.Iterable[str]] = None,
        exclude_patterns: t.Optional[t.Iterable[str]] = None,
        interval: t.Union[int, float] = 1,
    ) -> None:
        self.extra_files: t.Set[str] = {os.path.abspath(x) for x in extra_files or ()}
        self.exclude_patterns: t.Set[str] = set(exclude_patterns or ())
        self.interval = interval

    def __enter__(self) -> "ReloaderLoop":
        """Do any setup, then run one step of the watch to populate the
        initial filesystem state.
        """
        self.run_step()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # type: ignore
        """Clean up any resources associated with the reloader."""
        pass

    def run(self) -> None:
        """Continually run the watch step, sleeping for the configured
        interval after each step.
        """
        while True:
            self.run_step()
            time.sleep(self.interval)

    def run_step(self) -> None:
        """Run one step for watching the filesystem. Called once to set
        up initial state, then repeatedly to update it.
        """
        pass

    def restart_with_reloader(self) -> int:
        """Spawn a new Python interpreter with the same arguments as the
        current one, but running the reloader thread.
        """
        while True:
            _log("info", f" * Restarting with {self.name}")
            args = _get_args_for_reloading()
            new_environ = os.environ.copy()
            new_environ["WERKZEUG_RUN_MAIN"] = "true"
            exit_code = subprocess.call(args, env=new_environ, close_fds=False)

            if exit_code != 3:
                return exit_code

    def trigger_reload(self, filename: str) -> None:
        self.log_reload(filename)
        sys.exit(3)

    def log_reload(self, filename: str) -> None:
        filename = os.path.abspath(filename)
        _log("info", f" * Detected change in {filename!r}, reloading")


class StatReloaderLoop(ReloaderLoop):
    name = "stat"

    def __enter__(self) -> ReloaderLoop:
        self.mtimes: t.Dict[str, float] = {}
        return super().__enter__()

    def run_step(self) -> None:
        for name in chain(_find_stat_paths(self.extra_files, self.exclude_patterns)):
            try:
                mtime = os.stat(name).st_mtime
            except OSError:
                continue

            old_time = self.mtimes.get(name)

            if old_time is None:
                self.mtimes[name] = mtime
                continue

            if mtime > old_time:
                self.trigger_reload(name)


class WatchdogReloaderLoop(ReloaderLoop):
    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        from watchdog.observers import Observer
        from watchdog.events import PatternMatchingEventHandler

        super().__init__(*args, **kwargs)
        trigger_reload = self.trigger_reload

        class EventHandler(PatternMatchingEventHandler):  # type: ignore
            def on_any_event(self, event):  # type: ignore
                trigger_reload(event.src_path)

        reloader_name = Observer.__name__.lower()

        if reloader_name.endswith("observer"):
            reloader_name = reloader_name[:-8]

        self.name = f"watchdog ({reloader_name})"
        self.observer = Observer()
        # Extra patterns can be non-Python files, match them in addition
        # to all Python files in default and extra directories. Ignore
        # __pycache__ since a change there will always have a change to
        # the source file (or initial pyc file) as well. Ignore Git and
        # Mercurial internal changes.
        extra_patterns = [p for p in self.extra_files if not os.path.isdir(p)]
        self.event_handler = EventHandler(
            patterns=["*.py", "*.pyc", "*.zip", *extra_patterns],
            ignore_patterns=[
                "*/__pycache__/*",
                "*/.git/*",
                "*/.hg/*",
                *self.exclude_patterns,
            ],
        )
        self.should_reload = False

    def trigger_reload(self, filename: str) -> None:
        # This is called inside an event handler, which means throwing
        # SystemExit has no effect.
        # https://github.com/gorakhargosh/watchdog/issues/294
        self.should_reload = True
        self.log_reload(filename)

    def __enter__(self) -> ReloaderLoop:
        self.watches: t.Dict[str, t.Any] = {}
        self.observer.start()
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):  # type: ignore
        self.observer.stop()
        self.observer.join()

    def run(self) -> None:
        while not self.should_reload:
            self.run_step()
            time.sleep(self.interval)

        sys.exit(3)

    def run_step(self) -> None:
        to_delete = set(self.watches)

        for path in _find_watchdog_paths(self.extra_files, self.exclude_patterns):
            if path not in self.watches:
                try:
                    self.watches[path] = self.observer.schedule(
                        self.event_handler, path, recursive=True
                    )
                except OSError:
                    # Clear this path from list of watches We don't want
                    # the same error message showing again in the next
                    # iteration.
                    self.watches[path] = None

            to_delete.discard(path)

        for path in to_delete:
            watch = self.watches.pop(path, None)

            if watch is not None:
                self.observer.unschedule(watch)


reloader_loops: t.Dict[str, t.Type[ReloaderLoop]] = {
    "stat": StatReloaderLoop,
    "watchdog": WatchdogReloaderLoop,
}

try:
    __import__("watchdog.observers")
except ImportError:
    reloader_loops["auto"] = reloader_loops["stat"]
else:
    reloader_loops["auto"] = reloader_loops["watchdog"]


def ensure_echo_on() -> None:
    """Ensure that echo mode is enabled. Some tools such as PDB disable
    it which causes usability issues after a reload."""
    # tcgetattr will fail if stdin isn't a tty
    if sys.stdin is None or not sys.stdin.isatty():
        return

    try:
        import termios
    except ImportError:
        return

    attributes = termios.tcgetattr(sys.stdin)

    if not attributes[3] & termios.ECHO:
        attributes[3] |= termios.ECHO
        termios.tcsetattr(sys.stdin, termios.TCSANOW, attributes)


def run_with_reloader(
    main_func: t.Callable[[], None],
    extra_files: t.Optional[t.Iterable[str]] = None,
    exclude_patterns: t.Optional[t.Iterable[str]] = None,
    interval: t.Union[int, float] = 1,
    reloader_type: str = "auto",
) -> None:
    """Run the given function in an independent Python interpreter."""
    import signal

    signal.signal(signal.SIGTERM, lambda *args: sys.exit(0))
    reloader = reloader_loops[reloader_type](
        extra_files=extra_files, exclude_patterns=exclude_patterns, interval=interval
    )

    try:
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            ensure_echo_on()
            t = threading.Thread(target=main_func, args=())
            t.daemon = True

            # Enter the reloader to set up initial state, then start
            # the app thread and reloader update loop.
            with reloader:
                t.start()
                reloader.run()
        else:
            sys.exit(reloader.restart_with_reloader())
    except KeyboardInterrupt:
        pass
