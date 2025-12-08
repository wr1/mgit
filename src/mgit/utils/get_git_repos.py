"""Git repo discovery utilities."""
from pathlib import Path
from typing import List


def get_git_repos(root: Path) -> List[Path]:
    """Find all git repos in subdirs."""
    return [d for d in root.iterdir() if d.is_dir() and (d / ".git").exists()]
