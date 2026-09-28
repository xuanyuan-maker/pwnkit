import datetime
import logging
import stat
import subprocess
from pathlib import Path

from elftools.common.exceptions import ELFError

from pwnkit.elf.metadata import inspect_elf
from pwnkit.libc.switcher import scan_dependencies, switch_elf


logger = logging.getLogger("pwnkit")
TEMPLATES = {"": "exp.py", "heap": "exp_heap.py"}


def _package_src() -> Path:
    return Path(__file__).resolve().parents[1]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _chmod_x(path: Path) -> None:
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _run_checksec(path: Path) -> None:
    try:
        subprocess.run(["pwn", "checksec", f"--file={path}"])
    except FileNotFoundError:
        print("警告：找不到 pwn 命令，跳过 checksec")


def init_elf(path: Path, template_type: str = "") -> bool:
    path = path.expanduser().resolve()
    if not path.is_file():
        print(f"失败：ELF 不存在或者不是文件：{path}")
        return False

    try:
        metadata = inspect_elf(path)
        scan = scan_dependencies(path)
    except (OSError, ELFError) as exc:
        logger.debug("init inspection failed: %s", exc)
        print(f"失败：无法检查 ELF：{path}")
        return False

    if metadata.machine not in {"x64", "x86"}:
        print(f"失败：暂不支持 {metadata.machine} 架构")
        return False
    arch = "amd64" if metadata.bits == 64 else "i386"

    for dependency in {path, *scan.local.values()}:
        try:
            _chmod_x(dependency)
        except OSError as exc:
            logger.debug("chmod failed for %s: %s", dependency, exc)
            print(f"警告：无法添加可执行权限：{dependency}")

    if not switch_elf(path):
        return False

    _run_checksec(path)
    template = TEMPLATES[template_type]
    template_path = _repo_root() / "templates" / template
    if not template_path.is_file():
        print(f"失败：找不到模板：{template_path}")
        return False

    content = template_path.read_text(encoding="utf-8")
    content = (
        content.replace("[ARCH]", arch)
        .replace("[ELF_PATH]", str(path))
        .replace("[PWNKIT_PATH]", str(_package_src()))
    )
    output = path.parent / "exp.py"
    if output.exists():
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = output.with_suffix(f"{output.suffix}.bak_{timestamp}")
        output.rename(backup)
        print(f"已备份原 exp.py：{backup.name}")
    output.write_text(content, encoding="utf-8")
    try:
        _chmod_x(output)
    except OSError as exc:
        logger.debug("chmod failed for %s: %s", output, exc)
        print(f"警告：无法添加可执行权限：{output}")
    print(f"成功：已生成 {output}")
    return True
