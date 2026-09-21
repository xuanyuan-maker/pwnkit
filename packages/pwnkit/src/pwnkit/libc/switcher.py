import logging
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path

from pwnkit.elf.metadata import ElfMetadata, inspect_elf


LIBC = "libc.so.6"
logger = logging.getLogger("pwnkit")


@dataclass(frozen=True)
class GlibcCandidate:
    directory: Path
    version: str
    libc: Path | None
    loader: Path | None


@dataclass(frozen=True)
class DependencyScan:
    metadata: ElfMetadata
    local: dict[str, Path]
    missing: tuple[str, ...]


def loader_name(bits: int) -> str:
    return "ld-linux-x86-64.so.2" if bits == 64 else "ld-linux.so.2"


def _local_library(directory: Path, name: str) -> Path | None:
    path = directory / name
    return path if path.is_file() else None


def scan_dependencies(path: Path) -> DependencyScan:
    metadata = inspect_elf(path)
    root = path.parent
    queue = [path]
    visited: set[Path] = set()
    local: dict[str, Path] = {}
    missing: set[str] = set()

    while queue:
        current = queue.pop()
        current = current.resolve()
        if current in visited:
            continue
        visited.add(current)
        current_info = inspect_elf(current)
        names = list(current_info.needed)
        if current_info.interpreter:
            names.append(Path(current_info.interpreter).name)
        for name in names:
            name = Path(name).name
            dependency = _local_library(root, name)
            if dependency is None:
                missing.add(name)
                continue
            local[name] = dependency
            queue.append(dependency)

    return DependencyScan(metadata=metadata, local=local, missing=tuple(sorted(missing)))


def _version_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def _find_file(directory: Path, name: str) -> Path | None:
    for path in directory.rglob(name):
        if ".debug" not in path.parts and path.is_file():
            return path
    return None


def find_candidates(root: Path, bits: int, minimum: str | None) -> list[GlibcCandidate]:
    suffix = "_amd64" if bits == 64 else "_i386"
    loader = loader_name(bits)
    candidates: list[GlibcCandidate] = []
    for directory in root.iterdir():
        if not directory.is_dir() or not directory.name.endswith(suffix):
            continue
        version = directory.name.removesuffix(suffix).split("-", 1)[0]
        if not version or not all(part.isdigit() for part in version.split(".")):
            continue
        if minimum is not None and _version_key(version) < _version_key(minimum):
            continue
        candidates.append(
            GlibcCandidate(
                directory=directory,
                version=version,
                libc=_find_file(directory, LIBC),
                loader=_find_file(directory, loader),
            )
        )
    candidates = sorted(candidates, key=lambda item: (item.version, item.directory.name))
    if minimum is not None:
        exact = [candidate for candidate in candidates if candidate.version == minimum]
        if exact:
            return exact
    return candidates


def _config_root(config: Path) -> Path:
    with config.open("rb") as stream:
        return Path(tomllib.load(stream)["glibc"]["root"]).expanduser()


def _choose(title: str, candidates: list[GlibcCandidate], field: str) -> GlibcCandidate | None:
    available = [candidate for candidate in candidates if getattr(candidate, field) is not None]
    print(f"{title}:")
    print("0) 不修改")
    for index, candidate in enumerate(available, 1):
        print(f"{index}) {candidate.directory}")
    while True:
        try:
            value = input("请选择索引 [0]: ").strip() or "0"
        except EOFError:
            print("未修改")
            return None
        try:
            index = int(value)
        except ValueError:
            print("失败：索引必须是数字")
            continue
        if index == 0:
            return None
        if 1 <= index <= len(available):
            return available[index - 1]
        print("失败：索引超出范围")


def _patch(path: Path, replacements: dict[str, Path], interpreter: Path, rpath: Path) -> None:
    command = ["patchelf", "--force-rpath", "--set-rpath", str(rpath)]
    command.extend(
        argument
        for name, replacement in replacements.items()
        for argument in ("--replace-needed", name, str(replacement))
    )
    command.extend(("--set-interpreter", str(interpreter), str(path)))
    subprocess.run(command, check=True, capture_output=True, text=True)


def switch_elf(path: Path, config: Path = Path("configs/pwnkit.toml")) -> bool:
    scan = scan_dependencies(path)
    bits = scan.metadata.bits
    loader = loader_name(bits)
    logger.debug("file: %s", path)
    logger.debug("architecture: %s-bit %s", bits, scan.metadata.machine)
    logger.debug("interpreter: %s", scan.metadata.interpreter)
    logger.debug("needed: %s", scan.metadata.needed)
    logger.debug("all local dependencies: %s", scan.local)
    logger.debug("missing dependencies: %s", scan.missing)
    logger.debug("minimum libc version: %s", scan.metadata.min_glibc)
    if scan.metadata.machine not in {"x64", "x86"}:
        print(f"失败：暂不支持 {scan.metadata.machine} 架构")
        return False
    unsupported = [name for name in scan.missing if name not in {LIBC, loader}]
    if unsupported:
        print(f"失败：缺少非 glibc 依赖：{', '.join(unsupported)}")
        return False

    libc = scan.local.get(LIBC)
    interpreter = scan.local.get(loader)
    if libc is None or interpreter is None:
        candidates = find_candidates(_config_root(config), bits, scan.metadata.min_glibc)
        logger.debug("glibc candidates: %s", candidates)
        if not candidates:
            print("失败：没有找到满足架构和 libc 版本要求的候选库")
            return False
        if libc is None:
            candidate = _choose("选择 libc.so.6", candidates, "libc")
            if candidate is None:
                print("未修改")
                return True
            libc = candidate.libc
            if interpreter is None:
                interpreter = candidate.loader
        if interpreter is None:
            candidate = _choose("选择 ld-linux", candidates, "loader")
            if candidate is None:
                print("未修改")
                return True
            interpreter = candidate.loader

    replacements = {
        name: scan.local[Path(name).name]
        for name in scan.metadata.needed
        if Path(name).name in scan.local
    }
    replacements[LIBC] = libc
    try:
        _patch(path, replacements, interpreter, path.parent)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"失败：patchelf 修改 ELF 失败：{exc}")
        return False
    print(f"成功：已修改 {path}")
    return True
