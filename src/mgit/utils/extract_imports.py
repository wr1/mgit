"""Import extraction utilities."""
import ast
from pathlib import Path
from typing import Set


def extract_imports(file: Path) -> Set[str]:
    """Extract import names from a Python file."""
    imports = set()
    try:
        with open(file, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split(".")[0])
    except Exception:
        pass
    return imports
