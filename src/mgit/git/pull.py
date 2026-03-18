"""Pull / sync operations."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

from ..utils.repo_paths import get_repo_paths
from ..config import load_config
from ..utils.logger import logger
from ..utils.run_command import run_command
from ..utils.output import emit


def pull_repos(
    root: Path,
    rebase: bool = False,
    stash: bool = False,
    profile: Optional[str] = None,
    fmt: str = "rich",
) -> None:
    """Pull (and optionally rebase/stash) across repos in parallel."""
    config = load_config(root)
    repos = config.profiles.get(profile or "all", [])
    logger.info(f"Pulling in repos: {repos}  rebase={rebase}  stash={stash}")
    repo_paths = get_repo_paths(root, repos)

    results: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=max(1, len(repo_paths))) as executor:
        future_to_repo = {
            executor.submit(_pull_single_repo, repo, rebase, stash): repo
            for repo in repo_paths
        }
        for future in as_completed(future_to_repo):
            repo = future_to_repo[future]
            try:
                results[repo.name] = future.result()
            except Exception as exc:
                results[repo.name] = {"status": "error", "output": str(exc), "conflicts": []}

    if fmt != "rich":
        emit({"profile": profile or "all", "repos": results}, fmt)
        return

    ok = [r for r, v in results.items() if v["status"] == "ok"]
    err = [r for r, v in results.items() if v["status"] == "error"]
    conflicts = [r for r, v in results.items() if v.get("conflicts")]
    for repo_name, info in results.items():
        marker = "✓" if info["status"] == "ok" else "✗"
        print(f"{marker} {repo_name}: {info['output'][:120]}")
        if info.get("conflicts"):
            print(f"  CONFLICTS: {info['conflicts']}")
    print(f"\n{len(ok)} ok  {len(err)} errors  {len(conflicts)} with conflicts")


def _pull_single_repo(repo: Path, rebase: bool, stash: bool) -> dict:
    """Pull a single repo, optionally stashing first."""
    stash_created = False

    if stash:
        dirty = run_command(["git", "status", "--porcelain"], cwd=repo).stdout.strip()
        if dirty:
            s = run_command(["git", "stash"], cwd=repo)
            if s.returncode != 0:
                return {"status": "error", "output": f"stash failed: {s.stderr}", "conflicts": []}
            stash_created = True
            logger.info(f"Stashed in {repo.name}")

    cmd = ["git", "pull", "--rebase"] if rebase else ["git", "pull"]
    result = run_command(cmd, cwd=repo)

    conflicts: list[str] = []
    if result.returncode != 0:
        # Detect conflict markers
        conflict_check = run_command(["git", "diff", "--name-only", "--diff-filter=U"], cwd=repo)
        conflicts = [f.strip() for f in conflict_check.stdout.splitlines() if f.strip()]
        status = "error"
        output = (result.stdout + result.stderr).strip()
    else:
        status = "ok"
        output = (result.stdout + result.stderr).strip() or "already up to date"

    if stash_created and result.returncode == 0:
        pop = run_command(["git", "stash", "pop"], cwd=repo)
        if pop.returncode != 0:
            conflicts += ["stash pop conflict"]
            status = "error"
            output += f"\nstash pop failed: {pop.stderr}"

    return {"status": status, "output": output, "conflicts": conflicts}
