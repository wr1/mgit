"""Core operations for mgit."""
from pathlib import Path
from typing import List

from ..config import load_config
from ..utils.logger import logger


def get_repo_paths(root: Path, repos: List[str]) -> List[Path]:
    """Get full paths for repos."""
    return [root / r for r in repos if (root / r).is_dir()]
