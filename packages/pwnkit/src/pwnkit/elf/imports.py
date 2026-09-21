from pathlib import Path

from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection


def get_imports(path: str | Path) -> list[str]:
    """Return undefined symbols from an ELF dynamic symbol table."""
    with Path(path).open("rb") as stream:
        elf = ELFFile(stream)
        section = elf.get_section_by_name(".dynsym")
        if not isinstance(section, SymbolTableSection):
            return []
        return [
            symbol.name
            for symbol in section.iter_symbols()
            if symbol.name and symbol["st_shndx"] == "SHN_UNDEF"
        ]
