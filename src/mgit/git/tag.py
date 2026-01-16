"""Tag operations."""
from pathlib import Path
from typing import Optional

from ..utils.repo_paths import get_repo_paths
from ..config import load_config
from ..utils.logger import logger
from ..utils.run_command import run_command


def tag_repos(
    root: Path, tag: str, push: bool = False, profile: Optional[str] = None,
) -> None:
    """Create git tag in repos."""
    config = load_config(root)
    repos = config.profiles.get(profile or "all", [])
    logger.info(f"Tagging '{tag}' in repos: {repos}")
    repo_paths = get_repo_paths(root, repos)
    for repo in repo_paths:
        logger.info(f"Creating tag '{tag}' in {repo.name}")
        result = run_command(["git", "tag", tag], cwd=repo)
        if result.returncode != 0:
            logger.error(f"Failed to create tag in {repo.name}: {result.stderr}")
        else:
            logger.info(f"Tagged '{tag}' in {repo.name}")
            if push:
                logger.info(f"Pushing tag '{tag}' in {repo.name}")
                push_result = run_command(["git", "push", "origin", tag], cwd=repo)
                if push_result.returncode != 0:
                    logger.error(
                        f"Failed to push tag in {repo.name}: {push_result.stderr}",
                    )
                else:
                    logger.info(f"Pushed tag '{tag}' in {repo.name}")
