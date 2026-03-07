"""Configuration handling for mgit."""

import os
from pathlib import Path
from typing import Any, Dict, List

import questionary
import yaml
from pydantic import BaseModel, Field

from ..utils.logger import logger


class TopicConfig(BaseModel):
    """Logical topic spanning multiple repos (e.g. "2d-meshing")."""

    targets: List[str]
    exclude: List[str] = Field(default_factory=list)
    with_deps: bool = True
    max_files: int = 250
    include_summary: bool = False


class Config(BaseModel):
    """Configuration model for mgit."""

    project_name: str
    profiles: Dict[str, list[str]]
    aliases: Dict[str, list[str]]
    import_map: Dict[str, str] = Field(default_factory=dict)
    topics: Dict[str, TopicConfig] = Field(default_factory=dict)


def load_config(root: Path) -> Config:
    """Load .mgitrc config."""
    config_path = root / ".mgitrc"
    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file {config_path} not found. Run 'mgit config init'.",
        )
    with open(config_path) as f:
        data = yaml.safe_load(f)
    try:
        return Config(**data)
    except ValidationError as e:
        logger.error(f"Invalid config: {e}")
        raise


def init_config(root: Path) -> None:
    """Interactive config init."""
    config_path = root / ".mgitrc"
    if config_path.exists():
        if not questionary.confirm("Config already exists. Overwrite?").ask():
            return
    repos = [d.name for d in root.iterdir() if d.is_dir() and (d / ".git").exists()]
    project_name = questionary.text("Project name:", default="my-project").ask()
    profiles = {}
    aliases = {}
    # Simple wizard - assume defaults for brevity
    config = Config(
        project_name=project_name,
        profiles={"all": repos},
        aliases={},
        import_map={},
        topics={},
    )
    with open(config_path, "w") as f:
        yaml.safe_dump(config.model_dump(), f)
    logger.info(f"Config created at {config_path}")


def edit_config(root: Path) -> None:
    """Open config in editor."""
    config_path = root / ".mgitrc"
    editor = os.environ.get("EDITOR", "gvim")
    os.system(f"{editor} {config_path}")
