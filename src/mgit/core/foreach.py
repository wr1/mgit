"""Foreach operations."""
from pathlib import Path
from typing import Optional

from . import get_repo_paths
from ..config import load_config
from ..utils.logger import logger
from ..utils.run_command import run_command


def foreach(root: Path, cmd: str, profile: Optional[str] = None) -> None:
    """Run command in each repo."""
    config = load_config(root)
    repos = config["profiles"].get(profile or "all", [])
    logger.info(f"Running '{cmd}' in repos: {repos}")
    repo_paths = get_repo_paths(root, repos)
    for repo in repo_paths:
        logger.info(f"Running in {repo.name}: {cmd}")
        result = run_command(cmd.split(), cwd=repo)
        if result.returncode != 0:
            logger.error(f"Failed in {repo.name}: {result.stderr}")
        else:
            logger.info(f"Succeeded in {repo.name}")
