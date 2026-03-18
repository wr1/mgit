"""Configuration handling for mgit."""

import os
from pathlib import Path
from typing import Dict, List

import questionary
import yaml
from pydantic import BaseModel, Field, ValidationError

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
    master_repo: str = Field(
        default="b3m",
        description="Master toolbox repo that controls the canonical version",
    )


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
    # Simple wizard - assume defaults for brevity
    config = Config(
        project_name=project_name,
        profiles={"all": repos},
        aliases={},
        import_map={},
        topics={},
        master_repo="b3m",
    )
    with open(config_path, "w") as f:
        yaml.safe_dump(config.model_dump(), f)
    logger.info(f"Config created at {config_path}")


def edit_config(root: Path) -> None:
    """Open config in editor."""
    config_path = root / ".mgitrc"
    editor = os.environ.get("EDITOR", "gvim")
    os.system(f"{editor} {config_path}")


def print_example_config() -> None:
    """Print annotated example .mgitrc for LLM demo."""
    example = """# This is a DEMO .mgitrc file for the mgit tool.
# It uses dummy repo names and settings to illustrate configuration.
# Copy and adapt this for your real project.
# Run 'mgit config help' to see this output.

project_name: my-demo-project  # Name of your project

profiles:
  all:  # Default profile with all repos
    - dummy-repo1
    - dummy-repo2
    - dummy-repo3
  dev:  # Profile for development repos
    - dummy-repo1
    - dummy-repo2
  prod:  # Profile for production repos
    - dummy-repo3

aliases:
  frontend: [dummy-repo1]  # Alias for frontend-related repos
  backend: [dummy-repo2, dummy-repo3]  # Alias for backend repos

# Optional: Map imports to repos for dependency folding
import_map:
  dummy_lib: dummy-repo1  # If dummy-repo1 provides dummy_lib

# Optional: Define topics for smart folding
topics:
  demo-topic:  # A topic example with explicit repo names
    targets: [dummy-repo1, dummy-repo2]
    exclude: ["*.log"]  # Exclude log files
    with_deps: true  # Follow Python imports
    max_files: 100  # Limit files
    include_summary: false  # Don't include summary by default
  dev-topic:  # Topic using a profile name as target
    targets: ["dev"]  # Refers to the 'dev' profile above
    exclude: ["__pycache__/**"]
    with_deps: true
    max_files: 200
  python-files:  # Topic using a glob pattern as target
    targets: ["**/*.py"]  # Glob for all Python files across repos
    exclude: ["tests/**", "*.pyc"]
    with_deps: false  # No dependency following for globs
    max_files: 500

# NEW: Master repo that owns the canonical version (used by `mgit version bump`)
master_repo: b3m
"""
    print(example)
