"""Command execution utilities."""
import subprocess
from pathlib import Path
from typing import List, Optional


def run_command(
    cmd: List[str], cwd: Optional[Path] = None,
) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    return subprocess.run(cmd, check=False, cwd=cwd, capture_output=True, text=True)
