"""CLI interface for mgit using treeparse."""

from pathlib import Path

from treeparse import argument, cli, command, group, option

from .config import edit_config, init_config
from .core import (
    branch,
    commit_repos,
    foreach,
    push_repos,
    run_tests,
    status,
    sync_repos,
    tag_repos,
)
from .prep import prep


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

# Git group
git_group = group(
    name="git",
    help="Git operations across repos.",
    sort_key=1,
    commands=[
        command(
            name="status",
            help="Show repo status table.",
            sort_key=0,
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
            sort_key=1,
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
            sort_key=2,
            callback=lambda name, delete=False, sync=False, profile=None: branch(
                Path.cwd(), name, delete, sync, profile,
            ),
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
            name="commit",
            help="Auto-commit in repos.",
            sort_key=3,
            callback=lambda all=False,
            message="Auto commit new files",
            profile=None: commit_repos(Path.cwd(), all, message, profile),
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
            sort_key=4,
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
            name="tag",
            help="Create git tag in repos.",
            sort_key=5,
            callback=lambda tag, push=False, profile=None: tag_repos(
                Path.cwd(), tag, push, profile,
            ),
            arguments=[
                argument(name="tag", arg_type=str, help="Tag name."),
            ],
            options=[
                option(
                    flags=["--push", "-u"],
                    arg_type=bool,
                    help="Push tag to remote.",
                ),
                option(
                    flags=["--profile", "-p"],
                    arg_type=str,
                    help="Profile to use.",
                ),
            ],
        ),
    ],
)

# Test group
test_group = group(
    name="test",
    help="Testing and dependency operations.",
    sort_key=2,
    commands=[
        command(
            name="sync",
            help="Run uv sync --dev in repos.",
            sort_key=0,
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
            sort_key=1,
            callback=lambda glob=None, parallel=True, profile=None: run_tests(
                Path.cwd(), glob, parallel, profile,
            ),
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
    ],
)

# Fold group
fold_group = group(
    name="fold",
    help="Context folding operations.",
    sort_key=3,
    commands=[
        command(
            name="prep",
            help="Flexible context folding for multiple repos and files",
            sort_key=0,
            callback=lambda targets,
            exclude=None,
            with_deps=False,
            max_files=200,
            output="__multig_context.json": prep(
                Path.cwd(), targets, exclude, with_deps, max_files, output,
            ),
            arguments=[
                argument(
                    name="targets",
                    arg_type=str,
                    nargs="*",
                    help="Repos, profiles, globs, or exact files",
                ),
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

# Main commands
app = cli(
    name="mgit",
    help="CLI for managing multiple git repos.",
    subgroups=[config_group, git_group, test_group, fold_group],
    commands=[],
)
