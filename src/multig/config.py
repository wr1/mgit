"""Configuration handling for multig."""

import os
from pathlib import Path
from typing import Dict, Any

import yaml

import questionary

from . import logger


def load_config(root: Path) -> Dict[str, Any]:
    """Load .multigrc config."""
    config_path = root / ".multigrc"
    if not config_path.exists():
        raise FileNotFoundError(f"Config file {config_path} not found. Run 'multig config init'.")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def init_config(root: Path) -> None:
    """Interactive config init."""
    config_path = root / ".multigrc"
    if config_path.exists():
        if not questionary.confirm("Config already exists. Overwrite?").ask():
            return
    repos = [d.name for d in root.iterdir() if d.is_dir() and (d / ".git").exists()]
    project_name = questionary.text("Project name:", default="my-project").ask()
    profiles = {}
    aliases = {}
    # Simple wizard - assume defaults for brevity
    config = {
        "project_name": project_name,
        "profiles": {"all": repos},
        "aliases": {},
    }
    with open(config_path, "w") as f:
        yaml.safe_dump(config, f)
    logger.info(f"Config created at {config_path}")


def edit_config(root: Path) -> None:
    """Open config in editor."""
    config_path = root / ".multigrc"
    editor = os.environ.get("EDITOR", "gvim")
    os.system(f"{editor} {config_path}")