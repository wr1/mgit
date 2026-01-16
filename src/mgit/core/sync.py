"""Sync operations."""
from pathlib import Path
from typing import Optional

from . import get_repo_paths
from ..config import load_config
from ..utils.logger import logger
from ..utils.run_command import run_command


def sync_repos(root: Path, profile: Optional[str] = None) -> None:
    """Run uv sync --dev in each repo."""
    config = load_config(root)
    repos = config.profiles.get(profile or "all", [])
    logger.info(f"Syncing dependencies in repos: {repos}")
    repo_paths = get_repo_paths(root, repos)
    for repo in repo_paths:
        logger.info(f"Running 'uv sync --dev' in {repo.name}")
        result = run_command(["uv", "sync", "--dev"], cwd=repo)
        if result.returncode != 0:
            logger.error(f"Failed to sync in {repo.name}: {result.stderr}")
        else:
            logger.info(f"Synced in {repo.name}")
