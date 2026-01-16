"""Context folding operations for mgit."""
from pathlib import Path
from typing import List, Optional, Set

import fnmatch

from ..config import load_config
from ..utils.find_dependencies import find_dependencies
from ..utils.fold_files import fold_files
from ..utils.logger import logger
from ..utils.resolve_targets import resolve_targets
from ..utils.run_command import run_command


def prep(
    root: Path,
    targets: List[str],
    exclude: Optional[List[str]] = None,
    with_deps: bool = False,
    max_files: int = 200,
    output: str = "__mgit_context.json",
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
        import_map = config.import_map if hasattr(config, 'import_map') else {}
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
    # Generate summary using cfold sum
    summary_path = root / "__mgit_summary.txt"
    repo_paths = [root / r for r in repos]
    if repo_paths:
        logger.info(f"Running cfold sum on repos: {[str(p) for p in repo_paths]}")
        cmd = ["cfold", "sum"] + [str(p) for p in repo_paths] + ["--output", str(summary_path)]
        result = run_command(cmd, cwd=root)
        if result.returncode != 0:
            logger.warning(f"cfold sum failed: {result.stderr}")
            summary_path = None
        else:
            logger.info(f"Generated summary at {summary_path}")
    else:
        summary_path = None
    # Include summary in files if generated
    final_files = list(files)
    if summary_path and summary_path.exists():
        final_files.append(summary_path)
    output_path = root / output
    logger.info(f"Folding {len(final_files)} files to {output_path}")
    fold_files(final_files, output_path)
    logger.info(f"Folded {len(final_files)} files to {output_path}, copied to clipboard.")
    print(f"Selected {len(final_files)} files → {output_path}")
    print("Copied to clipboard ✔")
