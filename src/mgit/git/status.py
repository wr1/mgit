"""Status operations."""

from pathlib import Path
from typing import Optional

import rich.table

from ..utils.repo_paths import get_repo_paths
from ..config import load_config
from ..utils.logger import logger
from ..utils.run_command import run_command
from ..utils.output import emit


def status(root: Path, profile: Optional[str] = None, fmt: str = "rich") -> None:
    """Show status table."""
    config = load_config(root)
    repos = config.profiles.get(profile or "all", [])
    logger.info(f"Loading status for profile '{profile or 'all'}' with repos: {repos}")
    repo_paths = get_repo_paths(root, repos)

    rows: list[dict] = []
    for repo in repo_paths:
        logger.info(f"Checking status for {repo.name}")
        branch = run_command(
            ["git", "branch", "--show-current"],
            cwd=repo,
        ).stdout.strip()
        dirty = bool(run_command(["git", "status", "--porcelain"], cwd=repo).stdout)
        ahead_behind_raw = run_command(
            ["git", "status", "-b", "--porcelain"],
            cwd=repo,
        ).stdout.split()[1:3]
        rows.append({
            "repo": repo.name,
            "branch": branch,
            "dirty": dirty,
            "ahead_behind": "/".join(ahead_behind_raw),
        })

    if fmt != "rich":
        emit({"profile": profile or "all", "repos": rows}, fmt)
        return

    table = rich.table.Table(title="Repo Status")
    table.add_column("Repo")
    table.add_column("Branch")
    table.add_column("Dirty")
    table.add_column("Ahead/Behind")
    for row in rows:
        table.add_row(row["repo"], row["branch"], "Yes" if row["dirty"] else "No", row["ahead_behind"])
    rich.print(table)
