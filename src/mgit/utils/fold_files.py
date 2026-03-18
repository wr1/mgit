"""File folding utilities."""

from pathlib import Path
from typing import List

import pyperclip

from ..utils.run_command import run_command


def fold_files(files: List[Path], output: Path) -> None:
    """Fold files using cfold binary."""
    cmd = ["cfold", "fold", "--clip", "False", "--output", str(output)] + [
        str(f) for f in files
    ]
    result = run_command(cmd)
    if result.returncode != 0:
        raise RuntimeError(f"cfold fold failed: {result.stderr}")
    pyperclip.copy(output.read_text())
