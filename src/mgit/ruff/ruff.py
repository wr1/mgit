"""Ruff operations."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

from ..utils.repo_paths import get_repo_paths
from ..config import load_config
from ..utils.logger import logger
from ..utils.run_command import run_command


def ruff_format(root: Path, profile: Optional[str] = None) -> None:
    """Run ruff format in repos in parallel."""
    config = load_config(root)
    repos = config.profiles.get(profile or "all", [])
    logger.info(f"Running ruff format in repos: {repos}")
    repo_paths = get_repo_paths(root, repos)
    results = {}
    with ThreadPoolExecutor(max_workers=len(repo_paths)) as executor:
        future_to_repo = {
            executor.submit(_ruff_format_single_repo, repo): repo for repo in repo_paths
        }
        for future in as_completed(future_to_repo):
            repo = future_to_repo[future]
            try:
                output = future.result()
                results[repo.name] = output
            except Exception as exc:
                results[repo.name] = f"Error: {exc}"
    for repo_name, output in results.items():
        print(f"Ruff format output for {repo_name}:")
        print(output)


def _ruff_format_single_repo(repo: Path) -> str:
    """Run ruff format for a single repo and return output."""
    logger.info(f"Running 'ruff format' in {repo.name}")
    result = run_command(["ruff", "format"], cwd=repo)
    if result.returncode != 0:
        logger.error(f"Failed to format in {repo.name}: {result.stderr}")
        return result.stderr
    else:
        logger.info(f"Formatted in {repo.name}")
        return (result.stdout + result.stderr).strip()


def ruff_check_fix(root: Path, profile: Optional[str] = None) -> None:
    """Run ruff check --fix --unsafe-fixes in repos in parallel."""
    config = load_config(root)
    repos = config.profiles.get(profile or "all", [])
    logger.info(f"Running ruff check --fix --unsafe-fixes in repos: {repos}")
    repo_paths = get_repo_paths(root, repos)
    results = {}
    with ThreadPoolExecutor(max_workers=len(repo_paths)) as executor:
        future_to_repo = {
            executor.submit(_ruff_check_fix_single_repo, repo): repo
            for repo in repo_paths
        }
        for future in as_completed(future_to_repo):
            repo = future_to_repo[future]
            try:
                output = future.result()
                results[repo.name] = output
            except Exception as exc:
                results[repo.name] = f"Error: {exc}"
    for repo_name, output in results.items():
        print(f"Ruff check output for {repo_name}:")
        print(output)


def _ruff_check_fix_single_repo(repo: Path) -> str:
    """Run ruff check --fix --unsafe-fixes for a single repo and return output."""
    logger.info(f"Running 'ruff check --fix --unsafe-fixes' in {repo.name}")
    result = run_command(["ruff", "check", "--fix", "--unsafe-fixes"], cwd=repo)
    if result.returncode != 0:
        logger.error(f"Failed to check/fix in {repo.name}: {result.stderr}")
        return result.stderr
    else:
        logger.info(f"Checked/fixed in {repo.name}")
        return (result.stdout + result.stderr).strip()
