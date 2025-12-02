"""Test for core functions."""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from multig.core import prep, branch, push_repos


def test_prep():
    """Test that prep calls fold_files without NameError."""
    root = Path("/tmp")
    target = "test"
    with patch("multig.core.load_config") as mock_load, \
         patch("multig.core.get_repos_from_config") as mock_get, \
         patch("multig.core.get_repo_paths") as mock_paths, \
         patch("multig.core.fold_files") as mock_fold:
        mock_load.return_value = {"profiles": {"all": ["repo1"]}}
        mock_get.return_value = ["repo1"]
        mock_paths.return_value = [Path("/tmp/repo1")]
        # Should not raise NameError
        prep(root, target)
        mock_fold.assert_called_once()


def test_branch_create():
    """Test creating a new branch across repos."""
    root = Path("/tmp")
    name = "feature/new"
    with patch("multig.core.load_config") as mock_load, \
         patch("multig.core.get_repo_paths") as mock_paths, \
         patch("multig.core.run_command") as mock_run:
        mock_load.return_value = {"profiles": {"all": ["repo1", "repo2"]}}
        mock_paths.return_value = [Path("/tmp/repo1"), Path("/tmp/repo2")]
        mock_run.return_value = MagicMock(returncode=0)
        branch(root, name, delete=False, sync=False, profile=None)
        # Should call checkout -b for each repo
        assert mock_run.call_count == 2
        mock_run.assert_any_call(["git", "checkout", "-b", name], cwd=Path("/tmp/repo1"))
        mock_run.assert_any_call(["git", "checkout", "-b", name], cwd=Path("/tmp/repo2"))


def test_push_repos():
    """Test pushing repos."""
    root = Path("/tmp")
    with patch("multig.core.load_config") as mock_load, \
         patch("multig.core.get_repo_paths") as mock_paths, \
         patch("multig.core.run_command") as mock_run:
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