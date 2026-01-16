"""Dependency finding utilities."""
from pathlib import Path
from typing import Dict, Set

from .extract_imports import extract_imports

from ..config import Config


def find_dependencies(files: Set[Path], import_map: Dict[str, str], root: Path) -> Set[str]:
    """Find additional repos based on imports."""
    deps = set()
    for file in files:
        imports = extract_imports(file)
        for imp in imports:
            if imp in import_map:
                deps.add(import_map[imp])
    return deps
