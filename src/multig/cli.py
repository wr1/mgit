"""CLI interface for multig using treeparse."""

from pathlib import Path
from typing import List, Optional

from treeparse import cli, command, group, argument, option

from .config import init_config, edit_config

from .core import status, foreach, branch, sync_repos, test_repos, commit_repos, push_repos, prep

from . import logger


def main() -> None:
    """Main entry point."""
    app.run()

# Config group
config_group = group(
    name="config",
    help="Manage configuration.",
    sort_key=0,
    commands=[
        command(
            name="init",
            help="Initialize .multigrc interactively.",
            sort_key=0,
            callback=lambda: init_config(Path.cwd()),
        ),
        command(
            name="edit",
            help="Edit .multigrc in editor.",
            sort_key=1,
            callback=lambda: edit_config(Path.cwd()),
        ),
    ],
)

# Main commands
app = cli(
    name="multig",
    help="CLI for managing multiple git repos.",
    subgroups=[config_group],
    commands=[
        command(
            name="status",
            help="Show repo status table.",
            sort_key=1,
            callback=lambda profile=None: status(Path.cwd(), profile),
            options=[
                option(
                    flags=["--profile", "-p"],
                    arg_type=str,
                    help="Profile to use.",
                ),
            ],
        ),
        command(
            name="foreach",
            help="Run command in each repo.",
            sort_key=2,
            callback=lambda cmd, profile=None: foreach(Path.cwd(), cmd, profile),
            arguments=[
                argument(name="cmd", arg_type=str, help="Command to run."),
            ],
            options=[
                option(
                    flags=["--profile", "-p"],
                    arg_type=str,
                    help="Profile to use.",
                ),
            ],
        ),
        command(
            name="branch",
            help="Manage branches.",
            sort_key=3,
            callback=lambda name, delete=False, sync=False, profile=None: branch(Path.cwd(), name, delete, sync, profile),
            arguments=[
                argument(name="name", arg_type=str, help="Branch name."),
            ],
            options=[
                option(
                    flags=["--delete", "-d"],
                    arg_type=bool,
                    help="Delete branch.",
                ),
                option(
                    flags=["--sync", "-s"],
                    arg_type=bool,
                    help="Sync branch across repos.",
                ),
                option(
                    flags=["--profile", "-p"],
                    arg_type=str,
                    help="Profile to use.",
                ),
            ],
        ),
        command(
            name="sync",
            help="Run uv sync --dev in repos.",
            sort_key=4,
            callback=lambda profile=None: sync_repos(Path.cwd(), profile),
            options=[
                option(
                    flags=["--profile", "-p"],
                    arg_type=str,
                    help="Profile to use.",
                ),
            ],
        ),
        command(
            name="test",
            help="Run pytest in repos.",
            sort_key=5,
            callback=lambda glob=None, parallel=True, profile=None: test_repos(Path.cwd(), glob, parallel, profile),
            arguments=[
                argument(name="glob", arg_type=str, nargs="?", help="Glob pattern."),
            ],
            options=[
                option(
                    flags=["--parallel", "-P"],
                    arg_type=bool,
                    default=True,
                    help="Run in parallel.",
                ),
                option(
                    flags=["--profile", "-p"],
                    arg_type=str,
                    help="Profile to use.",
                ),
            ],
        ),
        command(
            name="commit",
            help="Auto-commit in repos.",
            sort_key=6,
            callback=lambda all=False, message="Auto commit new files", profile=None: commit_repos(Path.cwd(), all, message, profile),
            options=[
                option(
                    flags=["--all", "-a"],
                    arg_type=bool,
                    help="Stage all files.",
                ),
                option(
                    flags=["--message", "-m"],
                    arg_type=str,
                    default="Auto commit new files",
                    help="Commit message.",
                ),
                option(
                    flags=["--profile", "-p"],
                    arg_type=str,
                    help="Profile to use.",
                ),
            ],
        ),
        command(
            name="push",
            help="Push current branch to remote in repos.",
            sort_key=8,
            callback=lambda profile=None: push_repos(Path.cwd(), profile),
            options=[
                option(
                    flags=["--profile", "-p"],
                    arg_type=str,
                    help="Profile to use.",
                ),
            ],
        ),
        command(
            name="prep",
            help="Flexible context folding for multiple repos and files",
            sort_key=7,
            callback=lambda targets, exclude=None, with_deps=False, max_files=200, output="__multig_context.json": prep(Path.cwd(), targets, exclude, with_deps, max_files, output),
            arguments=[
                argument(name="targets", arg_type=str, nargs="*", help="Repos, profiles, globs, or exact files"),
            ],
            options=[
                option(
                    flags=["--exclude", "-x"],
                    arg_type=str,
                    multiple=True,
                    help="Patterns to exclude",
                ),
                option(
                    flags=["--with-deps", "-d"],
                    arg_type=bool,
                    help="Follow Python imports to add dependencies",
                ),
                option(
                    flags=["--max-files"],
                    arg_type=int,
                    default=200,
                    help="Safety limit",
                ),
                option(
                    flags=["--output", "-o"],
                    arg_type=str,
                    default="__multig_context.json",
                    help="Output file",
                ),
            ],
        ),
    ],
)