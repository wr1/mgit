"""Repo matching utilities."""

import fnmatch
from typing import List


def find_matching_repos(repos: List[str], pattern: str) -> List[str]:
    """Find repos matching a glob pattern."""
    return [r for r in repos if fnmatch.fnmatch(r, pattern)]
