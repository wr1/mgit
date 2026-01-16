"""Status operations."""
from pathlib import Path
from typing import Optional

import rich.table

from ..utils.repo_paths import get_repo_paths
from ..config import load_config
from ..utils.logger import logger
from ..utils.run_command import run_command


def status(root: Path, profile: Optional[str] = None) -> None:
    """Show status table."""
    config = load_config(root)
    repos = config.profiles.get(profile or "all", [])
    logger.info(f"Loading status for profile '{profile or 'all'}' with repos: {repos}")
    repo_paths = get_repo_paths(root, repos)
    table = rich.table.Table(title="Repo Status")
    table.add_column("Repo")
    table.add_column("Branch")
    table.add_column("Dirty")
    table.add_column("Ahead/Behind")
    for repo in repo_paths:
        logger.info(f"Checking status for {repo.name}")
        branch = run_command(
            ["git", "branch", "--show-current"], cwd=repo,
        ).stdout.strip()
        dirty = (
            "Yes"
            if run_command(["git", "status", "--porcelain"], cwd=repo).stdout
            else "No"
        )
        ahead_behind = run_command(
            ["git", "status", "-b", "--porcelain"], cwd=repo,
        ).stdout.split()[1:3]
        table.add_row(repo.name, branch, dirty, "/".join(ahead_behind))
    rich.print(table)
