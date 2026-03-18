"""Push operations."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

from ..utils.repo_paths import get_repo_paths
from ..config import load_config
from ..utils.logger import logger
from ..utils.run_command import run_command
from ..utils.output import emit


def push_repos(root: Path, profile: Optional[str] = None, fmt: str = "rich") -> None:
    """Push current branch to remote in repos."""
    config = load_config(root)
    repos = config.profiles.get(profile or "all", [])
    logger.info(f"Pushing in repos: {repos}")
    repo_paths = get_repo_paths(root, repos)
    results: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=max(1, len(repo_paths))) as executor:
        future_to_repo = {
            executor.submit(_push_single_repo, repo): repo for repo in repo_paths
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
        print(f"{marker} {repo_name}: {info['output'][:120]}")


def _push_single_repo(repo: Path) -> dict:
    """Push for a single repo and return structured result."""
    branch = run_command(
        ["git", "branch", "--show-current"],
        cwd=repo,
    ).stdout.strip()
    logger.info(f"Pushing branch '{branch}' in {repo.name}")
    upstream_check = run_command(
        ["git", "rev-parse", "--abbrev-ref", f"{branch}@{{upstream}}"],
        cwd=repo,
    )
    if upstream_check.returncode != 0:
        logger.info(f"Setting upstream for {branch} in {repo.name}")
        result = run_command(
            ["git", "push", "--set-upstream", "origin", branch],
            cwd=repo,
        )
    else:
        result = run_command(["git", "push"], cwd=repo)
    if result.returncode != 0:
        logger.error(f"Failed to push in {repo.name}: {result.stderr}")
        return {"status": "error", "output": result.stderr.strip()}
    else:
        logger.info(f"Pushed in {repo.name}")
        return {"status": "ok", "output": (result.stdout + result.stderr).strip()}
