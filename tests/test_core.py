"""Test for core functions."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from mgit.core import (
    branch,
    commit_repos,
    foreach,
    prep,
    push_repos,
    run_tests,
    status,
    sync_repos,
    tag_repos,
)


def test_prep():
    """Test that prep calls fold_files without NameError."""
    root = Path("/tmp")
    target = "test"
    with patch("mgit.core.load_config") as mock_load, patch(
        "mgit.core.get_repos_from_config",
    ) as mock_get, patch("mgit.core.get_repo_paths") as mock_paths, patch(
        "mgit.core.fold_files",
    ) as mock_fold:
        mock_load.return_value = {"profiles": {"all": ["repo1"]}}
        mock_get.return_value = ["repo1"]
        mock_paths.return_value = [Path("/tmp/repo1")]
        # Should not raise NameError
        prep(root, target)
        mock_fold.assert_called_once()


def test_prep_with_src():
    """Test prep with src in targets."""
    root = Path("/tmp")
    targets = ["src", "repo1"]
    with patch("mgit.core.load_config") as mock_load, patch(
        "mgit.core.resolve_targets",
    ) as mock_resolve, patch("mgit.core.fold_files") as mock_fold:
        mock_load.return_value = {"profiles": {"all": ["repo1"]}}
        mock_resolve.return_value = ({"repo1"}, set())
        prep(root, targets)
        mock_fold.assert_called_once()
        # Since src in targets, src_mode should be True, but since mocked, can't check scanning


def test_branch_create():
    """Test creating a new branch across repos."""
    root = Path("/tmp")
    name = "feature/new"
    with patch("mgit.core.load_config") as mock_load, patch(
        "mgit.core.get_repo_paths",
    ) as mock_paths, patch("mgit.core.run_command") as mock_run:
        mock_load.return_value = {"profiles": {"all": ["repo1", "repo2"]}}
        mock_paths.return_value = [Path("/tmp/repo1"), Path("/tmp/repo2")]
        mock_run.return_value = MagicMock(returncode=0)
        branch(root, name, delete=False, sync=False, profile=None)
        # Should call checkout -b for each repo
        assert mock_run.call_count == 2
        mock_run.assert_any_call(
            ["git", "checkout", "-b", name], cwd=Path("/tmp/repo1"),
        )
        mock_run.assert_any_call(
            ["git", "checkout", "-b", name], cwd=Path("/tmp/repo2"),
        )


def test_branch_delete():
    """Test deleting a branch across repos."""
    root = Path("/tmp")
    name = "feature/old"
    with patch("mgit.core.load_config") as mock_load, patch(
        "mgit.core.get_repo_paths",
    ) as mock_paths, patch("mgit.core.run_command") as mock_run:
        mock_load.return_value = {"profiles": {"all": ["repo1"]}}
        mock_paths.return_value = [Path("/tmp/repo1")]
        mock_run.return_value = MagicMock(returncode=0)
        branch(root, name, delete=True, sync=False, profile=None)
        mock_run.assert_called_once_with(
            ["git", "branch", "-D", name], cwd=Path("/tmp/repo1"),
        )


def test_branch_sync():
    """Test syncing branch across repos."""
    root = Path("/tmp")
    name = "main"
    with patch("mgit.core.load_config") as mock_load, patch(
        "mgit.core.get_repo_paths",
    ) as mock_paths, patch("mgit.core.run_command") as mock_run:
        mock_load.return_value = {"profiles": {"all": ["repo1", "repo2"]}}
        mock_paths.return_value = [Path("/tmp/repo1"), Path("/tmp/repo2")]
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="main\n"),  # get current from first repo
            MagicMock(returncode=0),  # checkout in repo1
            MagicMock(returncode=0),  # checkout in repo2
        ]
        branch(root, name, delete=False, sync=True, profile=None)
        assert mock_run.call_count == 3
        mock_run.assert_any_call(
            ["git", "branch", "--show-current"], cwd=Path("/tmp/repo1"),
        )
        mock_run.assert_any_call(["git", "checkout", "main"], cwd=Path("/tmp/repo1"))
        mock_run.assert_any_call(["git", "checkout", "main"], cwd=Path("/tmp/repo2"))


def test_push_repos():
    """Test pushing repos."""
    root = Path("/tmp")
    with patch("mgit.core.load_config") as mock_load, patch(
        "mgit.core.get_repo_paths",
    ) as mock_paths, patch("mgit.core.run_command") as mock_run:
        mock_load.return_value = {"profiles": {"all": ["repo1"]}}
        mock_paths.return_value = [Path("/tmp/repo1")]
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="main\n"),  # branch
            MagicMock(returncode=1),  # upstream check
            MagicMock(returncode=0),  # push --set-upstream
        ]
        push_repos(root, profile=None)
        # Check calls
        assert mock_run.call_count == 3


def test_status():
    """Test status function."""
    root = Path("/tmp")
    with patch("mgit.core.load_config") as mock_load, patch(
        "mgit.core.get_repo_paths",
    ) as mock_paths, patch("mgit.core.run_command") as mock_run, patch(
        "rich.print",
    ) as mock_print:
        mock_load.return_value = {"profiles": {"all": ["repo1"]}}
        mock_paths.return_value = [Path("/tmp/repo1")]
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="main\n"),
            MagicMock(returncode=0, stdout=""),
            MagicMock(returncode=0, stdout="## main...origin/main [ahead 1]\n"),
        ]
        status(root, profile=None)
        mock_print.assert_called_once()


def test_foreach():
    """Test foreach function."""
    root = Path("/tmp")
    cmd = "echo hello"
    with patch("mgit.core.load_config") as mock_load, patch(
        "mgit.core.get_repo_paths",
    ) as mock_paths, patch("mgit.core.run_command") as mock_run:
        mock_load.return_value = {"profiles": {"all": ["repo1"]}}
        mock_paths.return_value = [Path("/tmp/repo1")]
        mock_run.return_value = MagicMock(returncode=0)
        foreach(root, cmd, profile=None)
        mock_run.assert_called_once_with(["echo", "hello"], cwd=Path("/tmp/repo1"))


def test_sync_repos():
    """Test sync_repos function."""
    root = Path("/tmp")
    with patch("mgit.core.load_config") as mock_load, patch(
        "mgit.core.get_repo_paths",
    ) as mock_paths, patch("mgit.core.run_command") as mock_run:
        mock_load.return_value = {"profiles": {"all": ["repo1"]}}
        mock_paths.return_value = [Path("/tmp/repo1")]
        mock_run.return_value = MagicMock(returncode=0)
        sync_repos(root, profile=None)
        mock_run.assert_called_once_with(
            ["uv", "sync", "--dev"], cwd=Path("/tmp/repo1"),
        )


def test_run_tests():
    """Test run_tests function."""
    root = Path("/tmp")
    with patch("mgit.core.load_config") as mock_load, patch(
        "mgit.core.get_repo_paths",
    ) as mock_paths, patch("mgit.core.run_command") as mock_run:
        mock_load.return_value = {"profiles": {"all": ["repo1"]}}
        mock_paths.return_value = [Path("/tmp/repo1")]
        mock_run.return_value = MagicMock(returncode=0)
        run_tests(root, glob=None, parallel=True, profile=None)
        mock_run.assert_called_once_with(
            ["pytest", "-n", "auto"], cwd=Path("/tmp/repo1"),
        )


def test_commit_repos_all():
    """Test commit_repos with all=True."""
    root = Path("/tmp")
    with patch("mgit.core.load_config") as mock_load, patch(
        "mgit.core.get_repo_paths",
    ) as mock_paths, patch("mgit.core.run_command") as mock_run:
        mock_load.return_value = {"profiles": {"all": ["repo1"]}}
        mock_paths.return_value = [Path("/tmp/repo1")]
        mock_run.side_effect = [
            MagicMock(returncode=0),  # add
            MagicMock(returncode=0),  # diff --cached --quiet (has changes)
            MagicMock(returncode=0),  # commit
            MagicMock(returncode=0, stdout="diff"),  # show
        ]
        commit_repos(root, all=True, message="test", profile=None)
        assert mock_run.call_count == 4


def test_commit_repos_partial():
    """Test commit_repos with all=False."""
    root = Path("/tmp")
    with patch("mgit.core.load_config") as mock_load, patch(
        "mgit.core.get_repo_paths",
    ) as mock_paths, patch("mgit.core.run_command") as mock_run, patch(
        "pathlib.Path.exists",
    ) as mock_exists:
        mock_load.return_value = {"profiles": {"all": ["repo1"]}}
        mock_paths.return_value = [Path("/tmp/repo1")]
        mock_exists.return_value = True  # src/ exists
        mock_run.side_effect = [
            MagicMock(returncode=0),  # add src/
            MagicMock(returncode=0),  # diff --cached --quiet
            MagicMock(returncode=0),  # commit
            MagicMock(returncode=0, stdout="diff"),  # show
        ]
        commit_repos(root, all=False, message="test", profile=None)
        # Should add src/, tests/, examples/
        assert mock_run.call_count == 4


def test_tag_repos():
    """Test tag_repos function."""
    root = Path("/tmp")
    tag = "v1.0"
    with patch("mgit.core.load_config") as mock_load, patch(
        "mgit.core.get_repo_paths",
    ) as mock_paths, patch("mgit.core.run_command") as mock_run:
        mock_load.return_value = {"profiles": {"all": ["repo1"]}}
        mock_run.return_value = MagicMock(returncode=0)
        tag_repos(root, tag, push=False, profile=None)
        mock_run.assert_called_once_with(["git", "tag", tag], cwd=Path("/tmp/repo1"))


def test_tag_repos_push():
    """Test tag_repos with push."""
    root = Path("/tmp")
    tag = "v1.0"
    with patch("mgit.core.load_config") as mock_load, patch(
        "mgit.core.get_repo_paths",
    ) as mock_paths, patch("mgit.core.run_command") as mock_run:
        mock_load.return_value = {"profiles": {"all": ["repo1"]}}
        mock_paths.return_value = [Path("/tmp/repo1")]
        mock_run.return_value = MagicMock(returncode=0)
        tag_repos(root, tag, push=True, profile=None)
        assert mock_run.call_count == 2
        mock_run.assert_any_call(["git", "tag", tag], cwd=Path("/tmp/repo1"))
        mock_run.assert_any_call(["git", "push", "origin", tag], cwd=Path("/tmp/repo1"))
