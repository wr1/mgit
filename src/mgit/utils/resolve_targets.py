"""Target resolution utilities."""

from pathlib import Path
from typing import List, Set

import fnmatch


from ..config import Config


def resolve_targets(
    config: Config,
    targets: List[str],
    root: Path,
    exclude: List[str] = None,
) -> tuple[Set[str], Set[Path]]:
    """Resolve targets to repos and explicit files."""
    repos = set()
    explicit_files = set()
    all_repos = set(config.profiles.get("all", []))
    magic_words = {"src", "tests", "examples", "pyproject"}
    i = 0
    while i < len(targets):
        target = targets[i]
        if target in config.profiles:
            repos.update(config.profiles[target])
        elif target in config.aliases:
            repos.update(config.aliases[target])
        elif target in magic_words:
            # Collect following non-magic terms
            following = []
            j = i + 1
            while (
                j < len(targets)
                and targets[j] not in magic_words
                and targets[j] not in config.profiles
                and targets[j] not in config.aliases
            ):
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
    # Apply excludes
    if exclude:
        filtered = set()
        for file in explicit_files:
            if not any(fnmatch.fnmatch(str(file), excl) for excl in exclude):
                filtered.add(file)
        explicit_files = filtered
    return repos, explicit_files


def resolve_topic(
    config: Config, topic_name: str, root: Path
) -> tuple[Set[str], Set[Path], TopicConfig]:
    """Resolve a topic name → repos, files, and topic settings."""
    if topic_name not in config.topics:
        raise ValueError(f"Topic '{topic_name}' not found in .mgitrc")

    topic = config.topics[topic_name]
    # Reuse your existing resolver (it already handles repo:glob perfectly)
    selected_repos, explicit_files = resolve_targets(
        config, topic.targets, root, topic.exclude
    )
    return selected_repos, explicit_files, topic
