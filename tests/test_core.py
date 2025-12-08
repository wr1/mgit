"""Test for core functions."""
from pathlib import Path
from unittest.mock import MagicMock, patch

from mgit.core.branch import branch
from mgit.core.commit import commit_repos
from mgit.core.foreach import foreach
from mgit.core.push import push_repos
from mgit.core.status import status
from mgit.core.sync import sync_repos
from mgit.core.tag import tag_repos
from mgit.core.test import run_tests


def test_branch_create():
    """Test creating a new branch across repos."""
    root = Path("/tmp")
    name = "feature/new"
    with patch("mgit.core.branch.load_config") as mock_load, patch(
        "mgit.core.branch.get_repo_paths",
    ) as mock_paths, patch("mgit.core.branch.run_command") as mock_run:
        mock_load.return_value = {"profiles": {"all": ["repo1", "repo2"]}}
        mock_paths.return_value = [Path("/tmp/repo1"), Path("/tmp/repo2")]
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
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
    with patch("mgit.core.branch.load_config") as mock_load, patch(
        "mgit.core.branch.get_repo_paths",
    ) as mock_paths, patch("mgit.core.branch.run_command") as mock_run:
        mock_load.return_value = {"profiles": {"all": ["repo1"]}}
        mock_paths.return_value = [Path("/tmp/repo1")]
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        branch(root, name, delete=True, sync=False, profile=None)
        mock_run.assert_called_once_with(
            ["git", "branch", "-D", name], cwd=Path("/tmp/repo1"),
        )


def test_branch_sync():
    """Test syncing branch across repos."""
    root = Path("/tmp")
    name = "main"
    with patch("mgit.core.branch.load_config") as mock_load, patch(
        "mgit.core.branch.get_repo_paths",
    ) as mock_paths, patch("mgit.core.branch.run_command") as mock_run:
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
            ["git", "branch", "--show-current"], cwd=Path("/tmp/repo1"),
        )
        mock_run.assert_any_call(["git", "checkout", "main"], cwd=Path("/tmp/repo1"))
        mock_run.assert_any_call(["git", "checkout", "main"], cwd=Path("/tmp/repo2"))


def test_push_repos():
    """Test pushing repos."""
    root = Path("/tmp")
    with patch("mgit.core.push.load_config") as mock_load, patch(
        "mgit.core.push.get_repo_paths",
    ) as mock_paths, patch("mgit.core.push.run_command") as mock_run:
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
    with patch("mgit.core.status.load_config") as mock_load, patch(
        "mgit.core.status.get_repo_paths",
    ) as mock_paths, patch("mgit.core.status.run_command") as mock_run, patch(
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
    with patch("mgit.core.foreach.load_config") as mock_load, patch(
        "mgit.core.foreach.get_repo_paths",
    ) as mock_paths, patch("mgit.core.foreach.run_command") as mock_run:
        mock_load.return_value = {"profiles": {"all": ["repo1"]}}
        mock_paths.return_value = [Path("/tmp/repo1")]
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        foreach(root, cmd, profile=None)
        mock_run.assert_called_once_with(["echo", "hello"], cwd=Path("/tmp/repo1"))


def test_sync_repos():
    """Test sync_repos function."""
    root = Path("/tmp")
    with patch("mgit.core.sync.load_config") as mock_load, patch(
        "mgit.core.sync.get_repo_paths",
    ) as mock_paths, patch("mgit.core.sync.run_command") as mock_run:
        mock_load.return_value = {"profiles": {"all": ["repo1"]}}
        mock_paths.return_value = [Path("/tmp/repo1")]
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        sync_repos(root, profile=None)
        mock_run.assert_called_once_with(
            ["uv", "sync", "--dev"], cwd=Path("/tmp/repo1"),
        )


def test_run_tests():
    """Test run_tests function."""
    root = Path("/tmp")
    with patch("mgit.core.test.load_config") as mock_load, patch(
        "mgit.core.test.get_repo_paths",
    ) as mock_paths, patch("mgit.core.test.run_command") as mock_run:
        mock_load.return_value = {"profiles": {"all": ["repo1"]}}
        mock_paths.return_value = [Path("/tmp/repo1")]
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        run_tests(root, glob=None, parallel=True, profile=None)
        mock_run.assert_called_once_with(
            ["pytest", "-n", "auto"], cwd=Path("/tmp/repo1"),
        )


def test_commit_repos_all():
    """Test commit_repos with all=True."""
    root = Path("/tmp")
    with patch("mgit.core.commit.load_config") as mock_load, patch(
        "mgit.core.commit.get_repo_paths",
    ) as mock_paths, patch("mgit.core.commit.run_command") as mock_run:
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
    with patch("mgit.core.commit.load_config") as mock_load, patch(
        "mgit.core.commit.get_repo_paths",
    ) as mock_paths, patch("mgit.core.commit.run_command") as mock_run, patch(
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
    with patch("mgit.core.tag.load_config") as mock_load, patch(
        "mgit.core.tag.get_repo_paths",
    ) as mock_paths, patch("mgit.core.tag.run_command") as mock_run:
        mock_load.return_value = {"profiles": {"all": ["repo1"]}}
        mock_paths.return_value = [Path("/tmp/repo1")]
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        tag_repos(root, tag, push=False, profile=None)
        mock_run.assert_called_once_with(["git", "tag", tag], cwd=Path("/tmp/repo1"))


def test_tag_repos_push():
    """Test tag_repos with push."""
    root = Path("/tmp")
    tag = "v1.0"
    with patch("mgit.core.tag.load_config") as mock_load, patch(
        "mgit.core.tag.get_repo_paths",
    ) as mock_paths, patch("mgit.core.tag.run_command") as mock_run:
        mock_load.return_value = {"profiles": {"all": ["repo1"]}}
        mock_paths.return_value = [Path("/tmp/repo1")]
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        tag_repos(root, tag, push=True, profile=None)
        assert mock_run.call_count == 2
        mock_run.assert_any_call(["git", "tag", tag], cwd=Path("/tmp/repo1"))
        mock_run.assert_any_call(["git", "push", "origin", tag], cwd=Path("/tmp/repo1"))
