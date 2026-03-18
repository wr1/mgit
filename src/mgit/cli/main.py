"""Main CLI entry point."""

from pathlib import Path

from treeparse import argument, cli, command, group, option

from ..config import edit_config, init_config, print_example_config
from ..git.branch import branch
from ..git.commit import commit_repos
from ..git.foreach import foreach
from ..git.pull import pull_repos
from ..git.push import push_repos
from ..git.status import status
from ..git.tag import tag_repos
from ..fold.prep import prep
from ..fold.summarize import summary
from ..ruff.ruff import ruff_fix, ruff_format
from ..uv.sync import sync_repos
from ..test.test import run_tests
from ..version.bump import bump_version
from ..search.search import search_repos
from ..apply.apply import apply_patch


def main() -> None:
    """Main entry point."""
    app.run()


# ── Shared fmt option ──────────────────────────────────────────────────────────
_fmt_option = option(
    flags=["--fmt", "-F"],
    arg_type=str,
    default="rich",
    help="Output format: rich | json | llm | markdown",
)

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
        command(
            name="help",
            help="Show annotated example .mgitrc for LLM.",
            sort_key=2,
            callback=lambda: print_example_config(),
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
            callback=lambda profile=None, fmt="rich": status(Path.cwd(), profile, fmt),
            options=[
                option(flags=["--profile", "-p"], arg_type=str, help="Profile to use."),
                _fmt_option,
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
                option(flags=["--profile", "-p"], arg_type=str, help="Profile to use."),
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
                option(flags=["--delete", "-d"], arg_type=bool, help="Delete branch."),
                option(
                    flags=["--sync", "-s"],
                    arg_type=bool,
                    help="Sync branch across repos.",
                ),
                option(flags=["--profile", "-p"], arg_type=str, help="Profile to use."),
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
                option(flags=["--all", "-a"], arg_type=bool, help="Stage all files."),
                option(
                    flags=["--message", "-m"],
                    arg_type=str,
                    default="Auto commit new files",
                    help="Commit message.",
                ),
                option(flags=["--profile", "-p"], arg_type=str, help="Profile to use."),
            ],
        ),
        command(
            name="push",
            help="Push current branch to remote in repos.",
            sort_key=4,
            callback=lambda profile=None, fmt="rich": push_repos(
                Path.cwd(), profile, fmt
            ),
            options=[
                option(flags=["--profile", "-p"], arg_type=str, help="Profile to use."),
                _fmt_option,
            ],
        ),
        command(
            name="pull",
            help="Pull (and optionally rebase/stash) across repos.",
            sort_key=5,
            callback=lambda rebase=False, stash=False, profile=None, fmt="rich": (
                pull_repos(
                    Path.cwd(),
                    rebase,
                    stash,
                    profile,
                    fmt,
                )
            ),
            options=[
                option(
                    flags=["--rebase", "-r"],
                    arg_type=bool,
                    help="Use --rebase instead of merge.",
                ),
                option(
                    flags=["--stash", "-S"],
                    arg_type=bool,
                    help="Auto-stash before pull, pop after.",
                ),
                option(flags=["--profile", "-p"], arg_type=str, help="Profile to use."),
                _fmt_option,
            ],
        ),
        command(
            name="tag",
            help="Create git tag in repos.",
            sort_key=6,
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
                    flags=["--push", "-u"], arg_type=bool, help="Push tag to remote."
                ),
                option(flags=["--profile", "-p"], arg_type=str, help="Profile to use."),
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
                option(flags=["--profile", "-p"], arg_type=str, help="Profile to use."),
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
                option(flags=["--profile", "-p"], arg_type=str, help="Profile to use."),
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
            callback=lambda profile=None, fmt="rich": ruff_format(
                Path.cwd(), profile, fmt
            ),
            options=[
                option(flags=["--profile", "-p"], arg_type=str, help="Profile to use."),
                _fmt_option,
            ],
        ),
        command(
            name="fix",
            help="Run ruff check --fix --unsafe-fixes in repos.",
            sort_key=1,
            callback=lambda profile=None, fmt="rich": ruff_fix(
                Path.cwd(), profile, fmt
            ),
            options=[
                option(flags=["--profile", "-p"], arg_type=str, help="Profile to use."),
                _fmt_option,
            ],
        ),
    ],
)

# Version group
version_group = group(
    name="version",
    help="Version bumping synced across all toolbox repos (master-driven).",
    sort_key=6,
    commands=[
        command(
            name="bump",
            help="Bump version in master (uv) + sync to every repo",
            sort_key=0,
            callback=lambda level="patch", profile=None, dry_run=False, commit=False, tag=False: (
                bump_version(Path.cwd(), level, profile, dry_run, commit, tag)
            ),
            arguments=[
                argument(
                    name="level",
                    arg_type=str,
                    default="patch",
                    help="patch | minor | major",
                ),
            ],
            options=[
                option(
                    flags=["--profile", "-p"],
                    arg_type=str,
                    help="Profile to sync (default: all)",
                ),
                option(
                    flags=["--dry-run", "-n"],
                    arg_type=bool,
                    help="Show what would happen",
                ),
                option(
                    flags=["--commit", "-c"],
                    arg_type=bool,
                    help="Auto-commit pyproject.toml changes",
                ),
                option(
                    flags=["--tag", "-t"],
                    arg_type=bool,
                    help="Create git tag (master only)",
                ),
            ],
        ),
    ],
)

# Search group
search_group = group(
    name="search",
    help="Cross-repo grep and symbol search.",
    sort_key=7,
    commands=[
        command(
            name="grep",
            help="Search for a pattern across repos (git grep).",
            sort_key=0,
            callback=lambda pattern, profile=None, repos=None, type=None, ignore_case=False, with_deps=False, fmt="rich": (
                search_repos(
                    Path.cwd(),
                    pattern,
                    profile,
                    list(repos) if repos else None,
                    type,
                    ignore_case,
                    with_deps,
                    fmt,
                )
            ),
            arguments=[
                argument(
                    name="pattern",
                    arg_type=str,
                    help="Regex/string pattern to search for.",
                ),
            ],
            options=[
                option(flags=["--profile", "-p"], arg_type=str, help="Profile to use."),
                option(
                    flags=["--repos", "-r"],
                    arg_type=str,
                    multiple=True,
                    help="Explicit repo list.",
                ),
                option(
                    flags=["--type", "-t"],
                    arg_type=str,
                    help="File extension to filter (e.g. py, ts).",
                ),
                option(
                    flags=["--ignore-case", "-i"],
                    arg_type=bool,
                    help="Case-insensitive search.",
                ),
                option(
                    flags=["--with-deps", "-d"],
                    arg_type=bool,
                    help="Include dependent repos.",
                ),
                _fmt_option,
            ],
        ),
    ],
)

# Apply group
apply_group = group(
    name="apply",
    help="Apply structured JSON patches across repos.",
    sort_key=8,
    commands=[
        command(
            name="patch",
            help="Apply a JSON patch file across repos.",
            sort_key=0,
            callback=lambda patch_file, dry_run=False, commit=False, message="mgit apply patch", fmt="rich": (
                apply_patch(
                    Path.cwd(),
                    patch_file,
                    dry_run,
                    commit,
                    message,
                    fmt,
                )
            ),
            arguments=[
                argument(
                    name="patch_file", arg_type=str, help="Path to JSON patch file."
                ),
            ],
            options=[
                option(
                    flags=["--dry-run", "-n"],
                    arg_type=bool,
                    help="Preview changes without writing files.",
                ),
                option(
                    flags=["--commit", "-c"],
                    arg_type=bool,
                    help="Auto-commit applied changes.",
                ),
                option(
                    flags=["--message", "-m"],
                    arg_type=str,
                    default="mgit apply patch",
                    help="Commit message.",
                ),
                _fmt_option,
            ],
        ),
    ],
)

# Main app
app = cli(
    name="mgit",
    help="CLI for managing multiple git repos.",
    subgroups=[
        config_group,
        git_group,
        uv_group,
        test_group,
        fold_group,
        ruff_group,
        version_group,
        search_group,
        apply_group,
    ],
    commands=[],
    show_types=True,
    show_defaults=True,
)
