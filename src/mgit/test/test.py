"""Test operations."""
from pathlib import Path
from typing import Optional

from ..utils.repo_paths import get_repo_paths
from ..config import load_config
from ..utils.find_matching_repos import find_matching_repos
from ..utils.logger import logger
from ..utils.run_command import run_command


def run_tests(
    root: Path,
    glob: Optional[str] = None,
    parallel: bool = True,
    profile: Optional[str] = None,
) -> None:
    """Run pytest in matching repos."""
    config = load_config(root)
    repos = config.profiles.get(profile or "all", [])
    if glob:
        repos = find_matching_repos(repos, glob)
        logger.info(f"Filtered repos with glob '{glob}': {repos}")
    logger.info(f"Running tests in repos: {repos} with parallel={parallel}")
    repo_paths = get_repo_paths(root, repos)
    for repo in repo_paths:
        cmd = ["uv", "run", "--active", "pytest"]
        if parallel:
            cmd.extend(["-n", "auto"])
        logger.info(f"Running '{' '.join(cmd)}' in {repo.name}")
        result = run_command(cmd, cwd=repo)
        if result.returncode != 0:
            logger.error(f"Tests failed in {repo.name}: {result.stderr}")
        else:
            logger.info(f"Tests passed in {repo.name}")
