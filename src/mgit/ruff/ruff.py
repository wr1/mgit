"""Ruff operations."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

from ..utils.repo_paths import get_repo_paths
from ..config import load_config
from ..utils.logger import logger
from ..utils.run_command import run_command
from ..utils.output import emit


def ruff_format(root: Path, profile: Optional[str] = None, fmt: str = "rich") -> None:
    """Run ruff format in repos in parallel."""
    config = load_config(root)
    repos = config.profiles.get(profile or "all", [])
    logger.info(f"Running ruff format in repos: {repos}")
    repo_paths = get_repo_paths(root, repos)
    results: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=max(1, len(repo_paths))) as executor:
        future_to_repo = {
            executor.submit(_ruff_format_single_repo, repo): repo for repo in repo_paths
        }
        for future in as_completed(future_to_repo):
            repo = future_to_repo[future]
            try:
                results[repo.name] = future.result()
            except Exception as exc:
                results[repo.name] = {"status": "error", "output": str(exc)}

    if fmt != "rich":
        emit({"profile": profile or "all", "repos": results}, fmt)
        return

    for repo_name, info in results.items():
        marker = "✓" if info["status"] == "ok" else "✗"
        print(f"ruff format {marker} {repo_name}: {info['output'][:120]}")


def _ruff_format_single_repo(repo: Path) -> dict:
    """Run ruff format for a single repo and return structured result."""
    logger.info(f"Running 'ruff format' in {repo.name}")
    result = run_command(["ruff", "format"], cwd=repo)
    if result.returncode != 0:
        logger.error(
            f"Failed to format in {repo.name}: {result.stdout} {result.stderr}"
        )
        return {"status": "error", "output": result.stderr.strip()}
    logger.info(f"Formatted in {repo.name}")
    return {"status": "ok", "output": (result.stdout + result.stderr).strip()}


def ruff_fix(root: Path, profile: Optional[str] = None, fmt: str = "rich") -> None:
    """Run ruff check --fix --unsafe-fixes in repos in parallel."""
    config = load_config(root)
    repos = config.profiles.get(profile or "all", [])
    logger.info(f"Running ruff check --fix --unsafe-fixes in repos: {repos}")
    repo_paths = get_repo_paths(root, repos)
    results: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=max(1, len(repo_paths))) as executor:
        future_to_repo = {
            executor.submit(_ruff_fix_single_repo, repo): repo for repo in repo_paths
        }
        for future in as_completed(future_to_repo):
            repo = future_to_repo[future]
            try:
                results[repo.name] = future.result()
            except Exception as exc:
                results[repo.name] = {"status": "error", "output": str(exc)}

    if fmt != "rich":
        emit({"profile": profile or "all", "repos": results}, fmt)
        return

    for repo_name, info in results.items():
        marker = "✓" if info["status"] == "ok" else "✗"
        print(f"ruff fix {marker} {repo_name}: {info['output'][:120]}")


def _ruff_fix_single_repo(repo: Path) -> dict:
    """Run ruff check --fix --unsafe-fixes for a single repo and return structured result."""
    logger.info(f"Running 'ruff check --fix --unsafe-fixes' in {repo.name}")
    result = run_command(["ruff", "check", "--fix", "--unsafe-fixes"], cwd=repo)
    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0:
        logger.error(f"Failed to check/fix in {repo.name}: {output}")
        return {"status": "error", "output": output}
    logger.info(f"Checked/fixed in {repo.name}")
    return {"status": "ok", "output": output}
