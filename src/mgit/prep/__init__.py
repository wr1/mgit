"""Context folding operations for mgit."""
from pathlib import Path
from typing import List, Optional, Set

import fnmatch

from ..config import load_config
from ..utils.find_dependencies import find_dependencies
from ..utils.fold_files import fold_files
from ..utils.logger import logger
from ..utils.resolve_targets import resolve_targets


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
                    for file in repo.rglob("*.py"):
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
