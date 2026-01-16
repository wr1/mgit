"""Tests for ruff operations."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mgit.core.ruff import ruff_check_fix, ruff_format
from mgit.utils.run_command import run_command


@pytest.fixture
def mock_config():
    """Mock config for testing."""
    return {
        "profiles": {
            "all": ["repo1", "repo2"],
        },
    }


@pytest.fixture
def mock_repo_paths():
    """Mock repo paths."""
    return [Path("repo1"), Path("repo2")]


@patch("mgit.core.ruff.load_config")
@patch("mgit.core.ruff.get_repo_paths")
@patch("mgit.core.ruff.run_command")
@patch("builtins.print")
@patch("mgit.core.ruff.logger")
def test_ruff_format(mock_logger, mock_print, mock_run_command, mock_get_repo_paths, mock_load_config, mock_config, mock_repo_paths):
    """Test ruff_format function."""
    mock_load_config.return_value = MagicMock(profiles={"all": ["repo1", "repo2"]})
    mock_get_repo_paths.return_value = mock_repo_paths
    mock_run_command.return_value = MagicMock(returncode=0, stdout="", stderr="")

    ruff_format(Path("root"))

    assert mock_load_config.call_count == 1
    assert mock_get_repo_paths.call_count == 1
    assert mock_run_command.call_count == 2  # Once per repo
    mock_run_command.assert_any_call(["ruff", "format"], cwd=Path("repo1"))
    mock_run_command.assert_any_call(["ruff", "format"], cwd=Path("repo2"))
    assert mock_print.call_count == 4  # Prints header and output for each repo


@patch("mgit.core.ruff.load_config")
@patch("mgit.core.ruff.get_repo_paths")
@patch("mgit.core.ruff.run_command")
@patch("builtins.print")
@patch("mgit.core.ruff.logger")
def test_ruff_check_fix(mock_logger, mock_print, mock_run_command, mock_get_repo_paths, mock_load_config, mock_config, mock_repo_paths):
    """Test ruff_check_fix function."""
    mock_load_config.return_value = MagicMock(profiles={"all": ["repo1", "repo2"]})
    mock_get_repo_paths.return_value = mock_repo_paths
    mock_run_command.return_value = MagicMock(returncode=0, stdout="", stderr="")

    ruff_check_fix(Path("root"))

    assert mock_load_config.call_count == 1
    assert mock_get_repo_paths.call_count == 1
    assert mock_run_command.call_count == 2  # Once per repo
    mock_run_command.assert_any_call(["ruff", "check", "--fix", "--unsafe-fixes"], cwd=Path("repo1"))
    mock_run_command.assert_any_call(["ruff", "check", "--fix", "--unsafe-fixes"], cwd=Path("repo2"))
    assert mock_print.call_count == 4  # Prints header and output for each repo


@patch("mgit.core.ruff.load_config")
@patch("mgit.core.ruff.get_repo_paths")
@patch("mgit.core.ruff.run_command")
@patch("builtins.print")
@patch("mgit.core.ruff.logger")
def test_ruff_format_with_error(mock_logger, mock_print, mock_run_command, mock_get_repo_paths, mock_load_config, mock_config, mock_repo_paths):
    """Test ruff_format with command error."""
    mock_load_config.return_value = MagicMock(profiles={"all": ["repo1", "repo2"]})
    mock_get_repo_paths.return_value = mock_repo_paths
    mock_run_command.return_value = MagicMock(returncode=1, stdout="", stderr="Error message")

    ruff_format(Path("root"))

    assert mock_run_command.call_count == 2
    assert mock_logger.error.call_count == 2
    mock_logger.error.assert_any_call("Failed to format in repo1: Error message")
    mock_logger.error.assert_any_call("Failed to format in repo2: Error message")
    assert mock_print.call_count == 4


@patch("mgit.core.ruff.load_config")
@patch("mgit.core.ruff.get_repo_paths")
@patch("mgit.core.ruff.run_command")
@patch("builtins.print")
@patch("mgit.core.ruff.logger")
def test_ruff_check_fix_with_error(mock_logger, mock_print, mock_run_command, mock_get_repo_paths, mock_load_config, mock_config, mock_repo_paths):
    """Test ruff_check_fix with command error."""
    mock_load_config.return_value = MagicMock(profiles={"all": ["repo1", "repo2"]})
    mock_get_repo_paths.return_value = mock_repo_paths
    mock_run_command.return_value = MagicMock(returncode=1, stdout="", stderr="Error message")

    ruff_check_fix(Path("root"))

    assert mock_run_command.call_count == 2
    assert mock_logger.error.call_count == 2
    mock_logger.error.assert_any_call("Failed to check/fix in repo1: Error message")
    mock_logger.error.assert_any_call("Failed to check/fix in repo2: Error message")
    assert mock_print.call_count == 4
