import re
from dataclasses import dataclass
from pathlib import Path

from elftools.elf.elffile import ELFFile


@dataclass(frozen=True)
class ElfMetadata:
    path: Path
    bits: int
    machine: str
    needed: tuple[str, ...]
    interpreter: str | None
    min_glibc: str | None


def inspect_elf(path: str | Path) -> ElfMetadata:
    path = Path(path)
    with path.open("rb") as stream:
        elf = ELFFile(stream)
        dynamic = elf.get_section_by_name(".dynamic")
        needed = tuple(
            tag.needed
            for tag in dynamic.iter_tags()
            if tag.entry.d_tag == "DT_NEEDED"
        ) if dynamic is not None else ()
        interpreter = next(
            (
                segment.get_interp_name()
                for segment in elf.iter_segments()
                if segment["p_type"] == "PT_INTERP"
            ),
            None,
        )
        versions = {
            match.group(1)
            for section in [elf.get_section_by_name(".gnu.version_r")]
            if section is not None
            for _, auxiliary in section.iter_versions()
            for version in auxiliary
            if (match := re.fullmatch(r"GLIBC_(\d+\.\d+)", version.name))
        }
        min_glibc = max(versions, key=lambda value: tuple(map(int, value.split("."))), default=None)
        return ElfMetadata(
            path=path,
            bits=elf.elfclass,
            machine=elf.get_machine_arch(),
            needed=needed,
            interpreter=interpreter,
            min_glibc=min_glibc,
        )
