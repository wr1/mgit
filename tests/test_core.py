"""Test for core functions."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from mgit.core import (
    branch,
    commit_repos,
    foreach,
    push_repos,
    run_tests,
    status,
    sync_repos,
    tag_repos,
)


def test_branch_create():
    """Test creating a new branch across repos."""
    root = Path("/tmp")
    name = "feature/new"
    with patch("mgit.core.load_config") as mock_load, patch(
        "mgit.core.get_repo_paths",
    ) as mock_paths, patch("subprocess.run") as mock_run:
        mock_load.return_value = {"profiles": {"all": ["repo1", "repo2"]}}
        mock_paths.return_value = [Path("/tmp/repo1"), Path("/tmp/repo2")]
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        branch(root, name, delete=False, sync=False, profile=None)
        # Should call checkout -b for each repo
        assert mock_run.call_count == 2
        mock_run.assert_any_call(
            ["git", "checkout", "-b", name], check=False, cwd=Path("/tmp/repo1"), capture_output=True, text=True,
        )
        mock_run.assert_any_call(
            ["git", "checkout", "-b", name], check=False, cwd=Path("/tmp/repo2"), capture_output=True, text=True,
        )


def test_branch_delete():
    """Test deleting a branch across repos."""
    root = Path("/tmp")
    name = "feature/old"
    with patch("mgit.core.load_config") as mock_load, patch(
        "mgit.core.get_repo_paths",
    ) as mock_paths, patch("subprocess.run") as mock_run:
        mock_load.return_value = {"profiles": {"all": ["repo1"]}}
        mock_paths.return_value = [Path("/tmp/repo1")]
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        branch(root, name, delete=True, sync=False, profile=None)
        mock_run.assert_called_once_with(
            ["git", "branch", "-D", name], check=False, cwd=Path("/tmp/repo1"), capture_output=True, text=True,
        )


def test_branch_sync():
    """Test syncing branch across repos."""
    root = Path("/tmp")
    name = "main"
    with patch("mgit.core.load_config") as mock_load, patch(
        "mgit.core.get_repo_paths",
    ) as mock_paths, patch("subprocess.run") as mock_run:
        mock_load.return_value = {"profiles": {"all": ["repo1", "repo2"]}}
        mock_paths.return_value = [Path("/tmp/repo1"), Path("/tmp/repo2")]
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="main\n", stderr=""),
            MagicMock(returncode=0, stdout="", stderr=""),
            MagicMock(returncode=0, stdout="", stderr=""),
        ]
        branch(root, name, delete=False, sync=True, profile=None)
        assert mock_run.call_count == 3
        mock_run.assert_any_call(
            ["git", "branch", "--show-current"], check=False, cwd=Path("/tmp/repo1"), capture_output=True, text=True,
        )
        mock_run.assert_any_call(["git", "checkout", "main"], check=False, cwd=Path("/tmp/repo1"), capture_output=True, text=True)
        mock_run.assert_any_call(["git", "checkout", "main"], check=False, cwd=Path("/tmp/repo2"), capture_output=True, text=True)


def test_push_repos():
    """Test pushing repos."""
    root = Path("/tmp")
    with patch("mgit.core.load_config") as mock_load, patch(
        "mgit.core.get_repo_paths",
    ) as mock_paths, patch("subprocess.run") as mock_run:
        mock_load.return_value = {"profiles": {"all": ["repo1"]}}
        mock_paths.return_value = [Path("/tmp/repo1")]
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="main\n", stderr=""),
            MagicMock(returncode=1, stdout="", stderr=""),
            MagicMock(returncode=0, stdout="", stderr=""),
        ]
        push_repos(root, profile=None)
        # Check calls
        assert mock_run.call_count == 3


def test_status():
    """Test status function."""
    root = Path("/tmp")
    with patch("mgit.core.load_config") as mock_load, patch(
        "mgit.core.get_repo_paths",
    ) as mock_paths, patch("subprocess.run") as mock_run, patch(
        "rich.print",
    ) as mock_print:
        mock_load.return_value = {"profiles": {"all": ["repo1"]}}
        mock_paths.return_value = [Path("/tmp/repo1")]
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="main\n", stderr=""),
            MagicMock(returncode=0, stdout="", stderr=""),
            MagicMock(returncode=0, stdout="## main...origin/main [ahead 1]\n", stderr=""),
        ]
        status(root, profile=None)
        mock_print.assert_called_once()


def test_foreach():
    """Test foreach function."""
    root = Path("/tmp")
    cmd = "echo hello"
    with patch("mgit.core.load_config") as mock_load, patch(
        "mgit.core.get_repo_paths",
    ) as mock_paths, patch("subprocess.run") as mock_run:
        mock_load.return_value = {"profiles": {"all": ["repo1"]}}
        mock_paths.return_value = [Path("/tmp/repo1")]
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        foreach(root, cmd, profile=None)
        mock_run.assert_called_once_with(["echo", "hello"], check=False, cwd=Path("/tmp/repo1"), capture_output=True, text=True)


def test_sync_repos():
    """Test sync_repos function."""
    root = Path("/tmp")
    with patch("mgit.core.load_config") as mock_load, patch(
        "mgit.core.get_repo_paths",
    ) as mock_paths, patch("subprocess.run") as mock_run:
        mock_load.return_value = {"profiles": {"all": ["repo1"]}}
        mock_paths.return_value = [Path("/tmp/repo1")]
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        sync_repos(root, profile=None)
        mock_run.assert_called_once_with(
            ["uv", "sync", "--dev"], check=False, cwd=Path("/tmp/repo1"), capture_output=True, text=True,
        )


def test_run_tests():
    """Test run_tests function."""
    root = Path("/tmp")
    with patch("mgit.core.load_config") as mock_load, patch(
        "mgit.core.get_repo_paths",
    ) as mock_paths, patch("subprocess.run") as mock_run:
        mock_load.return_value = {"profiles": {"all": ["repo1"]}}
        mock_paths.return_value = [Path("/tmp/repo1")]
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        run_tests(root, glob=None, parallel=True, profile=None)
        mock_run.assert_called_once_with(
            ["pytest", "-n", "auto"], check=False, cwd=Path("/tmp/repo1"), capture_output=True, text=True,
        )


def test_commit_repos_all():
    """Test commit_repos with all=True."""
    root = Path("/tmp")
    with patch("mgit.core.load_config") as mock_load, patch(
        "mgit.core.get_repo_paths",
    ) as mock_paths, patch("subprocess.run") as mock_run:
        mock_load.return_value = {"profiles": {"all": ["repo1"]}}
        mock_paths.return_value = [Path("/tmp/repo1")]
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""),
            MagicMock(returncode=1, stdout="", stderr=""),
            MagicMock(returncode=0, stdout="", stderr=""),
            MagicMock(returncode=0, stdout="diff", stderr=""),
        ]
        commit_repos(root, all=True, message="test", profile=None)
        assert mock_run.call_count == 4


def test_commit_repos_partial():
    """Test commit_repos with all=False."""
    root = Path("/tmp")
    with patch("mgit.core.load_config") as mock_load, patch(
        "mgit.core.get_repo_paths",
    ) as mock_paths, patch("subprocess.run") as mock_run, patch(
        "pathlib.Path.exists",
    ) as mock_exists:
        mock_load.return_value = {"profiles": {"all": ["repo1"]}}
        mock_paths.return_value = [Path("/tmp/repo1")]
        mock_exists.return_value = True
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""),
            MagicMock(returncode=1, stdout="", stderr=""),
            MagicMock(returncode=0, stdout="", stderr=""),
            MagicMock(returncode=0, stdout="diff", stderr=""),
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
    ) as mock_paths, patch("subprocess.run") as mock_run:
        mock_load.return_value = {"profiles": {"all": ["repo1"]}}
        mock_paths.return_value = [Path("/tmp/repo1")]
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        tag_repos(root, tag, push=False, profile=None)
        mock_run.assert_called_once_with(["git", "tag", tag], check=False, cwd=Path("/tmp/repo1"), capture_output=True, text=True)


def test_tag_repos_push():
    """Test tag_repos with push."""
    root = Path("/tmp")
    tag = "v1.0"
    with patch("mgit.core.load_config") as mock_load, patch(
        "mgit.core.get_repo_paths",
    ) as mock_paths, patch("subprocess.run") as mock_run:
        mock_load.return_value = {"profiles": {"all": ["repo1"]}}
        mock_paths.return_value = [Path("/tmp/repo1")]
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        tag_repos(root, tag, push=True, profile=None)
        assert mock_run.call_count == 2
        mock_run.assert_any_call(["git", "tag", tag], check=False, cwd=Path("/tmp/repo1"), capture_output=True, text=True)
        mock_run.assert_any_call(["git", "push", "origin", tag], check=False, cwd=Path("/tmp/repo1"), capture_output=True, text=True)
