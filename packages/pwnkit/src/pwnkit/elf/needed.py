from pathlib import Path

from elftools.elf.elffile import ELFFile


def get_needed(path: str | Path) -> list[str]:
    """Return the shared libraries listed by ELF DT_NEEDED entries."""
    with Path(path).open("rb") as stream:
        elf = ELFFile(stream)
        dynamic = elf.get_section_by_name(".dynamic")
        if dynamic is None:
            return []
        return [
            tag.needed
            for tag in dynamic.iter_tags()
            if tag.entry.d_tag == "DT_NEEDED"
        ]
