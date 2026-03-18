"""Version bumping and synchronization across toolbox repositories.

Driven by the master repo (default: b3m, configurable in .mgitrc).
Uses `uv version --bump` on the master then propagates the exact version.
"""

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table

from ..config import load_config
from ..utils.logger import logger
from ..utils.repo_paths import get_repo_paths
from ..utils.run_command import run_command

console = Console()


def bump_version(
    root: Path,
    level: str = "patch",
    profile: Optional[str] = None,
    dry_run: bool = False,
    commit: bool = False,
    tag: bool = False,
) -> None:
    """Bump version in master repo (uv) then sync the exact same version to all others."""
    config = load_config(root)
    master = config.master_repo
    master_path = root / master

    if not master_path.exists():
        console.print(f"[red]✗ Master repo '{master}' not found[/red]")
        return

    console.print(
        f"[bold cyan]mgit version bump[/bold cyan] — master: [cyan]{master}[/cyan]"
    )

    # 1. Bump master with uv
    bump_cmd = ["uv", "version", "--bump", level]
    if commit:
        bump_cmd.append("--commit")
    if tag:
        bump_cmd.append("--tag")

    logger.info(f"Bumping {level} in master {master}")
    result = run_command(bump_cmd, cwd=master_path)
    if result.returncode != 0:
        console.print(f"[red]✗ uv version bump failed: {result.stderr}[/red]")
        return

    # 2. Read new version
    pyproject = master_path / "pyproject.toml"
    content = pyproject.read_text(encoding="utf-8")
    import re

    match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
    if not match:
        console.print("[red]✗ Could not read new version[/red]")
        return
    new_version = match.group(1)
    console.print(f"[green]→ New version: {new_version}[/green]")

    # 3. Sync to other repos
    repos = config.profiles.get(profile or "all", [])
    repo_paths = get_repo_paths(root, repos)

    table = Table(title="Version sync plan")
    table.add_column("Repository")
    table.add_column("Status")

    updated = 0
    for repo in repo_paths:
        if repo.name == master:
            table.add_row(repo.name, "[dim]master (already bumped)[/dim]")
            continue
        if not (repo / "pyproject.toml").exists():
            table.add_row(repo.name, "[dim]no pyproject.toml[/dim]")
            continue

        if dry_run:
            table.add_row(repo.name, f"[yellow]would set → {new_version}[/yellow]")
            continue

        # Set exact version with uv
        set_cmd = ["uv", "version", new_version]
        set_result = run_command(set_cmd, cwd=repo)
        if set_result.returncode == 0:
            table.add_row(repo.name, f"[green]✓ {new_version}[/green]")
            updated += 1

            if commit:
                run_command(["git", "add", "pyproject.toml"], cwd=repo)
                run_command(
                    ["git", "commit", "-m", f"chore(version): sync to {new_version}"],
                    cwd=repo,
                )
        else:
            table.add_row(repo.name, "[red]✗ failed[/red]")

    console.print(table)
    if dry_run:
        console.print("[dim]— dry-run complete —[/dim]")
    else:
        console.print(
            f"[bold green]✓ Version {new_version} synced across toolbox[/bold green]"
        )
