"""Commit operations."""

from pathlib import Path
from typing import Optional

from ..utils.repo_paths import get_repo_paths
from ..config import load_config
from ..utils.logger import logger
from ..utils.run_command import run_command


def commit_repos(
    root: Path,
    all: bool = False,
    message: str = "Auto commit new files",
    profile: Optional[str] = None,
) -> None:
    """Auto-commit in repos."""
    config = load_config(root)
    repos = config.profiles.get(profile or "all", [])
    logger.info(f"Committing in repos: {repos} with all={all}, message='{message}'")
    repo_paths = get_repo_paths(root, repos)
    for repo in repo_paths:
        logger.info(f"Committing in {repo.name}")
        if all:
            logger.info(f"Adding basic files in {repo.name}")
            result_add = run_command(
                ["git", "add", "*.py", "pyproject.toml", "README.md"],
                cwd=repo,
            )
            if result_add.returncode != 0:
                logger.error(f"Failed to add files in {repo.name}: {result_add.stderr}")
                continue
            logger.info(f"Added basic files in {repo.name}")
        else:
            # Add specific files - check if dirs exist
            paths = ["src/", "tests/", "examples/", "pyproject.toml", "README.md"]
            added_any = False
            for path in paths:
                if path.endswith("/"):
                    if (repo / path).exists():
                        logger.info(f"Adding {path} in {repo.name}")
                        result_add = run_command(["git", "add", path], cwd=repo)
                        if result_add.returncode == 0:
                            added_any = True
                        else:
                            logger.warning(
                                f"Failed to add {path} in {repo.name}: {result_add.stderr}",
                            )
                else:
                    # For files like pyproject.toml, README.md, add if exists
                    if (repo / path).exists():
                        logger.info(f"Adding {path} in {repo.name}")
                        result_add = run_command(["git", "add", path], cwd=repo)
                        if result_add.returncode == 0:
                            added_any = True
                        else:
                            logger.warning(
                                f"Failed to add {path} in {repo.name}: {result_add.stderr}",
                            )
            if added_any:
                logger.info(f"Added specific files in {repo.name}")
            else:
                logger.info(f"No specific files to add in {repo.name}")
        # Check if there are staged changes
        result_staged = run_command(["git", "diff", "--cached", "--quiet"], cwd=repo)
        if result_staged.returncode == 0:
            logger.info(f"Nothing staged to commit in {repo.name}")
            continue
        logger.info(f"Committing in {repo.name}")
        result_commit = run_command(
            ["git", "commit", "-m", message, "--no-edit"],
            cwd=repo,
        )
        if result_commit.returncode != 0:
            logger.error(
                f"Failed to commit in {repo.name}: {result_commit.stderr or result_commit.stdout}",
            )
        else:
            logger.info(f"Committed in {repo.name}")
            # Show diff
            diff_result = run_command(["git", "show"], cwd=repo)
            if diff_result.returncode == 0:
                print(f"Commit diff for {repo.name}:")
                print(diff_result.stdout)
