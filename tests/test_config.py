"""Test for config functions."""

from pathlib import Path
from unittest.mock import patch

import pytest

from mgit.config import edit_config, init_config, load_config


def test_load_config():
    """Test load_config."""
    root = Path("/tmp")
    config_path = root / ".mgitrc"
    with patch("pathlib.Path.exists") as mock_exists, patch(
        "builtins.open",
        create=True,
    ) as mock_open, patch("yaml.safe_load") as mock_load:
        mock_exists.return_value = True
        mock_load.return_value = {
            "project_name": "test",
            "profiles": {"all": ["repo1"]},
            "aliases": {},
        }
        config = load_config(root)
        assert config.project_name == "test"


def test_load_config_missing():
    """Test load_config with missing file."""
    root = Path("/tmp")
    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.return_value = False
        with pytest.raises(FileNotFoundError):
            load_config(root)


def test_init_config():
    """Test init_config."""
    root = Path("/tmp")
    with patch("pathlib.Path.exists") as mock_exists, patch(
        "mgit.config.questionary.confirm"
    ) as mock_confirm, patch(
        "mgit.config.questionary.text",
    ) as mock_text, patch("pathlib.Path.iterdir") as mock_iterdir, patch(
        "builtins.open",
        create=True,
    ) as mock_open, patch("yaml.safe_dump") as mock_dump:
        mock_exists.return_value = True
        mock_confirm.return_value.ask.return_value = False
        init_config(root)
        # If exists, and not overwrite, do nothing
        # Test the wizard part if not exists


def test_edit_config():
    """Test edit_config."""
    root = Path("/tmp")
    with patch("os.environ.get") as mock_env, patch("os.system") as mock_system:
        mock_env.return_value = "vim"
        edit_config(root)
        mock_system.assert_called_once_with("vim /tmp/.mgitrc")
