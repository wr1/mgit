"""Main CLI entry point."""

from pathlib import Path

from treeparse import argument, cli, command, group, option

from ..config import edit_config, init_config
from ..git.branch import branch
from ..git.commit import commit_repos
from ..git.foreach import foreach
from ..git.push import push_repos
from ..git.status import status
from ..git.tag import tag_repos
from ..fold.prep import prep
from ..fold.summarize import summary
from ..ruff.ruff import ruff_check_fix, ruff_format
from ..uv.sync import sync_repos
from ..test.test import run_tests


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
            help="Initialize .mgitrc interactively.",
            sort_key=0,
            callback=lambda: init_config(Path.cwd()),
        ),
        command(
            name="edit",
            help="Edit .mgitrc in editor.",
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
                Path.cwd(),
                name,
                delete,
                sync,
                profile,
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
            callback=lambda all=False, message="Auto commit new files", profile=None: (
                commit_repos(Path.cwd(), all, message, profile)
            ),
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
                Path.cwd(),
                tag,
                push,
                profile,
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

# Uv group
uv_group = group(
    name="uv",
    help="Uv operations across repos.",
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
    ],
)

# Test group
test_group = group(
    name="test",
    help="Testing operations.",
    sort_key=3,
    commands=[
        command(
            name="test",
            help="Run pytest in repos.",
            sort_key=0,
            callback=lambda glob=None, parallel=True, profile=None: run_tests(
                Path.cwd(),
                glob,
                parallel,
                profile,
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
    sort_key=4,
    commands=[
        command(
            name="prep",
            help="Flexible context folding for multiple repos and files",
            sort_key=0,
            callback=lambda targets, exclude=None, with_deps=False, max_files=200, output="context.json", sum=None, no_summary=False: (
                prep(
                    Path.cwd(),
                    targets,
                    exclude,
                    with_deps,
                    max_files,
                    output,
                    sum,
                    no_summary,
                )
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
                    flags=["--max-files", "-M"],
                    arg_type=int,
                    default=200,
                    help="Safety limit",
                ),
                option(
                    flags=["--output", "-o"],
                    arg_type=str,
                    default="context.json",
                    help="Output file",
                ),
                option(
                    flags=["--sum"],
                    arg_type=str,
                    help="Profile to summarize and include in fold",
                ),
                option(
                    flags=["--no-summary"],
                    arg_type=bool,
                    help="Do not include summary even if topic specifies it",
                ),
            ],
        ),
        command(
            name="sum",
            help="Generate code summary for repos (defaults to 'all' profile)",
            sort_key=1,
            callback=lambda repos=None, output="summary.txt": summary(
                Path.cwd(), repos or [], output
            ),
            options=[
                option(
                    flags=["--repos", "-r"],
                    arg_type=str,
                    multiple=True,
                    help="Repos to summarize (overrides default profile)",
                ),
                option(
                    flags=["--output", "-o"],
                    arg_type=str,
                    default="summary.txt",
                    help="Output file",
                ),
            ],
        ),
    ],
)

# Ruff group
ruff_group = group(
    name="ruff",
    help="Ruff formatting and checking operations.",
    sort_key=5,
    commands=[
        command(
            name="format",
            help="Run ruff format in repos.",
            sort_key=0,
            callback=lambda profile=None: ruff_format(Path.cwd(), profile),
            options=[
                option(
                    flags=["--profile", "-p"],
                    arg_type=str,
                    help="Profile to use.",
                ),
            ],
        ),
        command(
            name="check",
            help="Run ruff check --fix --unsafe-fixes in repos.",
            sort_key=1,
            callback=lambda profile=None: ruff_check_fix(Path.cwd(), profile),
            options=[
                option(
                    flags=["--profile", "-p"],
                    arg_type=str,
                    help="Profile to use.",
                ),
            ],
        ),
    ],
)

# Main commands
app = cli(
    name="mgit",
    help="CLI for managing multiple git repos.",
    subgroups=[config_group, git_group, uv_group, test_group, fold_group, ruff_group],
    commands=[],
    theme="red_white_blue",
)
