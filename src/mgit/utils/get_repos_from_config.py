"""Config-based repo retrieval utilities."""
from typing import Dict, List

from ..config import Config


def get_repos_from_config(config: Config, target: str) -> List[str]:
    """Expand profiles and aliases to repo list."""
    repos = []
    if target in config.profiles:
        repos.extend(config.profiles[target])
    elif target in config.aliases:
        repos.extend(config.aliases[target])
    else:
        repos.append(target)
    return repos
