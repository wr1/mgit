"""Utility functions for mgit."""

import ast
import fnmatch
import logging
import subprocess
from pathlib import Path
from typing import List, Optional, Set

import pyperclip
import rich.logging

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[rich.logging.RichHandler()],
)
logger = logging.getLogger(__name__)


def run_command(
    cmd: List[str], cwd: Optional[Path] = None,
) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    return subprocess.run(cmd, check=False, cwd=cwd, capture_output=True, text=True)


def get_repos_from_config(config: dict, target: str) -> List[str]:
    """Expand profiles and aliases to repo list."""
    repos = []
    if target in config.get("profiles", {}):
        repos.extend(config["profiles"][target])
    elif target in config.get("aliases", {}):
        repos.extend(config["aliases"][target])
    else:
        repos.append(target)
    return repos


def find_matching_repos(repos: List[str], pattern: str) -> List[str]:
    """Find repos matching a glob pattern."""

    return [r for r in repos if fnmatch.fnmatch(r, pattern)]


def fold_files(files: List[Path], output: Path) -> None:
    """Fold files using cfold or cat."""
    try:
        from cfold.cli.fold import fold

        fold(
            files=[str(f) for f in files],
            output=str(output),
            prompt=None,
            dialect="default",
            bare=False,
        )
    except ImportError:
        # Fallback to cat
        with open(output, "w") as f:
            for file in files:
                f.write(f"# {file}\n")
                f.write(file.read_text())
                f.write("\n")
    pyperclip.copy(output.read_text())


def get_git_repos(root: Path) -> List[Path]:
    """Find all git repos in subdirs."""
    return [d for d in root.iterdir() if d.is_dir() and (d / ".git").exists()]


def extract_imports(file: Path) -> Set[str]:
    """Extract import names from a Python file."""
    imports = set()
    try:
        with open(file, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split(".")[0])
    except Exception:
        pass
    return imports


def resolve_targets(
    config: dict, targets: List[str], root: Path,
) -> tuple[Set[str], Set[Path]]:
    """Resolve targets to repos and explicit files."""
    repos = set()
    explicit_files = set()
    all_repos = set(config.get("profiles", {}).get("all", []))
    magic_words = {"src", "tests", "examples", "pyproject"}
    for target in targets:
        if target in config.get("profiles", {}):
            repos.update(config["profiles"][target])
        elif target in config.get("aliases", {}):
            repos.update(config["aliases"][target])
        elif target in magic_words:
            # Magic: add specific dirs/files from all repos
            for repo_name in all_repos:
                repo_path = root / repo_name
                if repo_path.exists():
                    if target == "pyproject":
                        pyproject = repo_path / "pyproject.toml"
                        if pyproject.exists():
                            explicit_files.add(pyproject)
                    else:
                        # Add all .py in target dir
                        target_dir = repo_path / target
                        if target_dir.exists():
                            explicit_files.update(target_dir.rglob("*.py"))
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
    return repos, explicit_files


def find_dependencies(files: Set[Path], import_map: dict, root: Path) -> Set[str]:
    """Find additional repos based on imports."""
    deps = set()
    for file in files:
        imports = extract_imports(file)
        for imp in imports:
            if imp in import_map:
                deps.add(import_map[imp])
    return deps
