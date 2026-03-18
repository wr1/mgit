"""Summarize operations for mgit."""

from pathlib import Path
from typing import List

from ..config import load_config
from ..utils.logger import logger
from ..utils.run_command import run_command


def summary(root: Path, repos: List[str], output: str = "summary.txt") -> None:
    """Generate code summary for repos using cfold sum."""
    config = load_config(root)
    if not repos:
        repos = config.profiles.get("all", [])
    elif len(repos) == 1 and repos[0] in config.profiles:
        repos = config.profiles[repos[0]]
    # Else, repos is list of repo names
    if not repos:
        logger.error("No repos specified or in 'all' profile")
        return
    output_path = root / output
    logger.info(f"Generating summary for repos: {repos} to {output_path}")
    cmd = (
        ["cfold", "summarize", "--clip", "False"]
        + [str(root / r) for r in repos]
        + ["--output", str(output_path)]
    )
    logger.info(f"Running command: {' '.join(cmd)}")
    result = run_command(cmd, cwd=root)
    if result.returncode != 0 or not output_path.exists():
        logger.error(f"Failed to generate summary: {result.stderr}")
        if result.stdout:
            logger.error(f"Stdout: {result.stdout}")
    else:
        logger.info(f"Summary generated at {output_path}")
        print(f"Summary created: {output_path}")
