import os
import tomllib
from pathlib import Path

import gdb


def _split_path(value):
    return [item for item in str(value or "").split(os.pathsep) if item]


def _add_unique(paths, path):
    text = str(path)
    if text not in paths:
        paths.append(text)


def _config_path():
    if value := os.environ.get("PWNKIT_CONFIG"):
        return Path(value).expanduser()
    for directory in (Path.cwd(), *Path.cwd().parents):
        path = directory / "configs" / "pwnkit.toml"
        if path.is_file():
            return path
    return None


def _load_libs_root():
    for variable in ("PWN_GLIBC_LIBS_DIR", "PWNKIT_GLIBC_ROOT"):
        if value := os.environ.get(variable):
            return Path(value).expanduser()

    config_path = _config_path()
    if config_path is None:
        gdb.write("[pwnkit] configs/pwnkit.toml was not found\n", gdb.STDERR)
        return None
    try:
        with config_path.open("rb") as stream:
            value = tomllib.load(stream)["glibc"]["root"]
    except (KeyError, OSError, tomllib.TOMLDecodeError) as exc:
        gdb.write(f"[pwnkit] failed to read {config_path}: {exc}\n", gdb.STDERR)
        return None
    return Path(value).expanduser()


def _existing_debug_dirs(libs_root):
    debug_dirs = []
    thread_db_dirs = []
    for glibc_dir in sorted(libs_root.iterdir()):
        if not glibc_dir.is_dir():
            continue

        for candidate in (glibc_dir / ".debug" / "debug", glibc_dir / ".debug"):
            if (candidate / ".build-id").is_dir():
                _add_unique(debug_dirs, candidate)

        for candidate in (
            glibc_dir / "x86_64-linux-gnu",
            glibc_dir / "i386-linux-gnu",
            glibc_dir,
        ):
            if candidate.is_dir() and any(candidate.glob("libthread_db*.so*")):
                _add_unique(thread_db_dirs, candidate)
    return debug_dirs, thread_db_dirs


def reload_glibc_debug():
    libs_root = _load_libs_root()
    if libs_root is None or not libs_root.is_dir():
        if os.environ.get("PWN_GLIBC_DEBUG_VERBOSE") == "1":
            gdb.write("[pwnkit] glibc root is not configured\n")
        return

    debug_dirs, thread_db_dirs = _existing_debug_dirs(libs_root)
    for path in _split_path(gdb.parameter("debug-file-directory")):
        _add_unique(debug_dirs, path)

    if debug_dirs:
        gdb.execute("set debug-file-directory " + os.pathsep.join(debug_dirs), to_string=True)
    if thread_db_dirs:
        gdb.execute("set libthread-db-search-path " + os.pathsep.join(thread_db_dirs), to_string=True)

    if os.environ.get("PWN_GLIBC_DEBUG_VERBOSE") == "1":
        gdb.write(f"[pwnkit] loaded glibc debug dirs from {libs_root}\n")


class GlibcDebugReload(gdb.Command):
    def __init__(self):
        super().__init__("pwn-glibc-debug-reload", gdb.COMMAND_SUPPORT)

    def invoke(self, argument, from_tty):
        reload_glibc_debug()
        gdb.write("[pwnkit] glibc debug paths reloaded\n")


GlibcDebugReload()
reload_glibc_debug()
