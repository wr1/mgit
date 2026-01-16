"""Branch management operations."""
from pathlib import Path
from typing import Optional

from ..utils.repo_paths import get_repo_paths
from ..config import load_config
from ..utils.logger import logger
from ..utils.run_command import run_command


def branch(
    root: Path,
    name: str,
    delete: bool = False,
    sync: bool = False,
    profile: Optional[str] = None,
) -> None:
    """Manage branches."""
    config = load_config(root)
    repos = config.profiles.get(profile or "all", [])
    repo_paths = get_repo_paths(root, repos)
    if delete:
        logger.info(f"Deleting branch '{name}' in repos: {repos}")
        for repo in repo_paths:
            logger.info(f"Deleting branch '{name}' in {repo.name}")
            result = run_command(["git", "branch", "-D", name], cwd=repo)
            if result.returncode != 0:
                logger.error(f"Failed to delete branch in {repo.name}: {result.stderr}")
    elif sync:
        current = run_command(
            ["git", "branch", "--show-current"], cwd=root / repos[0],
        ).stdout.strip()
        logger.info(f"Syncing to branch '{current}' in repos: {repos}")
        for repo in repo_paths:
            logger.info(f"Checking out '{current}' in {repo.name}")
            result = run_command(["git", "checkout", current], cwd=repo)
            if result.returncode != 0:
                logger.error(f"Failed to checkout in {repo.name}: {result.stderr}")
    else:
        logger.info(f"Creating branch '{name}' in repos: {repos}")
        for repo in repo_paths:
            logger.info(f"Creating and checking out '{name}' in {repo.name}")
            result = run_command(["git", "checkout", "-b", name], cwd=repo)
            if result.returncode != 0:
                logger.error(f"Failed to create branch in {repo.name}: {result.stderr}")
