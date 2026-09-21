import argparse
import logging
from pathlib import Path

from elftools.common.exceptions import ELFError

from pwnkit.elf.imports import get_imports


logger = logging.getLogger("pwnkit")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pwnkit")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="show debug output",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    chlibc = commands.add_parser("chlibc", help="inspect ELF libc dependencies")
    chlibc.add_argument("elf", type=Path, help="ELF file to inspect")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(message)s",
    )

    if args.command == "chlibc":
        try:
            imports = get_imports(args.elf)
        except (OSError, ELFError) as exc:
            logger.debug("failed to inspect %s: %s", args.elf, exc)
            return 1
        logger.debug("file: %s", args.elf)
        logger.debug("imports: %s", imports)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
