"""Config-based repo retrieval utilities."""
from typing import Dict, List


def get_repos_from_config(config: Dict[str, any], target: str) -> List[str]:
    """Expand profiles and aliases to repo list."""
    repos = []
    if target in config.get("profiles", {}):
        repos.extend(config["profiles"][target])
    elif target in config.get("aliases", {}):
        repos.extend(config["aliases"][target])
    else:
        repos.append(target)
    return repos
