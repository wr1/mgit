"""Test for utils functions."""

import ast
from pathlib import Path
from unittest.mock import MagicMock, patch

from mgit.utils.extract_imports import extract_imports
from mgit.utils.find_dependencies import find_dependencies
from mgit.utils.find_matching_repos import find_matching_repos
from mgit.utils.fold_files import fold_files
from mgit.utils.get_git_repos import get_git_repos
from mgit.utils.get_repos_from_config import get_repos_from_config
from mgit.utils.resolve_targets import resolve_targets
from mgit.utils.run_command import run_command


def test_run_command():
    """Test run_command."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="output", stderr="")
        result = run_command(["echo", "hello"])
        mock_run.assert_called_once_with(
            ["echo", "hello"],
            check=False,
            cwd=None,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0


def test_get_repos_from_config():
    """Test get_repos_from_config."""
    from mgit.config import Config

    config = Config(
        project_name="test", profiles={"test": ["repo1"]}, aliases={"alias1": ["repo2"]}
    )
    assert get_repos_from_config(config, "test") == ["repo1"]
    assert get_repos_from_config(config, "alias1") == ["repo2"]
    assert get_repos_from_config(config, "repo3") == ["repo3"]


def test_find_matching_repos():
    """Test find_matching_repos."""
    repos = ["b3m", "b3_geo", "cgfoil"]
    assert find_matching_repos(repos, "b3*") == ["b3m", "b3_geo"]


def test_fold_files():
    """Test fold_files."""
    files = [Path("/tmp/file1.py")]
    output = Path("/tmp/output.json")
    with patch("mgit.utils.fold_files.pyperclip.copy") as mock_copy, patch(
        "pathlib.Path.read_text",
        return_value="content",
    ) as mock_read:
        fold_files(files, output)
        mock_copy.assert_called_once_with("content")


def test_get_git_repos():
    """Test get_git_repos."""
    root = Path("/tmp")
    mock_repo = MagicMock()
    mock_repo.is_dir.return_value = True
    mock_git = MagicMock()
    mock_git.exists.return_value = True
    mock_repo.__truediv__ = MagicMock(return_value=mock_git)
    with patch("pathlib.Path.iterdir", return_value=[mock_repo]) as mock_iterdir:
        repos = get_git_repos(root)
        assert len(repos) == 1


def test_extract_imports():
    """Test extract_imports."""
    file = Path("/tmp/test.py")
    with patch("builtins.open", create=True) as mock_open, patch(
        "ast.parse",
    ) as mock_parse, patch("ast.walk") as mock_walk:
        mock_open.return_value.__enter__.return_value.read.return_value = "import os"
        mock_tree = MagicMock()
        mock_parse.return_value = mock_tree
        mock_node = MagicMock()
        mock_node.__class__ = ast.Import
        mock_alias = MagicMock()
        mock_alias.name = "os"
        mock_node.names = [mock_alias]
        mock_walk.return_value = [mock_node]
        imports = extract_imports(file)
        assert "os" in imports


def test_resolve_targets():
    """Test resolve_targets."""
    from mgit.config import Config

    config = Config(project_name="test", profiles={"all": ["repo1"]}, aliases={})
    targets = ["repo1"]
    root = Path("/tmp")
    repos, explicit_files = resolve_targets(config, targets, root)
    assert repos == {"repo1"}
    assert explicit_files == set()


def test_find_dependencies():
    """Test find_dependencies."""
    files = [Path("/tmp/file1.py")]
    import_map = {"os": "stdlib"}
    root = Path("/tmp")
    with patch("mgit.utils.find_dependencies.extract_imports") as mock_extract:
        mock_extract.return_value = {"os"}
        deps = find_dependencies(files, import_map, root)
        assert deps == {"stdlib"}
