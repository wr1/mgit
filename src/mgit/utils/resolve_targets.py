"""Target resolution utilities."""
from pathlib import Path
from typing import Dict, List, Set

import fnmatch

from .get_repos_from_config import get_repos_from_config


def resolve_targets(
    config: Dict[str, any], targets: List[str], root: Path,
) -> tuple[Set[str], Set[Path]]:
    """Resolve targets to repos and explicit files."""
    repos = set()
    explicit_files = set()
    all_repos = set(config.get("profiles", {}).get("all", []))
    magic_words = {"src", "tests", "examples", "pyproject"}
    i = 0
    while i < len(targets):
        target = targets[i]
        if target in config.get("profiles", {}):
            repos.update(config["profiles"][target])
        elif target in config.get("aliases", {}):
            repos.update(config["aliases"][target])
        elif target in magic_words:
            # Collect following non-magic terms
            following = []
            j = i + 1
            while j < len(targets) and targets[j] not in magic_words and targets[j] not in config.get("profiles", {}) and targets[j] not in config.get("aliases", {}):
                following.append(targets[j])
                j += 1
            if following:
                # Apply magic to following repos
                for repo_name in following:
                    repo_path = root / repo_name
                    if repo_path.exists():
                        if target == "pyproject":
                            pyproject = repo_path / "pyproject.toml"
                            if pyproject.exists():
                                explicit_files.add(pyproject)
                        else:
                            target_dir = repo_path / target
                            if target_dir.exists():
                                explicit_files.update(target_dir.rglob("*.py"))
            else:
                # Apply to all repos
                for repo_name in all_repos:
                    repo_path = root / repo_name
                    if repo_path.exists():
                        if target == "pyproject":
                            pyproject = repo_path / "pyproject.toml"
                            if pyproject.exists():
                                explicit_files.add(pyproject)
                        else:
                            target_dir = repo_path / target
                            if target_dir.exists():
                                explicit_files.update(target_dir.rglob("*.py"))
            i = j - 1
        elif "*" in target:
            # Glob pattern
            for repo_name in all_repos:
                repo_path = root / repo_name
                if repo_path.exists():
                    explicit_files.update(repo_path.rglob(target))
        elif (root / target).exists():
            if (root / target).is_file():
                explicit_files.add((root / target).resolve())
            else:
                repos.add(target)
        else:
            repos.add(target)
        i += 1
    return repos, explicit_files
