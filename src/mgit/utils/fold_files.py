"""File folding utilities."""
from pathlib import Path
from typing import List

import pyperclip


def fold_files(files: List[Path], output: Path) -> None:
    """Fold files using cfold or cat."""
    try:
        from cfold.cli.fold import fold

        fold(
            files=[str(f) for f in files],
            output=str(output),
            prompt=None,
            dialect="default",
            bare=False,
        )
    except ImportError:
        # Fallback to cat
        with open(output, "w") as f:
            for file in files:
                f.write(f"# {file}\n")
                f.write(file.read_text())
                f.write("\n")
    pyperclip.copy(output.read_text())
