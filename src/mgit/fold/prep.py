"""Prep operations for mgit."""

from pathlib import Path
from typing import List, Optional

import fnmatch

from ..config import load_config
from ..fold.summarize import summary
from ..utils.find_dependencies import find_dependencies
from ..utils.fold_files import fold_files
from ..utils.logger import logger
from ..utils.resolve_targets import resolve_targets, resolve_topic
from ..utils.run_command import run_command


def prep(
    root: Path,
    targets: List[str],
    exclude: Optional[List[str]] = None,
    with_deps: bool = True,
    max_files: int = 200,
    output: str = "context.json",
    sum: Optional[str] = None,
    no_summary: bool = False,
) -> None:
    """Smart cfold for targets."""
    config = load_config(root)

    # === NEW: Topic detection ===
    topic = None
    topic_name = None
    if targets and targets[0] in config.topics:
        topic_name = targets[0]
        selected_repos, explicit_files, topic = resolve_topic(config, topic_name, root)
        use_with_deps = topic.with_deps
        use_max_files = topic.max_files
        # Override default output for topics
        if output == "context.json":
            output = f"{topic_name}.json"
        print(f"Using topic '{topic_name}' → {len(selected_repos)} repos")
    else:
        selected_repos, explicit_files = resolve_targets(config, targets, root, exclude)
        use_with_deps = with_deps
        use_max_files = max_files

    # === Rest of your existing logic (get_repo_paths, find_dependencies, etc.) ===
    from ..utils.repo_paths import get_repo_paths

    repo_paths = get_repo_paths(root, list(selected_repos))
    files = set(explicit_files)
    exclude_dirs = {".venv", "build", "__pycache__"}
    src_mode = "src" in targets
    for repo in repo_paths:
        if repo.exists():
            logger.info(f"Scanning {repo.name} for .py files")
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
    # Apply topic excludes
    if topic:
        filtered = set()
        for file in files:
            if not any(fnmatch.fnmatch(str(file), excl) for excl in topic.exclude):
                filtered.add(file)
        files = filtered
    # Apply user excludes if not topic
    if exclude and not topic:
        filtered = set()
        for file in files:
            if not any(fnmatch.fnmatch(str(file), excl) for excl in exclude):
                filtered.add(file)
        files = filtered
    logger.info(f"Selected {len(files)} files")
    if use_with_deps:
        import_map = config.import_map
        deps = find_dependencies(files, import_map, root)
        logger.info(f"Adding dependencies: {deps}")
        for dep in deps:
            dep_repo = root / dep
            if dep_repo.exists():
                for file in dep_repo.rglob("*.py"):
                    if not any(part in file.parts for part in exclude_dirs):
                        files.add(file)
    if len(files) > use_max_files:
        logger.warning(f"Too many files ({len(files)}), limiting to {use_max_files}")
        files = set(list(files)[:use_max_files])
    # Generate summary if requested
    summary_path = None
    if sum:
        sum_repos = config.profiles.get(sum, [])
        if sum_repos:
            summary_path = root / f"summary_{sum}.txt"
            logger.info(f"Generating summary for profile '{sum}' to {summary_path}")
            cmd = (
                ["cfold", "sum"]
                + [str(root / r) for r in sum_repos]
                + ["--output", str(summary_path)]
            )
            result = run_command(cmd, cwd=root)
            if result.returncode != 0:
                logger.warning(f"cfold sum failed for profile {sum}: {result.stderr}")
                summary_path = None
            else:
                logger.info(f"Generated summary at {summary_path}")
        else:
            logger.warning(f"Profile '{sum}' not found or empty")
    # Include summary in files if generated or topic includes
    final_files = list(files)
    if summary_path and summary_path.exists():
        final_files.insert(0, summary_path)
    elif topic and topic.include_summary and not no_summary:
        summary_output = root / "summary.txt"
        summary(root, [r.name for r in repo_paths], str(summary_output))
        if summary_output.exists():
            final_files.insert(0, summary_output)
    output_path = root / output
    logger.info(f"Folding {len(final_files)} files to {output_path}")
    logger.info(f"Files included: {', '.join(str(f) for f in final_files)}")
    fold_files(final_files, output_path)
    print(f"✓ Folded {len(final_files)} items (incl. summary) → {output}")
    print("Copied to clipboard ✓")
