"""Core operations for mgit."""

from pathlib import Path
from typing import List, Optional

import rich.table

from . import logger
from .config import load_config
from .utils import (
    find_dependencies,
    find_matching_repos,
    fold_files,
    resolve_targets,
    run_command,
)


def get_repo_paths(root: Path, repos: List[str]) -> List[Path]:
    """Get full paths for repos."""
    return [root / r for r in repos if (root / r).is_dir()]


def status(root: Path, profile: Optional[str] = None) -> None:
    """Show status table."""
    config = load_config(root)
    repos = config["profiles"].get(profile or "all", [])
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


def foreach(root: Path, cmd: str, profile: Optional[str] = None) -> None:
    """Run command in each repo."""
    config = load_config(root)
    repos = config["profiles"].get(profile or "all", [])
    logger.info(f"Running '{cmd}' in repos: {repos}")
    repo_paths = get_repo_paths(root, repos)
    for repo in repo_paths:
        logger.info(f"Running in {repo.name}: {cmd}")
        result = run_command(cmd.split(), cwd=repo)
        if result.returncode != 0:
            logger.error(f"Failed in {repo.name}: {result.stderr}")
        else:
            logger.info(f"Succeeded in {repo.name}")


def branch(
    root: Path,
    name: str,
    delete: bool = False,
    sync: bool = False,
    profile: Optional[str] = None,
) -> None:
    """Manage branches."""
    config = load_config(root)
    repos = config["profiles"].get(profile or "all", [])
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


def sync_repos(root: Path, profile: Optional[str] = None) -> None:
    """Run uv sync --dev in each repo."""
    config = load_config(root)
    repos = config["profiles"].get(profile or "all", [])
    logger.info(f"Syncing dependencies in repos: {repos}")
    repo_paths = get_repo_paths(root, repos)
    for repo in repo_paths:
        logger.info(f"Running 'uv sync --dev' in {repo.name}")
        result = run_command(["uv", "sync", "--dev"], cwd=repo)
        if result.returncode != 0:
            logger.error(f"Failed to sync in {repo.name}: {result.stderr}")
        else:
            logger.info(f"Synced in {repo.name}")


def run_tests(
    root: Path,
    glob: Optional[str] = None,
    parallel: bool = True,
    profile: Optional[str] = None,
) -> None:
    """Run pytest in matching repos."""
    config = load_config(root)
    repos = config["profiles"].get(profile or "all", [])
    if glob:
        repos = find_matching_repos(repos, glob)
        logger.info(f"Filtered repos with glob '{glob}': {repos}")
    logger.info(f"Running tests in repos: {repos} with parallel={parallel}")
    repo_paths = get_repo_paths(root, repos)
    for repo in repo_paths:
        cmd = ["pytest"]
        if parallel:
            cmd.extend(["-n", "auto"])
        logger.info(f"Running '{' '.join(cmd)}' in {repo.name}")
        result = run_command(cmd, cwd=repo)
        if result.returncode != 0:
            logger.error(f"Tests failed in {repo.name}: {result.stderr}")
        else:
            logger.info(f"Tests passed in {repo.name}")


def commit_repos(
    root: Path,
    all: bool = False,
    message: str = "Auto commit new files",
    profile: Optional[str] = None,
) -> None:
    """Auto-commit in repos."""
    config = load_config(root)
    repos = config["profiles"].get(profile or "all", [])
    logger.info(f"Committing in repos: {repos} with all={all}, message='{message}'")
    repo_paths = get_repo_paths(root, repos)
    for repo in repo_paths:
        logger.info(f"Committing in {repo.name}")
        if all:
            logger.info(f"Adding basic files in {repo.name}")
            result_add = run_command(
                ["git", "add", "*.py", "pyproject.toml", "README.md"], cwd=repo,
            )
            if result_add.returncode != 0:
                logger.error(f"Failed to add files in {repo.name}: {result_add.stderr}")
                continue
            logger.info(f"Added basic files in {repo.name}")
        else:
            # Add specific files - check if dirs exist
            paths = ["src/", "tests/", "examples/"]
            added_any = False
            for path in paths:
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
            ["git", "commit", "-m", message, "--no-edit"], cwd=repo,
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


def push_repos(root: Path, profile: Optional[str] = None) -> None:
    """Push current branch to remote in repos."""
    config = load_config(root)
    repos = config["profiles"].get(profile or "all", [])
    logger.info(f"Pushing in repos: {repos}")
    repo_paths = get_repo_paths(root, repos)
    for repo in repo_paths:
        branch = run_command(
            ["git", "branch", "--show-current"], cwd=repo,
        ).stdout.strip()
        logger.info(f"Pushing branch '{branch}' in {repo.name}")
        # Check if upstream exists
        upstream_check = run_command(
            ["git", "rev-parse", "--abbrev-ref", f"{branch}@{{upstream}}"], cwd=repo,
        )
        if upstream_check.returncode != 0:
            # No upstream, set it
            logger.info(f"Setting upstream for {branch} in {repo.name}")
            result = run_command(
                ["git", "push", "--set-upstream", "origin", branch], cwd=repo,
            )
        else:
            result = run_command(["git", "push"], cwd=repo)
        if result.returncode != 0:
            logger.error(f"Failed to push in {repo.name}: {result.stderr}")
        else:
            logger.info(f"Pushed in {repo.name}")


def tag_repos(
    root: Path, tag: str, push: bool = False, profile: Optional[str] = None,
) -> None:
    """Create git tag in repos."""
    config = load_config(root)
    repos = config["profiles"].get(profile or "all", [])
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


def prep(
    root: Path,
    targets: List[str],
    exclude: Optional[List[str]] = None,
    with_deps: bool = False,
    max_files: int = 200,
    output: str = "__multig_context.json",
) -> None:
    """Smart cfold for targets."""
    config = load_config(root)
    repos, explicit_files = resolve_targets(config, targets, root)
    logger.info(f"Resolved repos: {repos}, explicit files: {len(explicit_files)}")
    files = set(explicit_files)
    exclude_dirs = {".venv", "build", "__pycache__"}
    src_mode = "src" in targets
    for repo_name in repos:
        repo = root / repo_name
        if repo.exists():
            logger.info(f"Scanning {repo_name} for .py files")
            if src_mode:
                src_dir = repo / "src"
                if src_dir.exists():
                    for file in src_dir.rglob("*.py"):
                        if not any(part in file.parts for part in exclude_dirs):
                            files.add(file)
            else:
                for file in repo.rglob("*.py"):
                    if not any(part in file.parts for part in exclude_dirs):
                        files.add(file)
    # Apply user excludes
    if exclude:
        filtered = set()
        for file in files:
            if not any(fnmatch.fnmatch(str(file), excl) for excl in exclude):
                filtered.add(file)
        files = filtered
    logger.info(f"Selected {len(files)} files")
    if with_deps:
        import_map = config.get("import_map", {})
        deps = find_dependencies(files, import_map, root)
        logger.info(f"Adding dependencies: {deps}")
        for dep in deps:
            dep_repo = root / dep
            if dep_repo.exists():
                for file in dep_repo.rglob("*.py"):
                    if not any(part in file.parts for part in exclude_dirs):
                        files.add(file)
    if len(files) > max_files:
        logger.warning(f"Too many files ({len(files)}), limiting to {max_files}")
        files = set(list(files)[:max_files])
    output_path = root / output
    logger.info(f"Folding {len(files)} files to {output_path}")
    fold_files(list(files), output_path)
    logger.info(f"Folded {len(files)} files to {output_path}, copied to clipboard.")
    print(f"Selected {len(files)} files → {output_path}")
    print("Copied to clipboard ✔")
