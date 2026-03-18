"""Cross-repo grep + symbol search."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

from ..utils.repo_paths import get_repo_paths
from ..config import load_config
from ..utils.logger import logger
from ..utils.run_command import run_command
from ..utils.output import emit


def search_repos(
    root: Path,
    pattern: str,
    profile: Optional[str] = None,
    repos_filter: Optional[list[str]] = None,
    file_type: Optional[str] = None,
    case_insensitive: bool = False,
    with_deps: bool = False,
    fmt: str = "rich",
) -> None:
    """Search for a pattern across multiple repos using git grep."""
    config = load_config(root)

    if repos_filter:
        repos = repos_filter
    else:
        repos = config.profiles.get(profile or "all", [])

    logger.info(f"Searching '{pattern}' in repos: {repos}")
    repo_paths = get_repo_paths(root, repos)

    results: dict[str, list[dict]] = {}
    with ThreadPoolExecutor(max_workers=max(1, len(repo_paths))) as executor:
        future_to_repo = {
            executor.submit(_search_single_repo, repo, pattern, file_type, case_insensitive): repo
            for repo in repo_paths
        }
        for future in as_completed(future_to_repo):
            repo = future_to_repo[future]
            try:
                results[repo.name] = future.result()
            except Exception as exc:
                logger.error(f"Search failed in {repo.name}: {exc}")
                results[repo.name] = []

    total_matches = sum(len(v) for v in results.values())

    if fmt != "rich":
        emit(
            {
                "pattern": pattern,
                "profile": profile or "all",
                "total_matches": total_matches,
                "repos": results,
            },
            fmt,
        )
        return

    # Rich output
    for repo_name, matches in sorted(results.items()):
        if not matches:
            continue
        print(f"\n[{repo_name}] — {len(matches)} match(es)")
        for m in matches:
            print(f"  {m['file']}:{m['line']}: {m['text']}")
    print(f"\nTotal: {total_matches} match(es) across {len([r for r in results if results[r]])} repo(s)")


def _search_single_repo(
    repo: Path,
    pattern: str,
    file_type: Optional[str],
    case_insensitive: bool,
) -> list[dict]:
    """Run git grep in a single repo and return structured results."""
    cmd = ["git", "grep", "-n", "--no-color"]
    if case_insensitive:
        cmd.append("-i")
    cmd.append(pattern)
    if file_type:
        # e.g. --type py → search *.py files
        cmd += ["--", f"*.{file_type.lstrip('.')}"]

    result = run_command(cmd, cwd=repo)
    matches: list[dict] = []
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            # git grep -n output: file:lineno:text
            parts = line.split(":", 2)
            if len(parts) >= 3:
                matches.append({"file": parts[0], "line": int(parts[1]), "text": parts[2].strip()})
            elif len(parts) == 2:
                matches.append({"file": parts[0], "line": 0, "text": parts[1].strip()})
    return matches
